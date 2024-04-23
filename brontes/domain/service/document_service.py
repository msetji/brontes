from brontes.domain.repository import DocumentRepository
from brontes.domain.model.document import Document, DocumentQuery
from typing import List, Literal

class DocumentService:
  def __init__(self, document_repository: DocumentRepository):
    self.document_repository = document_repository

  def list_documents(self, facility_uri: str) -> List[Document]:
    return self.document_repository.list(facility_uri)

  def upload_document(self, facility_uri: str, file_content: bytes, file_name: str, file_type: str, discipline: Literal['Architectural', 'Plumbing', 'Electrical', 'Mechanical'] , space_uri: str | None = None, type_uri: str | None = None, component_uri: str | None = None) -> Document:
   return self.document_repository.upload(facility_uri, file_content, file_name, file_type, discipline,space_uri,type_uri,component_uri)
  
  def run_extraction_process(self, portoflio_uri: str, facility_uri: str, file_content, file_name: str, doc_uri: str, doc_url: str):
    return self.document_repository.run_extraction_process(portoflio_uri, facility_uri, file_content, file_name, doc_uri, doc_url)
  
  def delete_document(self, doc_uri: str):
    return self.document_repository.delete(doc_uri)
  
  def search(self, params: DocumentQuery):
    return self.document_repository.search(params)