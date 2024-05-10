from typing import Tuple, Dict
from uuid import uuid4

from brontes.infrastructure import BlobStore, KnowledgeGraph
from brontes.infrastructure.repos import FacilityRepository
from brontes.domain.utils.cobie import validate_spreadsheet, convert_to_rdf, parse_spreadsheet

class CobieToGraphService:
  """
  Import a cobie spreadsheet data into the knowledge graph. 
  """
  def __init__(self, blob_store: BlobStore, kg: KnowledgeGraph, facility_repository: FacilityRepository):
    self.blob_store = blob_store
    self.kg = kg
    self.facility_repository = facility_repository

  def process_cobie_spreadsheet(self, facility_uri, file: str | bytes, validate: bool = True) -> Tuple[bool, Dict]:
    if validate:
      errors_found, errors, _ = validate_spreadsheet(file_content=file)
      if errors_found:
        return errors_found, errors
      
    facility = self.facility_repository.get_facility(facility_uri=facility_uri)
    cobie_spreadsheet = parse_spreadsheet(facility=facility, file=file)
    
    rdf_graph_str = convert_to_rdf(spreadsheet=cobie_spreadsheet)
    unique_id = str(uuid4())
    url = self.blob_store.upload_file(file_content=rdf_graph_str.encode(), file_name=f"{unique_id}_cobie.ttl", file_type="text/turtle")
    self.kg.import_rdf_data(url)

    return False, None