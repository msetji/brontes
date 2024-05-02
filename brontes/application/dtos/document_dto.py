from dataclasses import dataclass, field
from typing import Optional
from typing_extensions import TypedDict

class DocumentMetadata(TypedDict, total=False):
  portfolio_uri: str
  facility_uri: str
  filename: str
  document_uri: Optional[str]
  document_url: Optional[str]
  filetype: Optional[str]
  page_number: Optional[int] 

@dataclass
class DocumentMetadataChunk:
  content: str
  metadata: DocumentMetadata

@dataclass
class DocumentQuery:
  portfolio_uri: str
  query: str
  limit: int = 25
  facility_uri: Optional[str] = None
  document_uri: Optional[str] = None