# from uuid import uuid4

from brontes.domain.utils.bacnet import load_bacnet_json_file, upload_to_graph 
from brontes.infrastructure import KnowledgeGraph, BlobStore
from brontes.infrastructure.repos import FacilityRepository

class BacnetToGraphService:
  """
  This application service is responsible for converting BACnet data to RDF format then uploading it to the knowledge graph.
  """
  def __init__(self, blob_store: BlobStore, kg: KnowledgeGraph, facility_repository: FacilityRepository) -> None:
    self.blob_store = blob_store
    self.kg = kg
    self.facility_repository = facility_repository

  def upload_bacnet_data(self, facility_uri: str, file: bytes):
    """
    This function takes a json file of bacnet data, converts it to rdf and uploads it to the knowledge graph.
    """
    try:
      facility = self.facility_repository.get_facility(facility_uri)
      devices = load_bacnet_json_file(facility, file)
      graph = self.kg.graph_store(batching=False)
      upload_to_graph(graph, devices)
    except Exception as e:
      raise e