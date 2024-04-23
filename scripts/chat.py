#!/usr/bin/env python

# To run with different env file: POETRY_DOTENV_LOCATION=.env.beta poetry run scripts/chat.py 

from brontes.infrastructure import AzureBlobStore, KnowledgeGraph, Postgres
from brontes.domain.repository import DocumentRepository, PortfolioRepository, AIRepository, FacilityRepository
from brontes.domain.service import AIAssistantService
from brontes.domain.model import User
import argparse
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
import asyncio
import os
import uuid

async def main():
  # Create the argument parser
  parser = argparse.ArgumentParser()
  parser.add_argument('--portfolio_uri', type=str, help='The portfolio ID to use for the chat', default="https://syyclops.com/example")
  parser.add_argument('--facility_uri', type=str, help='The email of the user to chat with', default="https://syyclops.com/example/example")
  parser.add_argument('--email', type=str, help='The email of the user to chat with', default="example@example.com")
  parser.add_argument('--verbose', type=bool, default=False, help='Print verbose output') 
  args = parser.parse_args()
  verbose = args.verbose
  portfolio_uri = args.portfolio_uri
  email = args.email
  facility_uri = args.facility_uri

  user = User(email=email, full_name="", hashed_password="")

  # Infrastructure
  postgres = Postgres()
  knowledge_graph = KnowledgeGraph()
  blob_store = AzureBlobStore()
  embeddings = OpenAIEmbeddings()
  vector_store = PGVector(
    collection_name=os.environ.get("POSTGRES_EMBEDDINGS_TABLE"),
    connection=os.environ.get("POSTGRES_CONNECTION_STRING"),
    embeddings=embeddings,
    use_jsonb=True
  )

  # Repositories
  document_repository = DocumentRepository(kg=knowledge_graph, blob_store=blob_store, vector_store=vector_store)
  portfolio_repository = PortfolioRepository(kg=knowledge_graph)
  ai_repository = AIRepository(postgres=postgres, kg=knowledge_graph)
  facility_repository = FacilityRepository(kg=knowledge_graph)
  
  # Services
  ai_assistant_service = AIAssistantService(document_repository=document_repository, portfolio_repository=portfolio_repository, ai_repository=ai_repository, facility_repository=facility_repository)

  session_id = str(uuid.uuid4())
  print(f"Session ID: {session_id}")

  while True:
    # Get input from user
    user_input = input("Enter input: ")

    # If the user enters "exit" then exit the program
    if user_input == "exit":
      break

    async for chunk in ai_assistant_service.chat(user=user, session_id=session_id, input=user_input, portfolio_uri=portfolio_uri, verbose=verbose, facility_uri=facility_uri):
      event = chunk["event"]
      data = chunk["data"]

      if event == "tool_call":
        if verbose:
          print("Tool:")
          print(data["tool_name"])

      if event == "message":
        chunk = data["chunk"]
        print(chunk, end="", flush=True)

    print()


if __name__ == "__main__":
  asyncio.run(main())