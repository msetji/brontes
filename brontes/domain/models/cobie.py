# This file contains the dataclasses that represent the COBie data model
# COBie (Construction Operations Building Information Exchange) is a standard for the exchange of facility data

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from .discipline import Discipline
from .ifc_reference import IFCReference

@dataclass
class Facility:
  uri: str
  name: str
  address: Optional[str] = None
  latitude: Optional[float] = None
  longitude: Optional[float] = None
  ifc_references: list[IFCReference] = field(default_factory=list)

@dataclass
class Portfolio:
  uri: str
  name: str
  facilities: list[Facility] = field(default_factory=list)

@dataclass
class Category:
  uri: str
  hasStringValue: str # The omniclass code and name combined
  name: Optional[str] = None # Just the name of the category
  omniClass: Optional[str] = None # Just the omniclass code
  pmTotalCost: Optional[float] = None
  pmLaborRate: Optional[float] = None
  maxMultiplier: Optional[float] = None
  isVerified: Optional[bool] = None
  pmFrequency: Optional[float] = None
  pmLaborCost: Optional[float] = None
  replacementCost: Optional[float] = None
  pmMaterialCost: Optional[float] = None
  pmTotalHours: Optional[float] = None
  pmTotalMinutes: Optional[float] = None
  minMultiplier: Optional[float] = None
  avgMultiplier: Optional[float] = None
  expectedLife: Optional[float] = None

@dataclass
class Floor:
  uri: str
  name: str
  description: Optional[str] = None
  elevation: Optional[float] = None
  height: Optional[float] = None

@dataclass
class Space:
  uri: str
  name: str
  floor: Floor
  description: Optional[str] = None
  extIdentifier: Optional[str] = None
  grossArea: Optional[float] = None
  netArea: Optional[float] = None
  category: Optional[Category] = None

@dataclass
class Manufacturer:
  name: str
  uri: str

@dataclass
class Type:
  name: str
  uri: str
  discipline: Optional[Discipline] = None
  category: Optional[Category] = None
  warrantyDurationParts: Optional[str] = None
  warrantyGuarantorParts: Optional[str] = None
  warrantyGuarantorLabor: Optional[str] = None
  warrantyDurationLabor: Optional[str] = None
  warrantyDurationUnit: Optional[str] = None
  warrantyDescription: Optional[str] = None
  description: Optional[str] = None
  modelNumber: Optional[str] = None
  extIdentifier: Optional[str] = None
  nominalLength: Optional[str] = None
  embeddings: Optional[float] = None

@dataclass
class Component:
  uri: str
  name: str
  description: Optional[str] = None
  type: Optional[Type] = None
  space: Optional[Space] = None
  extIdentifier: Optional[str] = None
  serialNumber: Optional[str] = None
  installationDate: Optional[float] = None # Unix timestamp in seconds

@dataclass
class System:
  uri: str
  name: str
  components: list[Component] = field(default_factory=list)
  description: Optional[str] = None
  category: Optional[Category] = None
  
class DocumentExtractionStatus(Enum):
  PENDING = 'pending'
  SUCCESS = 'success'
  FAILED = 'failed'

@dataclass
class Document:
  name: str
  uri: str
  url: str
  fileType: Optional[str] = None
  extractionStatus: Optional[DocumentExtractionStatus] = None
  thumbnailUrl: Optional[str] = None
  discipline: Optional[Discipline] = None
  vectorStoreIds: Optional[list[str]] = None

@dataclass
class COBieSpreadsheet:
  facility: Facility | None = None
  floors: list[Floor] = field(default_factory=list)
  spaces: list[Space] = field(default_factory=list)
  types: list[Type] = field(default_factory=list)
  components: list[Component] = field(default_factory=list)
  systems: list[System] = field(default_factory=list)
  documents: list[Document] = field(default_factory=list)