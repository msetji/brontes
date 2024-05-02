# This file contains the dataclasses that represent the bacnet data model
# BACnet is a standard for building automation and control networks

from dataclasses import dataclass, field
from typing import List, Optional

from .brick_class import BrickClass

@dataclass
class Point:
  """A point represents a sensor or actuator on the bacnet network."""
  uri: str
  timeseriesId: str
  object_name: str
  object_type: Optional[str] = None
  object_index: Optional[str] = None
  object_units: Optional[str] = None
  collect_enabled: Optional[bool] = None
  object_description: Optional[str] = None
  value: Optional[float] = None
  ts: Optional[str] = None
  embedding: Optional[List[float]] = None
  brick_class: Optional[BrickClass] = None
  mqtt_topic: Optional[str] = None

@dataclass
class Device:
  """A device is a controller on the bacnet network. Think a raspberry pi."""
  uri: str  # https://syyclops.com/{portfolio}/{facility}/device/{device_address}-{device_id}
  device_name: str
  device_id: str
  device_description: Optional[str] = None
  device_address: Optional[str] = None
  points: List[Point] = field(default_factory=list)
  template_id: Optional[str] = None