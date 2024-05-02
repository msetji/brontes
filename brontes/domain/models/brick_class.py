from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class BrickClass:
  uri: str
  label: Optional[str] = None
  description: Optional[str] = None
  parents: Optional[List['BrickClass']] = field(default_factory=list)
