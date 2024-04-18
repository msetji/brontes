#!/usr/bin/env python

from brontes.infrastructure import AzureBlobStore, KnowledgeGraph 
from brontes.domain.repository import DocumentRepository, PortfolioRepository
from brontes.domain.service import AIAssistantService
import argparse
from langchain_core.messages import HumanMessage, AIMessage
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
import asyncio
import os

async def main():
  # Create the argument parser
  parser = argparse.ArgumentParser()
  parser.add_argument('--portfolio_uri', type=str, help='The portfolio ID to use for the chat', default="https://syyclops.com/example")
  parser.add_argument('--verbose', type=bool, default=False, help='Print verbose output') 
  args = parser.parse_args()
  verbose = args.verbose
  portfolio_uri = args.portfolio_uri

  # Infrastructure
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

  # Services
  ai_assistant_service = AIAssistantService(document_repository=document_repository, portfolio_repository=portfolio_repository)

  messages = []

  while True:
    # Get input from user
    user_input = input("Enter input: ")

    # If the user enters "exit" then exit the program
    if user_input == "exit":
      break

    messages.append(HumanMessage(content=user_input))

    content = ""
    async for chunk in ai_assistant_service.chat(portfolio_uri=portfolio_uri, messages=messages, verbose=verbose):
      print(chunk, end="", flush=True)
      content += chunk

    messages.append(AIMessage(content=content))

    print()


if __name__ == "__main__":
  asyncio.run(main())