from django.core.management.base import BaseCommand
# from api.models import Document, DocumentRevision
from xml.etree import ElementTree
import re
import requests

_dublin_core_labels = {
    "abstract": "Abstract",
    "accessRights": "Access Rights",
    "accrualMethod": "Accrual Method",
    "accrualPeriodicity": "Accrual Periodicity",
    "accrualPolicy": "Accrual Policy",
    "alternative": "Alternative Title",
    "audience": "Audience",
    "available": "Date Available",
    "bibliographicCitation": "Bibliographic Citation",
    "conformsTo": "Conforms To",
    "contributor": "Contributor",
    "coverage": "Coverage",
    "created": "Date Created",
    "creator": "Creator",
    "date": "Date",
    "dateAccepted": "Date Accepted",
    "dateCopyrighted": "Date Copyrighted",
    "dateSubmitted": "Date Submitted",
    "educationLevel": "Audience Education Level",
    "extent": "Extent",
    "format": "Format",
    "hasFormat": "Has Format",
    "hasPart": "Has Part",
    "hasVersion": "Has Version",
    "identifier": "Identifier",
    "instructionalMethod": "Instructional Method",
    "isFormatOf": "Is Format Of",
    "isPartOf": "Is Part Of",
    "isReferencedBy": "Is Referenced By",
    "isReplacedBy": "Is Replaced By",
    "isRequiredBy": "Is Required By",
    "issued": "Date Issued",
    "isVersionOf": "Is Version Of",
    "language": "Language",
    "license": "License",
    "mediator": "Mediator",
    "medium": "Medium",
    "modified": "Date Modified",
    "provenance": "Provenance",
    "publisher": "Publisher",
    "references": "References",
    "relation": "Relation",
    "replaces": "Replaces",
    "requires": "Requires",
    "rights": "Rights",
    "rightsHolder": "Rights Holder",
    "source": "Source",
    "spatial": "Spatial Coverage",
    "subject": "Subject",
    "tableOfContents": "Table Of Contents",
    "temporal": "Temporal Coverage",
    "valid": "Date Valid",
    "description": "Description",
    "title": "Title",
    "type": "Type",
    "DCMIType": "DCMI Type Vocabulary",
    "DDC": "DDC",
    "IMT": "IMT",
    "LCC": "LCC",
    "LCSH": "LCSH",
    "MESH": "MeSH",
    "NLM": "NLM",
    "TGN": "TGN",
    "UDC": "UDC",
    "Box": "DCMI Box",
    "ISO3166": "ISO 3166",
    "ISO639-2": "ISO 639-2",
    "ISO639-3": "ISO 639-3",
    "Period": "DCMI Period",
    "Point": "DCMI Point",
    "RFC1766": "RFC 1766",
    "RFC3066": "RFC 3066",
    "RFC4646": "RFC 4646",
    "RFC5646": "RFC 5646",
    "URI": "URI",
    "W3CDTF": "W3C-DTF",
    "Agent": "Agent",
    "AgentClass": "Agent Class",
    "BibliographicResource": "Bibliographic Resource",
    "FileFormat": "File Format",
    "Frequency": "Frequency",
    "Jurisdiction": "Jurisdiction",
    "LicenseDocument": "License Document",
    "LinguisticSystem": "Linguistic System",
    "Location": "Location",
    "LocationPeriodOrJurisdiction": "Location, Period, or Jurisdiction",
    "MediaType": "Media Type",
    "MediaTypeOrExtent": "Media Type or Extent",
    "MethodOfAccrual": "Method of Accrual",
    "MethodOfInstruction": "Method of Instruction",
    "PeriodOfTime": "Period of Time",
    "PhysicalMedium": "Physical Medium",
    "PhysicalResource": "Physical Resource",
    "Policy": "Policy",
    "ProvenanceStatement": "Provenance Statement",
    "RightsStatement": "Rights Statement",
    "SizeOrDuration": "Size or Duration",
    "Standard": "Standard",
    "Collection": "Collection",
    "Dataset": "Dataset",
    "Event": "Event",
    "Image": "Image",
    "InteractiveResource": "Interactive Resource",
    "MovingImage": "Moving Image",
    "PhysicalObject": "Physical Object",
    "Service": "Service",
    "Software": "Software",
    "Sound": "Sound",
    "StillImage": "Still Image",
    "Text": "Text",
    "domainIncludes": "Domain Includes",
    "memberOf": "Member Of",
    "rangeIncludes": "Range Includes",
    "VocabularyEncodingScheme": "Vocabulary Encoding Scheme"
}

