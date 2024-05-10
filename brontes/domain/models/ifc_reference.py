from dataclasses import dataclass
from .discipline import Discipline

@dataclass
class IFCReference:
  name: str
  IfcGlobalID: str
  discipline: Discipline
