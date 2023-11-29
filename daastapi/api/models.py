"""
Document API models
"""

import json
from django.db import models

class Document(models.Model):
    """
    A document indexed by this API.
    """
    key = models.CharField(max_length=128, unique=True)
    current_rev = models.IntegerField(null=True)
    thumbnail = models.TextField(null=True, help_text='URL for a thumbnail of the Document')
    bib = models.TextField(null=True, help_text='Formatted bibliography for the Document')

    def __str__(self):
        return f"Document {self.key}"

class DocumentRevision(models.Model):
    """
    A specific revision of a Document.
    """
    class Status(models.IntegerChoices):
        """
        The publication status of the document revision.
        """
        DRAFT = 0 # Still being worked on.
        IMPORTED = 10 # The document revision was automatically imported by a management command
        CONTRIBUTION = 15 # Waiting for editorial decision.
        REJECTED = 99 # This revision should not be published.
        APPROVED = 100 # This revision should be published.
        PUBLISHED = 200 # A manifest was generated for this revision.
        NO_IMAGES = 500 # An IIIF manifest cannot be generated as there are no images for it

    document = models.ForeignKey(Document,
        null=False, on_delete=models.CASCADE, related_name='revisions')
    label = models.CharField(max_length=255, null=False, db_index=True)
    status = models.IntegerField(choices=Status.choices, db_index=True)
    revision_number = models.IntegerField(null=True)
    timestamp = models.DateField(db_index=True)
    # Document/pages metadata used to build an IIIF manifest.
    content = models.JSONField(null=False)

    class Meta:
        """Multi column uniqueness constraints"""
        constraints = [
            models.UniqueConstraint(fields=['document', 'revision_number'],
                                    name='unique_doc_rev_number')
        ]

    def __str__(self):
        return f"Document Revision {self.revision_number} ({self.label})"

class Transcription(models.Model):
    """
    The text transcription of a page in a document.
    """
    document_rev = models.ForeignKey(
        DocumentRevision, null=False,
        on_delete=models.CASCADE, related_name='transcriptions')
    page_number = models.IntegerField(null=False)
    # A BCP47 language code for the transcription text.
    # https://www.rfc-editor.org/bcp/bcp47.txt
    language_code = models.CharField(max_length=20, null=False)
    text = models.TextField(null=False)
    # Indicates whether the transcription is in the original language or a
    # translation.
    is_translation = models.BooleanField(null=False)

    def __str__(self):
        return f"Transcription p. {self.page_number}: {self.text}"

class EntityType(models.Model):
    """
    The type of entity that can be linked to a Document.
    """
    name = models.CharField(max_length=128, unique=True)
    url_label = models.CharField(max_length=256,
        help_text='The format of the url link label for entities of this " + \
            "type with a placeholder for the key')
    url_format = models.CharField(max_length=256,
        help_text='The format of the url with a placeholder for the entity key')
    def __str__(self):
        return f"Entity type: {self.name}"

class EntityDocument(models.Model):
    """
    Represents a connection between an Entity and a Document.
    """
    document = models.ForeignKey(Document, null=False,
        on_delete=models.RESTRICT, related_name='entities')
    notes = models.CharField(max_length=255, null=True)
    entity_type = models.ForeignKey(EntityType, null=False, on_delete=models.RESTRICT)
    entity_key = models.CharField(max_length=255, null=False, db_index=True)

    class Meta:
        """Multi column uniqueness constraints"""
        constraints = [
            models.UniqueConstraint(fields=['document', 'entity_type', 'entity_key'],
                                    name='unique_doc_entity_link')
        ]

class SearchOnEntity:
    """
    Search component that matches documents according to entities linked to it.
    """

    def __init__(self, typename: str, keys: list[str]):
        self.typename = typename
        self.keys = keys

class SearchModel:
    """
    Represents a search of documents in the database
    """

    def __init__(self,
                label: str | None = None,
                entities: list[SearchOnEntity] | None = None,
                results_page: int | None = None,
                page_size: int | None = None):
        self.label = label
        self.entities = entities or []
        self.results_page = results_page or 1
        self.page_size = page_size or 25

    @staticmethod
    def from_json(json_value: str):
        """
        Parse a JSON string to a SearchModel
        """
        data = json.loads(json_value)
        return SearchModel(
            data.get('label'),
            [SearchOnEntity(e['typename'], e['keys']) for e in data.get('entities', [])],
            data.get('results_page'),
            data.get('page_size'))

class EntityCache:
    """
    A simple cache that organizes the entities associated with each document.
    """

    def __init__(self):
        self._data = None

    def get(self, doc_key: str):
        """
        Get cached data for the document with the given key.
        """
        if not self._data:
            self.load()
        return self._data.get(doc_key, {})

    def load(self):
        """
        Load the cache
        """
        items = EntityDocument.objects.select_related('document', 'entity_type').all()
        data = {}
        for item in items:
            doc_data: dict[str,list[str]] = data.setdefault(item.document.key, {})
            by_type_data: list[str] = doc_data.setdefault(item.entity_type.name, [])
            by_type_data.append(item.entity_key)
        self._data = data
