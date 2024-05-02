from brontes.infrastructure.repos import FacilityRepository
from brontes.domain.models import Facility

def test_create_facility(knowledge_graph):
  facility_repository = FacilityRepository(kg=knowledge_graph)
  facility = Facility(name="Test Facility", uri="https://syyclops.com/example/testfacility2")
  portfolio_uri = "https://syyclops.com/example"

  created_facility = facility_repository.create_facility(facility=facility, portfolio_uri=portfolio_uri)

  assert created_facility is not None
  assert created_facility.uri == "https://syyclops.com/example/testfacility2"
  assert created_facility.name == "Test Facility"

def test_list_facilities_for_portfolio(knowledge_graph):
  facility_repository = FacilityRepository(kg=knowledge_graph)
  portfolio_uri = "https://syyclops.com/example"

  facilities = facility_repository.list_facilities_for_portfolio(portfolio_uri=portfolio_uri)

  assert len(facilities) == 2
  assert facilities[0].uri == "https://syyclops.com/example/example"

def test_get_facility(knowledge_graph):
  facility_repository = FacilityRepository(kg=knowledge_graph)
  facility_uri = "https://syyclops.com/example/example"

  facility = facility_repository.get_facility(facility_uri=facility_uri)

  assert facility is not None
  assert facility.uri == "https://syyclops.com/example/example"
  assert facility.name == "Example Facility"