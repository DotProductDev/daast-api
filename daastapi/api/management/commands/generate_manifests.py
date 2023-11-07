import pathlib
from django.core.management.base import BaseCommand

from api.models import DocumentRevision

class Command(BaseCommand):
    help = """This command generate manifest files based on the documents
        marked for publication in the database"""
    
    def add_arguments(self, parser):
        parser.add_argument("status", nargs="*", type=int,
                            default=DocumentRevision.Status.APPROVED,
                            help="Only generate manifests with these status codes. Default = PUBLISHED")
        parser.add_argument("outDir", type=pathlib.Path,
                            help="The output directory where the manifests should be placed")
    
    def handle(self, *args, **options):
        # TODO: 
        # 1. Query the Documents that match the status filter.
        # 2. Enumerate files at the output directory, to determine which of the
        #    manifests, if any is no longer present in the filter.
        # 3. Compute hashes of the manifests and use them to generate an etag
        #    value that will be set on the Document etag field.
        pass