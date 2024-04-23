import fitz
import io
import os
from uuid import uuid4
from typing import List, Literal
import tempfile
from langchain.vectorstores import VectorStore
from langchain_community.document_loaders.unstructured import UnstructuredAPIFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from brontes.domain.model.document import Document, DocumentQuery, DocumentMetadataChunk
from brontes.infrastructure import KnowledgeGraph, BlobStore

class DocumentRepository:
  def __init__(self, kg: KnowledgeGraph, blob_store: BlobStore, vector_store: VectorStore):
    self.kg = kg
    self.blob_store = blob_store
    self.vector_store = vector_store

  def list(self, facility_uri: str) -> List[Document]:
    with self.kg.create_session() as session:
      result = session.run("MATCH (d:Document)-[:documentTo]-(f:Facility {uri: $facility_uri}) RETURN d", facility_uri=facility_uri)
      data = result.data()
      return [Document(**record['d']) for record in data]
  
  def upload(self, facility_uri: str, file_content: bytes, file_name: str, file_type: str, discipline: Literal['Architectural', 'Plumbing', 'Electrical', 'Mechanical'], space_uri: str | None = None, type_uri: str | None = None, component_uri: str | None = None) -> Document:
    """
    Upload a file for a facility.

    1. Upload the file to the blob store
    2. Create a document node in the knowledge graph with extractionStatus = "pending"
    """
    try:
      thumbnail_url = None
      if file_type == "application/pdf":
        doc = fitz.open("pdf", io.BytesIO(file_content))
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(100/72, 100/72))
        thumbnail_url = self.blob_store.upload_file(file_content=pix.tobytes(), file_name=f"{file_name}_thumbnail.png", file_type="image/png")
      
      file_url = self.blob_store.upload_file(file_content=file_content, file_name=file_name, file_type=file_type)
    except Exception as e:
      raise e

    try:
      with self.kg.create_session() as session:
        doc_uri = f"{facility_uri}/document/{str(uuid4())}"

        #query for create document and relationship for given URI
        query = """ CREATE (d:Document:Resource {name: $name, url: $url, extractionStatus: 'pending', thumbnailUrl: $thumbnail_url, uri: $doc_uri, discipline: $discipline}) """
        query += " WITH d "
        query += " MATCH(f:Facility:Resource {uri: $facility_uri}) "
        createQuery = " CREATE (d)-[:documentTo]->(f)"

        if space_uri is not None:
          query += " , (s:Space:Resource {uri: $space_uri}) "
          createQuery += " , (d)-[:documentTo]->(s) "

        if type_uri is not None:
          query += " , (t:Type:Resource {uri: $type_uri}) "
          createQuery += " , (d)-[:documentTo]->(t) "

        if component_uri is not None:
          query += " , (c:Component:Resource {uri: $component_uri}) "
          createQuery += " , (d)-[:documentTo]->(c) "

        query += createQuery
        query +=  """RETURN d"""

        
        result = session.run(query, name=file_name, url=file_url, facility_uri=facility_uri, thumbnail_url=thumbnail_url, doc_uri=doc_uri, discipline=discipline, space_uri = space_uri, type_uri = type_uri, component_uri = component_uri)
        
        data = result.data()
        if len(data) == 0: raise ValueError("Document not created")
        return Document(extractionStatus="pending", name=file_name, uri=doc_uri, url=file_url, thumbnailUrl=thumbnail_url)
    except Exception as e:
      raise e
    
  def update_extraction_status(self, uri, status):
    """
    Update the extraction status of a document in the knowledge graph.
    pending, failed, or success
    """
    try:
      with self.kg.create_session() as session:
        query = "MATCH (d:Document {uri: $uri}) SET d.extractionStatus = $status RETURN d"
        result = session.run(query, uri=uri, status=status)
        return result.data()[0]['d']
    except Exception as e:
      raise e
        
  def run_extraction_process(self, portfolio_uri: str, facility_uri, file_content: bytes, file_name: str, doc_uri: str, doc_url: str):
    try:
      # Create tempfile because we need to pass in file path not file contents
      _, file_extension = os.path.splitext(file_name)
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
        doc.metadata['source'] = file_name
        doc.metadata['portfolio_uri'] = portfolio_uri
        doc.metadata['facility_uri'] = facility_uri
        doc.metadata['document_uri'] = doc_uri
        doc.metadata['document_url'] = doc_url
    except Exception as e:
      self.update_extraction_status(doc_uri, "failed")
      raise e

    try:
      ids = self.vector_store.add_documents(docs)

      # Update the document node in the knowledge graph to have the ids from the vector store
      with self.kg.create_session() as session:
        query = "MATCH (d:Document {uri: $uri}) SET d.vectorStoreIds = $ids RETURN d"
        result = session.run(query, uri=doc_uri, ids=ids)
        data = result.data()
        if len(data) == 0: raise ValueError("Document not updated")
    except Exception as e:
      self.update_extraction_status(doc_uri, "failed")
      raise e
    
    return self.update_extraction_status(doc_uri, "success")
  
  def delete(self, uri):
    """
    Delete a document from the facility. This will remove the document from the blob store, the vector store, and the knowledge graph.
    """
    try:
      with self.kg.create_session() as session:
        query = "MATCH (d:Document {uri: $uri}) WITH d, d.url as url, d.vectorStoreIds as vectorStoreIds DETACH DELETE d RETURN url, vectorStoreIds"
        result = session.run(query, uri=uri)
        data = result.data()
        if len(data) == 0:
          raise ValueError(f"Document with uri {uri} not found")
      url = data[0]['url']
      self.blob_store.delete_file(url)
      if 'vectorStoreIds' in data[0]:
        self.vector_store.delete(ids=data[0]['vectorStoreIds'])
    except Exception as e:
      raise e
    
  def search(self, params: DocumentQuery) -> List[DocumentMetadataChunk]:
    """
    Search vector store for documents in the facility
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