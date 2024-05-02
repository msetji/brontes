from typing import List, Generator
import json
import logging
from dataclasses import asdict
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, ToolCall
from langchain_core.tools import tool
from langchain_community.utilities.serpapi import SerpAPIWrapper

from brontes.infrastructure.repos import PortfolioRepository, AIRepository, FacilityRepository
from brontes.application.services import DocumentService
from brontes.domain.models import User
from brontes.application.dtos.document_dto import DocumentQuery

class AIAssistantService:
  """
  This application service provides the functionality to interact with the AI assistant.

  It coordinates the interaction between the AI model and the user as well as the AI model and the tools it can use.
  """
  def __init__(self, document_service: DocumentService, portfolio_repository: PortfolioRepository, facility_repository: FacilityRepository, ai_repository: AIRepository):
    self.document_service = document_service
    self.portfolio_repository = portfolio_repository
    self.ai_repository = ai_repository
    self.facility_repository = facility_repository

  def get_user_chat_session_history(self, user: User) -> List[str]:
    """Get all chat sessions for the given user."""
    return self.ai_repository.get_chat_sessions(user.email)
  
  async def chat(self, session_id: str, user: User, input: str, portfolio_uri: str, facility_uri: str | None = None, document_uri: str | None = None, verbose: bool = False) -> Generator[str, None, None]:
    # Initialize chat history manager
    chat_history = self.ai_repository.chat_history_client(user_email=user.email, session_id=session_id)

    # Define the tools that the AI assistant can use
    @tool
    def search_building_documents(query):
      """Perform a search for information from building documents. These documents may be O&M manuals, as-builts, cut sheets, etc. If you use information from this tool, please provide in line citations using markdown format. Format like this: [Document Chunk Index](URL of the document). For example, [1](https://syyclops.com/example/doc.pdf)."""
      query =  DocumentQuery(query=query, portfolio_uri=portfolio_uri, facility_uri=facility_uri, document_uri=document_uri, limit=20)
      return self.document_service.search(query)
    
    @tool
    def web_search(query):
      """Use google search to find information from the web."""
      search = SerpAPIWrapper()
      return search.run(query)
    
    tools = [search_building_documents, web_search]

    # TODO: Provide more context to the AI model
    # Get the context to be used in the chat
    # portfolio_context = str(self.portfolio_repository.get_portfolio(portfolio_uri=portfolio_uri).model_dump())

    # if facility_uri:
    #   # self.prompt.messages[0] += "\n\nCurrent Facility Context: {facility_context}"
    #   facility = self.facility_repository.get_facility(facility_uri=facility_uri)
    #   facility_name = facility.name
      # facility_context = str(facility.model_dump())

    # Define the AI model and prompt template
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # Define the chat template
    chat_template = ChatPromptTemplate.from_messages([
      ("system", """This is a conversation between you and {user_name}. You are an AI Assistant for a digital twin applicaiton to help facility owners, managers, and operators run their facilities efficently. Provide in line citations using markdown format if you are sourcing information from somewhere. Keep your answers as short and sweeet as possible."""),
      MessagesPlaceholder("chat_history")
    ])
    # Format the chat messages
    chat_history.add_message(HumanMessage(input)) # Add the user input to the chat history
    
    while True:
      gathered_chunks = None
      first = True

      # Fill out the chat template with the chat history
      messages = chat_template.format_messages(
        user_name=user.email,
        chat_history=chat_history.messages
      )

      ai_response = ""
      async for chunk in llm_with_tools.astream(messages):
        if "tool_calls" in chunk.additional_kwargs:
          if first:
            gathered_chunks = chunk
            first = False
          else: 
            gathered_chunks = gathered_chunks + chunk

        else:
          ai_response += chunk.content
          yield {"event": "message", "data": {"chunk": chunk.content}}

      # Check if there are any tool calls
      # If there is then run them and return them back to the model to keep the conversation going
      # If not then end the conversation
      if gathered_chunks is not None:
        tool_calls: List[ToolCall] = [ToolCall(name=tool_call['function']['name'], args=json.loads(tool_call['function']['arguments']), id=tool_call['id']) for tool_call in gathered_chunks.additional_kwargs["tool_calls"]]
        
        # Update the chat message history to show ai selected some tools to use
        chat_history.add_message(AIMessage(content="", tool_calls=tool_calls))

        for tool_call in tool_calls:
          tool_name = tool_call["name"]
          tool_args = tool_call["args"]
          tool_id = tool_call["id"]

          # if verbose:
          logging.info(f"Selected tool: {tool_name}")
          logging.info(f"Tool Args: {tool_args}")

          if tool_name == "search_building_documents":
            try:
              query = tool_args["query"]
              document_results = search_building_documents(query)

              logging.info(f"The search results are: {document_results[:3]}")

              # Create the context string to be used in the chat history
              document_context = ""
              chunk_index = 1
              for document_metadata_chunk in document_results:
                document_context += f"## Document Metadata Chunk Index: {chunk_index}\n"
                document_context += f"**Document Url**: {document_metadata_chunk.metadata['document_url']}\n"
                if "page_number" in document_metadata_chunk.metadata:
                  document_context += f"**Page Number**: {document_metadata_chunk.metadata['page_number']}\n"
                document_context += f"**Document Chunk Content**: {document_metadata_chunk.content}\n\n## End of Document Chunk\n\n"
                chunk_index += 1

              # Yield the tool call event and add to the chat history
              yield {"event": "source", "data": [asdict(result) for result in document_results]}
              chat_history.add_message(ToolMessage(content=document_context, tool_call_id=tool_id))
            except Exception as e:
              chat_history.add_message(ToolMessage(content=f"An error occurred while trying to search the building documents: {e}", tool_call_id=tool_id))
          elif tool_name == "web_search":
            try:
              search_results = web_search(tool_args["query"])
              logging.info(str(search_results))
              logging.info(len(search_results))
              yield {"event": "web_search_results", "data": search_results}

              chat_history.add_message(ToolMessage(content=str(search_results), tool_call_id=tool_id))
            except Exception as e:
              chat_history.add_message(ToolMessage(content=f"An error occurred while trying to search the web: {e}", tool_call_id=tool_id))
      else: 
        # Add final ai response to chat history and return
        chat_history.add_message(AIMessage(ai_response))
        return