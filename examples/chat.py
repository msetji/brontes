#!/usr/bin/env python

from openoperator.infrastructure import AzureBlobStore, KnowledgeGraph 
from openoperator.domain.repository import DocumentRepository
from openoperator.domain.service import AIAssistantService
import argparse
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
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

  llm_system_prompt = """You are an an AI Assistant that specializes in building operations and maintenance.
  Your goal is to help facility owners, managers, and operators manage their facilities and buildings more efficiently.
  Make sure to always follow ASHRAE guildelines.
  Don't be too wordy. Don't be too short. Be just right.
  Don't make up information. If you don't know, say you don't know.
  Always respond with markdown formatted text."""

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

  # Services
  ai_assistant_service = AIAssistantService(document_repository=document_repository)

  messages = [
    SystemMessage(content=llm_system_prompt)
  ]

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