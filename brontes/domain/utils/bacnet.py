from typing import List
import json
from rdflib import Graph, Literal, URIRef, RDF
from rdflib.namespace import XSD

from brontes.domain.models import Device, Point, Facility
from brontes.infrastructure.db.knowledge_graph import KnowledgeGraph

def load_bacnet_json_file(facility: Facility, file_content: bytes) -> List[Device]:
  """
  Load a json file of bacnet data and return a list of devices.
  """
  try:
    data = json.loads(file_content)
    devices: List[Device] = []
    for item in data:
      if item['Bacnet Data'] == None or item['Bacnet Data'] == "{}": continue
      bacnet_data = json.loads(item['Bacnet Data'])[0]

      # Check if the necessary keys are in bacnet_data
      if not all(key in bacnet_data for key in ['device_address', 'device_id', 'device_name']):
        print("Missing necessary key in bacnet_data, skipping this item.")
        continue

      if bacnet_data['device_name'] == None or bacnet_data['device_name'] == "":
        continue

      device_uri = f"{facility.uri}/device/{bacnet_data['device_address']}-{bacnet_data['device_id']}"
      # Check if its a bacnet device or a bacnet object
      if bacnet_data['object_type'] == "device":
        device = Device(
          uri=device_uri,
          device_name=bacnet_data['device_name'],
          device_id=bacnet_data['device_id'],
          device_address=bacnet_data['device_address'],
          device_description=bacnet_data.get('device_description')
        )
        devices.append(device)
      else:
        point_uri = f"{facility.uri}/point/{bacnet_data['device_address']}-{bacnet_data['device_id']}/{bacnet_data['object_type']}/{bacnet_data['object_index']}" 
        point = Point(
          uri=point_uri,
          timeseriesId=item['Name'],
          object_name=bacnet_data['object_name'],
          object_type=bacnet_data.get('object_type'),
          object_index=bacnet_data.get('object_index'),
          object_units=bacnet_data.get('object_units'),
          collect_enabled=item['Collect Enabled'],
          object_description=bacnet_data.get('object_description')
        )
        # Add the point to the device
        device = [d for d in devices if d.uri == device_uri][0] 
        device.points.append(point)
    return devices
  except Exception as e:
    raise e


def upload_to_graph(g: Graph, devices: List[Device]) -> Graph:
  """
  Upload the devices and their points to the graph store.
  """
  try:
    BACNET = KnowledgeGraph.prefixes['bacnet']
    A = RDF.type

    for device in devices:
      device_uri = URIRef(device.uri)
      g.add((device_uri, A, BACNET.Device))
      g.add((device_uri, BACNET.device_name, Literal(device.device_name)))
      g.add((device_uri, BACNET.device_id, Literal(device.device_id)))
      g.add((device_uri, BACNET.device_address, Literal(device.device_address)))
      g.add((device_uri, BACNET.device_description, Literal(device.device_description)))

      for point in device.points:
        point_uri = URIRef(point.uri)
        g.add((point_uri, A, BACNET.Point))
        g.add((point_uri, BACNET.timeseriesId, Literal(point.timeseriesId)))
        g.add((point_uri, BACNET.object_name, Literal(point.object_name)))
        g.add((point_uri, BACNET.object_type, Literal(point.object_type)))
        g.add((point_uri, BACNET.object_index, Literal(point.object_index)))
        g.add((point_uri, BACNET.object_units, Literal(point.object_units)))
        g.add((point_uri, BACNET.collect_enabled, Literal(point.collect_enabled, datatype=XSD.boolean)))
        g.add((point_uri, BACNET.object_description, Literal(point.object_description)))
        g.add((point_uri, BACNET.objectOf, device_uri))

  except Exception as e:
    raise e