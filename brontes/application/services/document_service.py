from typing import List, Optional
import logging
import os
import tempfile
import fitz
import io
from uuid import uuid4
import mimetypes

from langchain.vectorstores import VectorStore
from langchain_community.document_loaders.unstructured import UnstructuredAPIFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from brontes.infrastructure.repos import DocumentRepository
from brontes.domain.models import Document, Discipline
from brontes.application.dtos.document_dto import DocumentQuery, DocumentMetadataChunk
from brontes.infrastructure import BlobStore

class DocumentService:
  """
  This application service provides the functionality to interact with documents. It is responsible for uploading, listing, and deleting documents.

  It also provides the functionality to extract text from a document and add it to the vector store.
  """
  def __init__(self, document_repository: DocumentRepository, blob_store: BlobStore, vector_store: VectorStore):
    self.document_repository = document_repository
    self.vector_store = vector_store
    self.blob_store = blob_store

  def list_documents(self, facility_uri: str, space_uri: Optional[str] = None, type_uri: Optional[str] = None, component_uri: Optional[str] = None) -> List[Document]:
    try:
      return self.document_repository.list(facility_uri,space_uri,type_uri,component_uri)
    except Exception as e:
      raise e

  def upload_document(self, facility_uri: str, file_content: bytes, file_name: str, discipline: Discipline, space_uri: str | None = None, type_uri: str | None = None, component_uri: str | None = None) -> Optional[Document]:
    try:
      file_type = mimetypes.guess_type(file_name)[0]
      # Create the thumbnail
      thumbnail_url = None
      if file_type == "application/pdf":
        doc = fitz.open("pdf", io.BytesIO(file_content))
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(100/72, 100/72))
        thumbnail_url = self.blob_store.upload_file(file_content=pix.tobytes(), file_name=f"{file_name}_thumbnail.png", file_type="image/png")
    
      # Upload the file to the blob store
      file_url = self.blob_store.upload_file(file_content=file_content, file_name=file_name, file_type=file_type)
      
      # Create the document node in the graph
      doc_uri = f"{facility_uri}/document/{str(uuid4())}"
      document = Document(
        uri=doc_uri,
        name=file_name,
        url=file_url,
        thumbnailUrl=thumbnail_url,
        discipline=discipline,
        extractionStatus="pending",
        fileType=file_type
      )
      self.document_repository.upload(facility_uri=facility_uri, document=document, space_uri=space_uri, type_uri=type_uri, component_uri=component_uri)
    
      return document
    except Exception as e:
      raise e
  
  def run_extraction_process(self, portfolio_uri: str, facility_uri: str, file_content, document: Document):
    """
    Extract text from a document and add it to the vector store.
    Store the vector store ids in the document.
    """
    try:
      # Create tempfile because we need to pass in file path not file contents
      _, file_extension = os.path.splitext(document.name)
      temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
      temp_file.write(file_content)

      # Extract text from document
      loader = UnstructuredAPIFileLoader(
        url=os.environ.get("UNSTRUCTURED_URL"), 
        api_key=os.environ.get("UNSTRUCTURED_API_KEY"),
        mode="elements",
        file_path=temp_file.name,
        strategy="fast",
        pdf_infer_table_structure=True,
        skip_infer_table_types=[""],
        max_characters=1500,
        new_after_n_chars=1500,
        chunking_strategy="by_title",
        combine_under_n_chars=500,
        coordinates=True
      )
      docs = loader.load()
      text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=20,
      )
      docs = text_splitter.split_documents(docs)

      # Clean up temp file
      temp_file.close()

      # Add metadata to vector store
      for doc in docs:
        doc.metadata['source'] = document.name
        doc.metadata['portfolio_uri'] = portfolio_uri
        doc.metadata['facility_uri'] = facility_uri
        doc.metadata['document_uri'] = document.uri
        doc.metadata['document_url'] = document.url
    except Exception as e:
      document.extractionStatus = "failed"
      self.document_repository.update(document)
      raise e
    
    # Now we need to update the document with the vector store ids
    try:
      ids = self.vector_store.add_documents(docs)
      document.vectorStoreIds = ids
      self.document_repository.update(document)
    except Exception as e:
      document.extractionStatus = "failed"
      self.document_repository.update(document)
      raise e
    
    # Finally, update the document status to success
    document.extractionStatus = "success"
    self.document_repository.update(document)
    return document
  
  def delete_document(self, doc_uri: str):
    """
    Delete a document from the graph and the blob store and the vector store
    """
    try:
      document = self.document_repository.get(doc_uri)

      self.document_repository.delete(document=document) # remove from graph
      self.blob_store.delete_file(url=document.url) # remove from blob store
      if document.vectorStoreIds: # remove from vector store
        self.vector_store.delete(ids=document.vectorStoreIds)

    except Exception as e:
      logging.error(f"Error deleting document {doc_uri}: {e}")
      raise e
  
  def search(self, params: DocumentQuery) -> List[DocumentMetadataChunk]:
    """
    Search vector store for document metadata chunks
    """
    query = params.query
    limit = params.limit

    filter = {
      'portfolio_uri':{'$eq': params.portfolio_uri}
    }
    if params.facility_uri:
      filter['facility_uri'] = {'$eq': params.facility_uri}
    if params.document_uri:
      filter['document_uri'] = {'$eq': params.document_uri}
      
    try:
      docs = self.vector_store.similarity_search(query=query, k=limit, filter=filter)
      return [DocumentMetadataChunk(content=doc.page_content, metadata=doc.metadata) for doc in docs]
    except Exception as e:
      raise e
