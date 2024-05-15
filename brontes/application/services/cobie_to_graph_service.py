from typing import Tuple, Dict

from brontes.infrastructure import BlobStore, KnowledgeGraph
from brontes.infrastructure.repos import FacilityRepository
from brontes.domain.utils.cobie import validate_spreadsheet, upload_to_graph, parse_spreadsheet

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

    graph = self.kg.graph_store(batching=False)
    upload_to_graph(g=graph, spreadsheet=cobie_spreadsheet)

    # No errors found
    return False, None