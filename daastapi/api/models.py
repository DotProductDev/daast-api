from django.db import models

class Document(models.Model):
    """
    A document indexed by this API.
    """
    label = models.CharField(max_length=255, null=False, db_index=True)
    revisionNo = models.IntegerField(null=True)
    # The etag is used to ensure that browsers can properly cache our generated
    # manifests.
    etag = models.CharField(max_length=32)

class DocumentRevision(models.Model):
    """
    A specific revision of a Document.
    """
    class Status(models.IntegerChoices):
        """
        The publication status of the document revision.
        """
        DRAFT = 0 # Still being worked on.
        CONTRIBUTION = 15 # Waiting for editorial decision.
        REJECTED = 99 # This revision should not be published.
        APPROVED = 100 # This revision should be published.
        PUBLISHED = 200 # A manifest was generated for this revision.

    document = models.ForeignKey(Document, null=False, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, db_index=True)
    revisionNo = models.IntegerField(null=True)
    timestamp = models.DateField(db_index=True)
    # Document/pages metadata used to build an IIIF manifest.
    content = models.JSONField(null=False)

class DocumentLinkMode(models.Model):
    """
    A custom enumeration that describes how documents can be linked to
    Voyages/people in the Atlantic Slave Trade.
    """
    label = models.CharField(max_length=64, null=False)

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

class EntityDocument(models.Model):
    """
    Represents a connection between an Entity (abstract) and a Document.
    """
    link_mode = models.ForeignKey(DocumentLinkMode, null=False, on_delete=models.RESTRICT)
    document = models.ForeignKey(Document, null=False, on_delete=models.RESTRICT)
    notes = models.CharField(max_length=255, null=True)

    class Meta:
        abstract = True

class EnslavedDocument(EntityDocument):
    """
    Connects enslaved and documents.
    """
    enslaved_id = models.IntegerField(null=False, db_index=True)

class EnslaverDocument(EntityDocument):
    """
    Connects enslavers and documents.
    """
    enslaver_id = models.IntegerField(null=False, db_index=True)

class VoyageDocument(EntityDocument):
    """
    Connects voyages and documents.
    """
    voyage_id = models.IntegerField(null=False, db_index=True)
