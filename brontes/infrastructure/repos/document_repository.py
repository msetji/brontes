from typing import List, Optional
from dataclasses import asdict
import logging

from brontes.domain.models import Document
from brontes.infrastructure import KnowledgeGraph 

class DocumentRepository:
  """
  This repository is responsible for managing documents in the knowledge graph.
  A Document is a file that is associated with a facility, space, type, or component.
  """
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg

  def list(self, facility_uri: str, space_uri: Optional[str] = None, type_uri: Optional[str] = None, component_uri: Optional[str] = None) -> Optional[List[Document]]:
    """
    Fetch all the documents for a facility.
    """
    try:
      with self.kg.create_session() as session:
        query = "MATCH (d:Document)-[:documentTo]-(f:Facility {uri: $facility_uri})"
        if space_uri is not None:
          query += " MATCH (d)-[:documentTo]-(s:Space {uri: $space_uri}) "
        if type_uri is not None:
          query += " MATCH (d)-[:documentTo]-(t:Type {uri: $type_uri}) "
        if component_uri is not None:
          query += " MATCH (d)-[:documentTo]-(c:Component {uri: $component_uri}) "
        query += " return distinct d"

        data = session.run(query=query, facility_uri=facility_uri, space_uri = space_uri, type_uri = type_uri, component_uri = component_uri).data()
        return [
          Document(
            uri=record['d'].get('uri'), 
            name=record['d'].get('name'), 
            url=record['d'].get('url'), 
            extractionStatus=record['d'].get('extractionStatus'),
            thumbnailUrl=record['d'].get('thumbnailUrl'),
            discipline=record['d'].get('discipline'),
            vectorStoreIds=record['d'].get('vectorStoreIds'),
            fileType=record['d'].get('fileType')
          ) 
          for record in data
        ]
    except Exception as e:
      logging.exception(f"Failed to list documents for facility {facility_uri}: {e}")
      return None
  
  def upload(self, facility_uri: str, document: Document, space_uri: Optional[str], type_uri: Optional[str], component_uri: Optional[str]):
    """
    Upload a file for a facility.

    1. Upload the file to the blob store
    2. Create a document node in the knowledge graph with extractionStatus = "pending" and url details
    """
    try:
      with self.kg.create_session() as session:
        # Create the cypher query
        query = "CREATE (d:Document:Resource $document) "
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

        # Create the document dict, get the discpline enum value
        document_dict = asdict(document)
        document_dict['discipline'] = document.discipline.value

        # Run the query
        result = session.run(query, document=document_dict, facility_uri=facility_uri, space_uri = space_uri, type_uri = type_uri, component_uri = component_uri)
        
        data = result.data()
        if len(data) == 0: raise ValueError("Document not created")
    except Exception as e:
      raise e
    
  def update(self, document: Document) -> Document:
    """
    Update a documents properties in the knowledge graph.
    """
    try:
      with self.kg.create_session() as session:
        query = "MATCH (d:Document {uri: $uri}) SET d = $doc RETURN d"
        document_dict = asdict(document)
        document_dict['discipline'] = document.discipline.value
        result = session.run(query, uri=document.uri, doc=document_dict)
        return Document(
          uri=result.data()[0]['d']['uri'],
          name=result.data()[0]['d']['name'],
          url=result.data()[0]['d']['url'],
          extractionStatus=result.data()[0].get('extractionStatus'),
          thumbnailUrl=result.data()[0].get('thumbnailUrl'),
          discipline=result.data()[0].get('discipline'),
          vectorStoreIds=result.data()[0].get('vectorStoreIds'),
          fileType=result.data()[0].get('fileType')
        )
    except Exception as e:
      raise e
    
  def get(self, uri: str) -> Document:
    """
    Fetch a document from the knowledge graph
    """
    try:
      with self.kg.create_session() as session:
        query = "MATCH (d:Document {uri: $uri}) RETURN d"
        result = session.run(query, uri=uri)
        data = result.data()
        if len(data) == 0:
          raise Exception(f"Document with uri {uri} not found")
        return Document(
          uri=data[0]['d']['uri'],
          name=data[0]['d']['name'],
          url=data[0]['d']['url'],
          extractionStatus=data[0].get('extractionStatus'),
          thumbnailUrl=data[0].get('thumbnailUrl'),
          discipline=data[0].get('discipline'),
          vectorStoreIds=data[0].get('vectorStoreIds'),
          fileType=data[0].get('fileType')
        )
    except Exception as e:
      raise e
  
  def delete(self, document: Document):
    """
    Delete a document from the knowledge graph
    """
    try:
      with self.kg.create_session() as session:
        query = "MATCH (d:Document {uri: $uri}) WITH d, d.url as url, d.vectorStoreIds as vectorStoreIds DETACH DELETE d RETURN url, vectorStoreIds"
        result = session.run(query, uri=document.uri).data()
        if len(result) == 0:
          raise Exception(f"Document with uri {document.uri} not found")
    except Exception as e:
      raise e