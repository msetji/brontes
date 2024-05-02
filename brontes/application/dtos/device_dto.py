from dataclasses import dataclass
from typing import Optional

@dataclass
class DeviceCreateParams:
  device_name: str
  device_address: str
  device_id: str
  device_description: Optional[str] = None
  object_units: Optional[str] = None
  object_type: Optional[str] = None
  template_id: Optional[str] = None