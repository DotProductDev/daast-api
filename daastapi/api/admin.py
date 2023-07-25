from django.contrib import admin
from .models import Document, DocumentLinkMode, DocumentRevision, VoyageDocument, EnslaverDocument, EnslavedDocument

admin.site.register(Document)
admin.site.register(DocumentLinkMode)
admin.site.register(DocumentRevision)
admin.site.register(VoyageDocument)
admin.site.register(EnslaverDocument)
admin.site.register(EnslavedDocument)
