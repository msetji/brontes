from dataclasses import dataclass
from typing import Optional
from typing_extensions import TypedDict 

@dataclass
class PointReading: # TODO update point to use point reading
  ts: str
  value: float
  timeseriesid: str

class PointUpdates(TypedDict, total=False):
  """This is used to update a point's properties."""
  object_name: Optional[str]
  object_description: Optional[str]
  mqtt_topic: Optional[str]
  object_type: Optional[str]
  object_index: Optional[str]
  timeseriesId: Optional[str]

@dataclass
class PointCreateParams:
  object_name: str
  object_index: str
  timeseriesId: str
  object_type: Optional[str] = None
  object_units: Optional[str] = None
  collect_enabled: Optional[bool] = False
  mqtt_topic: Optional[str] = None
  object_description: Optional[str] = None

