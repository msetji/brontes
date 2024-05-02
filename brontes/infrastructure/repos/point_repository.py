from collections import OrderedDict
from dataclasses import asdict
from typing import List

from brontes.infrastructure import KnowledgeGraph, Timescale
from brontes.domain.models import Point, BrickClass, Device

class PointRepository:
  def __init__(self, kg: KnowledgeGraph, ts: Timescale):
    self.kg = kg
    self.ts = ts

  def get_points(self, facility_uri: str, component_uri: str | None = None, device_uri: str | None = None, collect_enabled: bool = None) -> List[Point]:
    query = "MATCH (p:Point"
    if collect_enabled is not None:
      query += "{collect_enabled: $collect_enabled}"
    query += ")"
    if device_uri: 
      query += "-[:objectOf]->(d:Device {uri: $device_uri})"
    elif component_uri: 
      query += "-[:objectOf]-(d:Device)-[:isDeviceOf]-(c:Component {uri: $component_uri})"
    query += " OPTIONAL MATCH (p)-[:hasBrickClass]-(b:Class)"
    query += " WHERE p.uri STARTS WITH $uri RETURN p, b as brick_class ORDER BY p.object_name DESC"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, component_uri=component_uri, uri=facility_uri, collect_enabled=collect_enabled, device_uri=device_uri)
        data = result.data()
        points: List[Point] = []
        for record in data:
          point = Point(
            uri=record['p']['uri'],
            timeseriesId=record['p']['timeseriesId'],
            object_name=record['p']['object_name'],
            object_type=record['p'].get('object_type'),
            object_units=record['p'].get('object_units'),
            object_index=record['p'].get('object_index'),
            collect_enabled=record['p'].get('collect_enabled'),
            object_description=record['p'].get('object_description'),
            mqtt_topic=record['p'].get('mqtt_topic'),
          )
          if 'brick_class' in record.keys() and record['brick_class']:
            point.brick_class = BrickClass(
              uri=record['brick_class']['uri'],
              label=record['brick_class'].get('label'),
              description=record['brick_class'].get('description'),
            )
          points.append(point)

      ids = [point.timeseriesId for point in points]
      if len(ids) > 0:
        readings = self.ts.get_latest_values(ids)
        readings_dict = OrderedDict((reading.timeseriesid, {"value": reading.value, "ts": reading.ts}) for reading in readings)

        for point in points:
          if point.timeseriesId in readings_dict:
            point.value = readings_dict[point.timeseriesId]['value']
            point.ts = readings_dict[point.timeseriesId]['ts']
      return points
    except Exception as e:
      raise e
    
  def get_point(self, point_uri: str) -> Point:
    query = """MATCH (p:Point {uri: $point_uri})
              OPTIONAL MATCH (p)-[:hasBrickClass]->(b:Class:Resource)
              OPTIONAL MATCH path=(b)-[:SCO*]->(parent:Class)
              WITH p, b, COLLECT(parent) AS parents
              RETURN p, b AS brick_class, parents"""
    try:
      with self.kg.create_session() as session:
        result = session.run(query, point_uri=point_uri)
        data = result.data()
        point = Point(
          uri=data[0]['p']['uri'],
          timeseriesId=data[0]['p']['timeseriesId'],
          object_name=data[0]['p']['object_name'],
          object_type=data[0]['p'].get('object_type'),
          object_index=data[0]['p'].get('object_index'),
          object_units=data[0]['p'].get('object_units'),
          collect_enabled=data[0]['p'].get('collect_enabled'),
          object_description=data[0]['p'].get('object_description'),
          mqtt_topic=data[0]['p'].get('mqtt_topic'),
        )
        if data[0]['brick_class']:
          parents = [
            BrickClass(
              uri=parent['uri'],
              label=parent.get('label'),
              description=parent.get('description'),
            ) for parent in data[0]['parents']
          ]
          brick_class = BrickClass(
            uri=data[0]['brick_class']['uri'],
            label=data[0]['brick_class'].get('label'),
            description=data[0]['brick_class'].get('description'),
          )
          brick_class.parents = parents
          point.brick_class = brick_class
          
      return point
    except Exception as e:
      raise e
  
  def create_point(self, device: Device, point: Point, brick_class_uri: str | None = None) -> Point | None:
    query = """
      MERGE (d:Device:Resource {uri: $device_uri})
        ON CREATE SET d = $device
      CREATE (p:Point:Resource $point) 
      MERGE (p)-[:objectOf]->(d)
    """
    if brick_class_uri:
      query += " WITH p MATCH (b:Class {uri: $brick_class_uri}) MERGE (p)-[:hasBrickClass]->(b)"
    query += " RETURN p"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device_uri=device.uri, point=asdict(point), brick_class_uri=brick_class_uri, device=asdict(device)).single()
        if result:
          return Point(
            uri=result['p']['uri'],
            timeseriesId=result['p']['timeseriesId'],
            object_name=result['p']['object_name'],
            object_type=result['p'].get('object_type'),
            object_index=result['p'].get('object_index'),
            object_units=result['p'].get('object_units'),
            collect_enabled=result['p'].get('collect_enabled'),
            object_description=result['p'].get('object_description'),
            mqtt_topic=result['p'].get('mqtt_topic'),
          )
        return None
    except Exception as e:
      raise e
  
  def update_point(self, point_uri: str, updates: dict = None, new_brick_class_uri: str = None):
    """
    Update properties of a point and optionally its brick class relationship.

    :param point_uri: The URI of the point to update.
    :param updates: A dictionary of property updates (e.g., {"object_name": "new_name"}).
    :param new_brick_class_uri: Optional. The URI of the new brick class to associate with the point.
    """
    try:
      with self.kg.create_session() as session:
        # Update point properties
        if updates:
          update_props_query = "MATCH (p:Point {uri: $point_uri}) SET "
          update_props_query += ", ".join(f"p.{k} = ${k}" for k in updates.keys())
          session.run(update_props_query, point_uri=point_uri, **updates)

        # Update brick class relationship if specified
        if new_brick_class_uri:
          update_brick_class_query = """
          MATCH (p:Point {uri: $point_uri})
          OPTIONAL MATCH (p)-[r:hasBrickClass]->(:Class)
          DELETE r
          WITH p
          MATCH (b:Class {uri: $new_brick_class_uri})
          MERGE (p)-[:hasBrickClass]->(b)
          """
          session.run(update_brick_class_query, point_uri=point_uri, new_brick_class_uri=new_brick_class_uri)
    except Exception as e:
      raise e

  def points_history(self, start_time: str, end_time: str, point_uris: list[str]):
    query = "MATCH (p:Point) WHERE p.uri in $point_uris RETURN p"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, point_uris=point_uris)
        points = [
          Point(
            uri=record['p']['uri'],
            timeseriesId=record['p']['timeseriesId'],
            object_name=record['p']['object_name'],
            object_type=record['p'].get('object_type'),
            object_index=record['p'].get('object_index'),
            object_units=record['p'].get('object_units'),
            collect_enabled=record['p'].get('collect_enabled'),
            object_description=record['p'].get('object_description'),
            mqtt_topic=record['p'].get('mqtt_topic'),
          ) for record in result.data()
        ]

      points = [asdict(point) for point in points]
      ids = []
      for point in points: 
        point.pop('embedding', None)
        ids.append(point['timeseriesId'])

      data = self.ts.get_timeseries(ids, start_time, end_time)
      data_dict = {item['timeseriesid']: item['data'] for item in data}

      for point in points:
        point['data'] = data_dict.get(point['timeseriesId'], [])

      # Group points by object_units
      grouped_points = {}
      for point in points:
        object_unit = point['object_units']
        if object_unit not in grouped_points:
          grouped_points[object_unit] = []
        grouped_points[object_unit].append(point)
    except Exception as e:
      raise e

    # Convert the dictionary to a list of groups
    grouped_points_list = [{'object_unit': k, 'points': v} for k, v in grouped_points.items()]

    return grouped_points_list