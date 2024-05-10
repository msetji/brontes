from uuid import uuid4

from brontes.domain.utils.bacnet import load_bacnet_json_file, convert_bacnet_data_to_rdf
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
      g = convert_bacnet_data_to_rdf(devices)
      graph_string = g.serialize(format='turtle', encoding='utf-8').decode()
      unique_id = str(uuid4())
      url = self.blob_store.upload_file(file_content=graph_string.encode(), file_name=f"{unique_id}_cobie.ttl", file_type="text/turtle")
      self.kg.import_rdf_data(url)
    except Exception as e:
      raise e