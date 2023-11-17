from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from api.models import Document, DocumentRevision

# Create your views here.

def manifest(request, key, rev_number_query=None):
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
    