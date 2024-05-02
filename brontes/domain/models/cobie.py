# This file contains the dataclasses that represent the COBie data model
# COBie (Construction Operations Building Information Exchange) is a standard for the exchange of facility data

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from .discipline import Discipline

@dataclass
class Facility:
  uri: str
  name: str
  address: Optional[str] = None
  latitude: Optional[float] = None
  longitude: Optional[float] = None

@dataclass
class Portfolio:
  uri: str
  name: str
  facilities: list[Facility] = field(default_factory=list)
  
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
  facility: Facility
  documents: list[Document] = field(default_factory=list)
