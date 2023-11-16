from django.db import models

class Document(models.Model):
    """
    A document indexed by this API.
    """
    key = models.CharField(max_length=128, unique=True)
    current_rev = models.IntegerField(null=True)
    def __str__(self):
        return self.key

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

    document = models.ForeignKey(Document,
        null=False, on_delete=models.CASCADE, related_name='revisions')
    label = models.CharField(max_length=255, null=False, db_index=True)
    status = models.IntegerField(choices=Status.choices, db_index=True)
    revision_number = models.IntegerField(null=True)
    timestamp = models.DateField(db_index=True)
    # Document/pages metadata used to build an IIIF manifest.
    content = models.JSONField(null=False)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['document', 'revision_number'], name='unique_doc_rev_number')
        ]
    
    def __str__(self):
        return self.label

class Transcription(models.Model):
    """
    The text transcription of a page in a document.
    """
    document_rev = models.ForeignKey(DocumentRevision, null=False, on_delete=models.CASCADE)
    page_number = models.IntegerField(null=False)
    # A BCP47 language code for the transcription text.
    # https://www.rfc-editor.org/bcp/bcp47.txt
    language_code = models.CharField(max_length=20, null=False)
    text = models.TextField(null=False)
    # Indicates whether the transcription is in the original language or a
    # translation.
    is_translation = models.BooleanField(null=False)
    
    def __str__(self):
    	return self.text

class EntityType(models.Model):
    """
    The type of entity that can be linked to a Document.
    """
    name = models.CharField(max_length=128, unique=True)
    url_format = models.CharField(max_length=256,
        help_text='The format of the url with a placeholder for the entity key')
    def __str__(self):
        return self.name
    
class EntityDocument(models.Model):
    """
    Represents a connection between an Entity and a Document.
    """
    document = models.ForeignKey(Document, null=False, on_delete=models.RESTRICT)
    notes = models.CharField(max_length=255, null=True)
    entity_type = models.ForeignKey(EntityType, null=False, on_delete=models.RESTRICT)
    entity_key = models.CharField(max_length=255, null=False, db_index=True)
