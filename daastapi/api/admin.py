from django.contrib import admin
from .models import Document, DocumentRevision, EntityType, EntityDocument

admin.site.register(Document)
admin.site.register(DocumentRevision)
admin.site.register(EntityType)
admin.site.register(EntityDocument)
