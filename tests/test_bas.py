from openoperator.core import BAS
import unittest
from unittest.mock import Mock, patch
import json
from rdflib import Namespace, RDF, URIRef, Literal

class TestBAS(unittest.TestCase):
  @patch('openoperator.services.knowledge_graph.KnowledgeGraph')
  def setUp(self, mock_knowledge_graph):
    mock_kg = mock_knowledge_graph.return_value
    facility = Mock()
    facility.knowledge_graph = mock_kg
    facility.uri = "https://openoperator.com/exampleCustomer/exampleFacility"
    embeddings = Mock()
    self.bas = BAS(facility, embeddings)

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.bas.knowledge_graph.create_session.return_value = session_mock
    return session_mock
  
  def test_devices(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "d": {
          "device_name": "test_device",
          "uri": "https://openoperator.com/facility/device"
        }
      },
      {
        "d": {
          "device_name": "test_device2",
          "uri": "https://openoperator.com/facility/device2"
        }
      }
    ]
    session_mock.run.return_value = mock_query_result

    devices = self.bas.devices()

    assert len(devices) == 2
    assert devices[0]['device_name'] == "test_device"
    assert devices[0]['uri'] == "https://openoperator.com/facility/device"
    assert devices[1]['device_name'] == "test_device2"

  def test_points(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "p": {
          "point_name": "test_point",
          "uri": "https://openoperator.com/facility/point"
        }
      },
      {
        "p": {
          "point_name": "test_point2",
          "uri": "https://openoperator.com/facility/point2"
        }
      }
    ]
    session_mock.run.return_value = mock_query_result

    points = self.bas.points()

    assert len(points) == 2
    assert points[0]['point_name'] == "test_point"
    assert points[0]['uri'] == "https://openoperator.com/facility/point"
    assert points[1]['point_name'] == "test_point2"

  def test_points_with_device_uri(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "p": {
          "point_name": "test_point",
          "uri": "https://openoperator.com/facility/point"
        }
      },
      {
        "p": {
          "point_name": "test_point2",
          "uri": "https://openoperator.com/facility/point2"
        }
      }
    ]
    session_mock.run.return_value = mock_query_result

    points = self.bas.points(device_uri="https://openoperator.com/facility/device")

    assert len(points) == 2
    assert points[0]['point_name'] == "test_point"
    assert points[0]['uri'] == "https://openoperator.com/facility/point"
    assert points[1]['point_name'] == "test_point2"

  def create_bacnet_json_data(self) -> bytes:
    data = [
      {
        "Name": "example/example/301:14-3014/device/3014",
        "Site": "Example Site",
        "Client": "Example Client",
        "Point Type": "",
        "Collect Enabled": "False",
        "Collect Interval": "",
        "Marker Tags": "",
        "Kv Tags": "[{}]",
        "Bacnet Data": "[{\"device_id\":\"3014\",\"device_name\":\"VAV-D2-37\",\"object_name\":\"VAV-D2-37\",\"object_type\":\"device\",\"object_index\":\"3014\",\"object_units\":\"\",\"present_value\":\"\",\"device_address\":\"301:14\",\"scrape_enabled\":\"False\",\"scrape_interval\":\"0\",\"device_description\":\"\",\"object_description\":\"\"}]",
        "Collect Config": "[{}]",
        "Updated": "2022-07-07 15:22:54.243447",
        "Created": "2022-01-10 22:09:55.493949"
      },
      {
        "Name": "example/example/301:14-3014/analogInput/1",
        "Site": "Example Site",
        "Client": "Example Client",
        "Point Type": "",
        "Collect Enabled": "True",
        "Collect Interval": "300",
        "Marker Tags": "",
        "Kv Tags": "[{}]",
        "Bacnet Data": "[{\"device_id\":\"3014\",\"device_name\":\"VAV-D2-37\",\"object_name\":\"3A14-Space-Co2\",\"object_type\":\"analogInput\",\"object_index\":\"1\",\"object_units\":\"noUnits\",\"present_value\":\"0.0\",\"device_address\":\"301:14\",\"scrape_enabled\":\"False\",\"scrape_interval\":\"0\",\"device_description\":\"\",\"object_description\":\"\"}]",
        "Collect Config": "[{}]",
        "Updated": "2022-07-07 15:22:54.247305",
        "Created": "2022-01-10 22:09:55.502661"
      },
      {
        "Name": "example/example/192.168.1.40-8000/analogValue/22",
        "Site": "Example Site",
        "Client": "Example Client",
        "Point Type": "",
        "Collect Enabled": "True",
        "Collect Interval": "300",
        "Marker Tags": "",
        "Kv Tags": "[{}]",
        "Bacnet Data": "[{\"device_id\":\"8000\",\"device_name\":\"AHU1\",\"object_name\":\"AHU01-DAT-SP1\",\"object_type\":\"analogValue\",\"object_index\":\"22\",\"object_units\":\"degreesFahrenheit\",\"present_value\":\"70.0\",\"device_address\":\"192.168.1.40\",\"scrape_enabled\":\"False\",\"scrape_interval\":\"0\",\"device_description\":\"\",\"object_description\":\"\"}]",
        "Collect Config": "[{}]",
        "Updated": "2022-07-07 15:22:47.873095",
        "Created": "2022-01-10 22:09:56.009211"
      },
    ]
    return bytes(json.dumps(data), 'utf-8')
  
  def test_convert_bacnet_data_to_rdf(self):
    bacnet_data = self.create_bacnet_json_data()
    g = self.bas.convert_bacnet_data_to_rdf(bacnet_data)
    
    BACNET = Namespace("http://data.ashrae.org/bacnet/#")
    device_uri = URIRef("https://openoperator.com/exampleCustomer/exampleFacility/301:14-3014/device/3014")
    assert (device_uri, RDF.type, BACNET.Device) in g
    assert (device_uri, BACNET.device_id, Literal("3014")) in g
    assert (device_uri, BACNET.device_name, Literal("VAV-D2-37")) in g
    assert (device_uri, BACNET.device_address, Literal("301:14")) in g
    assert (device_uri, BACNET.scrape_enabled, Literal("False")) in g

    point_uri = URIRef("https://openoperator.com/exampleCustomer/exampleFacility/301:14-3014/analogInput/1")
    assert (point_uri, RDF.type, BACNET.Point) in g
    assert (point_uri, BACNET.objectOf, device_uri) in g
    assert (point_uri, BACNET.object_name, Literal("3A14-Space-Co2")) in g
    assert (point_uri, BACNET.object_type, Literal("analogInput")) in g
    assert(point_uri, BACNET.timeseriesId, Literal("example/example/301:14-3014/analogInput/1")) in g

  def test_convert_bacnet_data_to_rdf_no_data(self):
    bacnet_data = bytes(json.dumps([]), 'utf-8')
    g = self.bas.convert_bacnet_data_to_rdf(bacnet_data)
    assert len(g) == 0
  
  def test_convert_bacnet_data_to_rdf_invalid_data(self):
    bacnet_data = bytes(json.dumps([{"invalid": "data"}]), 'utf-8')
    with self.assertRaises(Exception):
      self.bas.convert_bacnet_data_to_rdf(bacnet_data)
    
  def test_convert_bacnet_data_to_rdf_missing_keys(self):
    bacnet_data = bytes(json.dumps([{"Bacnet Data": "{}"}]), 'utf-8')
    g = self.bas.convert_bacnet_data_to_rdf(bacnet_data)
    assert len(g) == 0
  
  def test_upload_bacnet_data(self):
    bacnet_data = self.create_bacnet_json_data()
    session_mock = self.setup_session_mock()
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        'terminationStatus': 'OK',
        'triplesLoaded': 1,
        'triplesParsed': 1,
        'namespaces': {},
        'extraInfo': {}
      }
    ]
    session_mock.run.return_value = mock_query_result
    self.bas.upload_bacnet_data(bacnet_data)
    self.bas.blob_store.upload_file.assert_called_once()

  @patch('openoperator.core.bas.BAS.devices')
  @patch('openoperator.core.bas.BAS.points')
  def test_vectorize_graph(self, mock_points, mock_devices):
    mock_devices.return_value = [
      {
        "device_name": "test_device",
        "uri": "https://openoperator.com/facility/device"
      }
    ]
    mock_points.return_value = [
      {
        "object_name": "test_point",
        "uri": "https://openoperator.com/facility/point"
      }
    ]
    self.bas.embeddings.create_embeddings.return_value = [Mock(embedding=[0.1, 0.2, 0.3])]
    session_mock = self.setup_session_mock()

    self.bas.vectorize_graph()

    assert self.bas.embeddings.create_embeddings.call_count == 2
    self.bas.embeddings.create_embeddings.assert_called_with(['test_point'])

    # Check calls to session.run contain the correct Cypher query for devices and points
    device_query_call = [call for call in session_mock.run.call_args_list if "MATCH (n:Device)" in str(call)]
    point_query_call = [call for call in session_mock.run.call_args_list if "MATCH (n:Point)" in str(call)]
    self.assertTrue(device_query_call, "Device vectors not uploaded correctly.")
    self.assertTrue(point_query_call, "Point vectors not uploaded correctly.")

