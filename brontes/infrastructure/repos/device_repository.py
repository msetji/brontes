import os
import numpy as np
from dataclasses import asdict
from typing import Optional, List

from brontes.domain.models import Device, Point
from brontes.application.dtos.device_dto import DeviceCreateParams 
from brontes.infrastructure import KnowledgeGraph
from brontes.utils import dbscan_cluster

class DeviceRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg
  
  def get_devices(self, facility_uri: str, component_uri: Optional[str]) -> List[Device]:
    query = "MATCH (d:Device) where d.uri starts with $facility_uri OPTIONAL MATCH (d)-[:objectOf]-(p:Point)"
    if component_uri:
      query += " MATCH (d)-[:isDeviceOf]->(c:Component {uri: $component_uri})"
    query += " with d, collect(p) AS points RETURN d as device, points ORDER BY d.device_name DESC"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, facility_uri=facility_uri, component_uri=component_uri)
        data = result.data()
        devices = []
        for record in data:
          device_data = record['device']
          points_data = record['points']
          device = Device(
            uri=device_data['uri'],
            device_name=device_data['device_name'],
            device_id=device_data['device_id'],
            device_address=device_data.get('device_address'),
            template_id=device_data.get('template_id'),
          )
          points = [
            Point(
              uri=point_data['uri'],
              timeseriesId=point_data['timeseriesId'],
              object_name=point_data['object_name'],
              object_type=point_data.get('object_type'),
              object_index=point_data.get('object_index'),
              object_units=point_data.get('object_units'),
              collect_enabled=point_data.get('collect_enabled'),
              object_description=point_data.get('object_description'),
              mqtt_topic=point_data.get('mqtt_topic'),
            ) 
            for point_data in points_data
          ]
          device.points = points
          devices.append(device)
        return devices
    except Exception as e:
      raise e
    
  def get_device(self, device_uri: str) -> Device:
    query = "MATCH (d:Device {uri: $device_uri}) OPTIONAL MATCH (d)-[:objectOf]-(p:Point) RETURN d as device, collect(p) as points"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device_uri=device_uri)
        data = result.data()
        device_data = data[0]['device']
        points_data = data[0]['points']
        device = Device(
          uri=device_data['uri'],
          device_name=device_data['device_name'],
          device_id=device_data['device_id'],
          device_address=device_data.get('device_address'),
          template_id=device_data.get('template_id'),
        )
        points = [
          Point(
            uri=point_data['uri'],
            timeseriesId=point_data['timeseriesId'],
            object_name=point_data['object_name'],
            object_type=point_data.get('object_type'),
            object_index=point_data.get('object_index'),
            object_units=point_data.get('object_units'),
            collect_enabled=point_data.get('collect_enabled'),
            object_description=point_data.get('object_description'),
            mqtt_topic=point_data.get('mqtt_topic'),
          ) for point_data in points_data
        ]
        device.points = points
        return device
    except Exception as e:
      raise e
  
  def create_device(self, facility_uri: str, device: DeviceCreateParams) -> Device:
    uri = f"{facility_uri}/device/{device.device_address}-{device.device_id}"
    device = Device(uri=uri, **asdict(device))
    query = "CREATE (d:Device:Resource $device) RETURN d"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device=asdict(device))
        data = result.data()
        return Device(**data[0]['d'])
    except Exception as e:
      raise e
    
  def update(self, device_uri: str, new_details: dict) -> None:
    set_clauses = ', '.join([f'{key}: ${key}' for key in new_details.keys()])
    query = f"MATCH (d:Device {{uri: $device_uri}}) SET d += {{{set_clauses}}} RETURN d"
    try:
      with self.kg.create_session() as session:
        session.run(query, device_uri=device_uri, **new_details)
    except Exception as e:
      raise e

  def link_device_to_component(self, device_uri: str, component_uri: str):
    query = "MATCH (d:Device {uri: $device_uri}) MATCH (c:Component {uri: $component_uri}) MERGE (d)-[:isDeviceOf]->(c) RETURN d, c"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device_uri=device_uri, component_uri=component_uri)
        if result.single() is None: raise ValueError("Error linking device to component")
        return "Device linked to component"
    except Exception as e:
      raise e
    
  def get_device_graphic(self, device_uri: str):
    query = "MATCH (d:Device {uri: $device_uri}) return d"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device_uri=device_uri)
        record = result.single()
        if record is None: raise ValueError("Graphic not found")
        template_id = record['d']['template_id']
      svg_graphic = os.path.join(os.path.dirname(__file__), "svg_templates", f"{template_id}.svg") # Search the device_graphcs directory for the device graphic
      if os.path.exists(svg_graphic):
        return svg_graphic
    except Exception as e:
      raise e
    
  def cluster_devices(self, facility_uri: str):
    """
    Cluster the bacnet devices using the embeddings that were created from vectorizing the graph.
    """
    devices = self.get_devices(facility_uri)
    embeddings = [device['embedding'] for device in devices]
    embeddings = np.vstack(embeddings)
    cluster_assignments = dbscan_cluster(embeddings)
    
    # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
    clusters = {}
    for i in range(len(cluster_assignments)):
      cluster = cluster_assignments[i]
      if cluster not in clusters:
        clusters[cluster] = []
      clusters[cluster].append(devices[i]['device_name']) 

    return clusters