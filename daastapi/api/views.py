from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import F, Q, Subquery
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from functools import reduce
from api.models import Document, DocumentRevision, EntityCache, EntityDocument, SearchModel

def manifest(request, key: str, rev_number_query: int | None = None):
    """
    Endpoint for IIIF manifests generated for Documents.
    """
    doc = get_object_or_404(Document, key=key)
    rev: DocumentRevision = None
    rev_number_query = rev_number_query or doc.current_rev
    if rev_number_query:
        matches = list(DocumentRevision.objects \
                       .filter(document=doc). \
                        filter(revision_number=rev_number_query))
        if matches:
            rev = matches[0]
    if not rev or rev.status != DocumentRevision.Status.PUBLISHED:
        raise Http404
    return redirect(f"{settings.MANIFEST_URL_BASE}/{key}_rev{str(doc.current_rev).zfill(3)}.json")

_entity_cache = EntityCache()

@csrf_exempt
@require_POST
def search(request):
    """
    Search endpoint for Documents.
    """
    sm = SearchModel.from_json(request.body.decode('utf-8'))
    # Start with the current published revisions.
    qs = DocumentRevision.objects \
        .filter(status=DocumentRevision.Status.PUBLISHED) \
        .filter(revision_number=F('document__current_rev'))
    if sm.label:
        qs = qs.filter(label__icontains=sm.label)
    if sm.entities:
        entity_filter = [Q(entity_type__name=e.typename) & Q(entity_key__in=e.keys)
                         for e in sm.entities]
        entity_query = EntityDocument.objects \
            .filter(reduce(lambda x, y: x | y, entity_filter)) \
            .values_list('document_id')
        qs = qs.filter(document_id__in=Subquery(entity_query))
    qs = qs.order_by('document__key')
    qs = qs.values('label', 'revision_number',
            key=F('document__key'), thumb=F('document__thumbnail'))
    paginator = Paginator(qs, sm.page_size)
    results = list(paginator.get_page(sm.results_page))
    for item in results:
        item['entities'] = _entity_cache.get(item['key'])
    return JsonResponse({ 'matches': qs.count(), 'results': results })
