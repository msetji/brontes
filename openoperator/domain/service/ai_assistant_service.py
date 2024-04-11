from openoperator.domain.repository import DocumentRepository
from openoperator.infrastructure import LLM
from openoperator.domain.model import DocumentQuery
from typing import List, Generator
import copy
import json
from langchain.tools.retriever import create_retriever_tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage, ToolMessage
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain import hub
from langchain_core.utils.function_calling import convert_to_openai_function

class AIAssistantService:
  def __init__(self, document_repository: DocumentRepository):
    self.document_repository = document_repository
    self.vector_store = document_repository.vector_store

  
  async def chat(self, portfolio_uri: str, messages: List[BaseMessage], facility_uri: str | None = None, document_uri: str | None = None, verbose: bool = False):
    messages = copy.deepcopy(messages) # Copy the messages so we don't modify the original

    @tool
    def search_documents(query: str):
      """Search documents for metadata. These documents are drawings/plans, O&M manuals, etc."""
      document_query = DocumentQuery(query=query, portfolio_uri=portfolio_uri, facility_uri=facility_uri, document_uri=document_uri)
      return str(self.document_repository.search(document_query))


    tools = [search_documents]
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, streaming=True)
    llm_with_tools = llm.bind_tools(tools)

    while True:
      first_chunk = True
      gathered_chunks = None

      async for chunk in llm_with_tools.astream(messages):
        # Check if its selecting a tool
        if 'tool_calls' in chunk.additional_kwargs:
          if first_chunk:
            gathered_chunks = chunk
            first_chunk = False
          else:
            gathered_chunks = gathered_chunks + chunk
        else:
          yield chunk

      # Check if the model wants to use tools
      if gathered_chunks is not None:
        
        # Remove index from all chunnks in gathered_chunks
        for chunk in gathered_chunks.additional_kwargs['tool_calls']:
          del chunk['index']
        messages.append(AIMessage(content=gathered_chunks.content, additional_kwargs=gathered_chunks.additional_kwargs))

        for chunk in gathered_chunks.additional_kwargs['tool_calls']:
          tool_name = chunk['function']['name']
          tool_args = chunk['function']['arguments']
          tool_id = chunk['id']
          print(f"Using tool: {tool_name} with args: {tool_args}")

          if tool_name == "search_documents":
            query = json.loads(tool_args)['query']
            result = search_documents(query)
            messages.append(ToolMessage(content=result, tool_call_id=tool_id))
      else:
        return
        
      