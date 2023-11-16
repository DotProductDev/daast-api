from django.contrib import admin
from .models import Document, DocumentRevision, EntityType, EntityDocument,Transcription
import nested_admin

class EntityDocumentInline(nested_admin.NestedTabularInline):
	model=EntityDocument
	readonly_fields=(
		'notes',
		'entity_type',
		'entity_key'
	)
	can_delete=False
	extra=0
	classes=['collapse']


class TranscriptionInline(nested_admin.NestedTabularInline):
	model=Transcription
	readonly_fields=(
		'text',
		'page_number',
		'language_code',
		'is_translation'
		)
	classes=['collapse']
	can_delete=False
	extra=0

class DocumentRevisionInline(nested_admin.NestedStackedInline):
	model=DocumentRevision
	inlines=(
		TranscriptionInline,
	)
	readonly_fields=(
		'label',
		'status',
		'revision_number',
		'timestamp',
		'content'
	)
	classes=['collapse']
	can_delete=False
	extra=0


class DocumentAdmin(nested_admin.NestedModelAdmin):
	inlines=[
		DocumentRevisionInline,
		EntityDocumentInline
	]
	readonly_fields=['key','current_rev']
	search_fields=['key']
	list_fields=['label']


admin.site.register(Document,DocumentAdmin)