_max_errors = 5 # Maximum number of *consecutive* errors for the APIs we call.

class Command(BaseCommand):
    help = """This command fetches data from multiple APIs and consolidates
    the information into a local Document entity"""
    
    def add_arguments(self, parser):
        parser.add_argument("--voyages-key")
        parser.add_argument("--voyages-url")
        parser.add_argument("--zotero-key")
        parser.add_argument("--zotero-url", default="https://api.zotero.org")
        parser.add_argument("--zotero-groupname", default="sv-docs")
        parser.add_argument("--zotero-userid")

    @staticmethod
    def get_zotero_data(options, group_id):
        def extract_from_rdf(rdf):
            # Map all the entries first and later keep only those that have a
            # Dublin Core label, and for those we use that label for the key
            # value instead of the original XML tag's name.
            complete = { re.match('^{.*}(.*)$', e.tag)[1]: e.text for e in rdf }
            return { _dublin_core_labels[key]: val for key, val in complete.items() if key in _dublin_core_labels }

        def zotero_page(start, limit=100):
            res = requests.get( \
                f"{options['zotero_url']}/groups/{group_id}/items?start={start}&limit={limit}&content=rdf_dc", \
                headers={ 'Authorization': f"Bearer {options['zotero_key']}" }, \
                timeout=60)
            page = ElementTree.fromstring(res.content)
            # Select the content nodes and navigate through RDF elements until
            # we reach http://www.w3.org/1999/02/22-rdf-syntax-ns#Description.
            # The following will build a dictionary, indexed by Zotero ids,
            # where each entry is the RDF data of the Zotero item.
            entries = {
                e.find('{http://zotero.org/ns/api}key').text:
                    e.find('.//{http://www.w3.org/2005/Atom}content/*[1]/*[1]') for
                    e in page.findall('.//{http://www.w3.org/2005/Atom}entry')
            }
            count = len(entries)
            # Replace the XML element in the dict values by a dictionary of RDF
            # attributes with their respective values.
            page = {
                key: extract_from_rdf(rdf)
                for key, rdf in entries.items() if rdf is not None
            }
            return (page, count)

        zotero_data = {}
        zotero_start = 0
        error_count = 0
        last_error = None
        while True:
            if error_count >= _max_errors:
                raise Exception(f"Too many failures fetching data from the Zotero API: {last_error}")
            try:
                (page, count) = zotero_page(zotero_start, 100)
                print(f"Fetched {count} records from Zotero's API/{len(page)} items with proper data.")
                if count == 0:
                    break
                zotero_start += count
                zotero_data.update(page)
                error_count = 0
            except Exception as e:
                last_error = e
                error_count += 1
        return zotero_data
    
    @staticmethod 
    def get_voyages_data(options):
        voyages_data = []
        sv_headers = { "Authorization": f"Token {options['voyages_key']}" }
        idx_page = 1
        error_count = 0
        last_error = None
        while True:
            if error_count >= _max_errors:
                raise Exception(f"Too many failures fetching data from the Voyages API: {last_error}")
            try:
                res = requests.post(
                    f"{options['voyages_url']}/docs/",
                    headers=sv_headers,
                    json={ "results_page": idx_page, "results_per_page": 10, "files": [] },
                    timeout=60)
                page = res.json()
                if not page:
                    break
                voyages_data += page
                print(f"Fetched {len(page)} rows [first id={page[0]['id']}]")
                error_count = 0
                idx_page += 1
            except Exception as e:
                last_error = e
                error_count += 1
                continue
        return voyages_data
    
    def handle(self, *args, **options):
        zotero_groups_url = f"{options['zotero_url']}/users/{options['zotero_userid']}/groups"
        res = requests.get(zotero_groups_url, timeout=30)
        # Retrieve the group id from the Zotero API.
        match = next(item for item in res.json() if item['data']['name'] == options['zotero_groupname'])
        group_id = match['id']
        print(f"Zotero group id is {group_id}")

        # zotero_data = Command.get_zotero_data(options, group_id)
        voyages_data = Command.get_voyages_data(options)
        print(f"{len(voyages_data)}")