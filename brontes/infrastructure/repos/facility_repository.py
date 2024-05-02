from typing import List, Optional
from dataclasses import asdict

from brontes.infrastructure import KnowledgeGraph
from brontes.domain.models import Facility

class FacilityRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg
  
  def get_facility(self, facility_uri: str) -> Optional[Facility]:
    try:
      with self.kg.create_session() as session:
        result = session.run("MATCH (f:Facility {uri: $uri}) RETURN f", uri=facility_uri)
        record = result.single()
        if record is None:
          raise Exception(f"Facility {facility_uri} not found")
        facility_record = record['f']
        return Facility(uri=facility_record['uri'], name=facility_record['name'], address=facility_record.get('address'), latitude=facility_record.get('latitude'), longitude=facility_record.get('longitude'))
    except Exception as e:
      raise e
    
  def list_facilities_for_portfolio(self, portfolio_uri: str) -> List[Facility]:
    try:
      with self.kg.create_session() as session:
        result = session.run("MATCH (c:Customer {uri: $uri})-[:HAS_FACILITY]->(f:Facility) RETURN f", uri=portfolio_uri).data()
        return [
          Facility(uri=f['f']['uri'], name=f['f']['name'], address=f['f'].get('address'), latitude=f['f'].get('latitude'), longitude=f['f'].get('longitude')) 
          for f in result
        ]
    except Exception as e:
      raise e
    
  def create_facility(self, facility: Facility, portfolio_uri: str) -> Optional[Facility]:
    try:
      with self.kg.create_session() as session:
        query = "MATCH (c:Customer {uri: $portfolio_uri}) CREATE (f:Facility $facility) CREATE (c)-[:HAS_FACILITY]->(f) RETURN f"
        result = session.run(query=query, name=facility.name, uri=facility.uri, portfolio_uri=portfolio_uri, facility=asdict(facility))
        record = result.single()
        if record is None:
          raise ValueError(f"Error creating facility {facility.uri}")
        return Facility(uri=record['f']['uri'], name=record['f']['name'], address=record['f'].get('address'), latitude=record['f'].get('latitude'), longitude=record['f'].get('longitude'))
    except Exception as e:
      raise e
