from django.db import models

class Document(models.Model):
    """
    A document indexed by this API.
    """
    label = models.CharField(max_length=255, null=False, db_index=True)
    originalURI = models.CharField(max_length=1024, null=False)
    revisionNo = models.IntegerField(null=True)

class DocumentRevision(models.Model):
    """
    A specific revision of a Document.
    """
    class Status(models.IntegerChoices):
        """
        The publication status of the document revision.
        """
        DRAFT = 0
        CONTRIBUTION = 15
        REJECTED = 99
        PUBLISHED = 200

    document = models.ForeignKey(Document, null=False, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, db_index=True)
    revisionNo = models.IntegerField(null=True)
    timestamp = models.DateField(db_index=True)
    content = models.JSONField(null=False)
    digest = models.CharField(max_length=128)

class DocumentLinkMode(models.Model):
    """
    A custom enumeration that describes how documents can be linked to
    Voyages/people in the Atlantic Slave Trade.
    """
    label = models.CharField(max_length=64, null=False)

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
