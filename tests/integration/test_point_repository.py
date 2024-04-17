from brontes.domain.repository import PointRepository
from brontes.domain.model import Point, Device, PointUpdates
import pytest

@pytest.fixture(scope="session")
def point_repository(knowledge_graph, timescale):
  return PointRepository(kg=knowledge_graph, ts=timescale)

def test_create_point(point_repository):
  point = Point(uri="https://syyclops.com/example/point", timeseriesId="test_timeseries_id", object_name="Test Point 1")
  device = Device(uri="https://syyclops.com/example/device", device_name="test_device", device_id="3014")
  point = point_repository.create_point(device, point)
  assert point is not None
  assert point.uri == "https://syyclops.com/example/point"

def test_get_points(point_repository):
  points = point_repository.get_points(facility_uri="https://syyclops.com/example/example", device_uri="https://syyclops.com/example/device")

  assert len(points) == 1
  assert points[0].uri == "https://syyclops.com/example/point"

def test_update(point_repository):
  point_uri = "https://syyclops.com/example/point"
  point_updates = PointUpdates(object_name="Test Updating Point Name")
  point_repository.update_point(point_uri, point_updates)

  point = point_repository.get_point(point_uri)
  assert point is not None
  assert point.object_name == "Test Updating Point Name"
