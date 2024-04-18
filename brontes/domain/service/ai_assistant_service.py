from brontes.domain.repository import DocumentRepository, PortfolioRepository, AIRepository, FacilityRepository
from brontes.domain.model import DocumentQuery, User
from typing import List, Generator
import hashlib
from langchain_openai import ChatOpenAI
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent, Tool
from langchain_community.utilities.serpapi import SerpAPIWrapper
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, ToolMessage

class AIAssistantService:
  def __init__(self, document_repository: DocumentRepository, portfolio_repository: PortfolioRepository, facility_repository: FacilityRepository, ai_repository: AIRepository):
    self.document_repository = document_repository
    self.portfolio_repository = portfolio_repository
    self.vector_store = document_repository.vector_store
    self.ai_repository = ai_repository
    self.facility_repository = facility_repository

    self.prompt = ChatPromptTemplate.from_messages([
      ("system", """You are now a digital twin. Depending on the context given you may represent a portfolio, facility, system or equipment. As a digital twin your responses should reflect the context. Users should feel like they are speaking directly to their building or portfolio. Don't call yourself a digital twin, instead embody the role and provide the best possible answers to the user's questions. Talk about yourself and answer questions in the first person, as if you were the building or portfolio.
Digital twins are able to analyze all of the information about themselves and provide insights and recommendations to their owners, operators, and managers.
Your answer should be as short and concise as possible while still being informative.
You are an ASHRAE expert and always try to follow the ASHRAE guidelines.
You use tools when necessary to help you answer the question
       
Always provide in text references to the information you are providing with markdown links. For example, [ASHRAE 90.1](https://www.ashrae.org/technical-resources/standards-and-guidelines/ashrae-standards). Especially when using tools, make sure to provide the source of the information.
       
User context (The user you are speaking to): {user_context}
Portfolio context: {portfolio_context}"""),
      MessagesPlaceholder("chat_history"),
      ("human", "{input}"),
      MessagesPlaceholder("agent_scratchpad")
    ])

  def get_user_chat_session_history(self, user: User) -> List[str]:
    """Get all chat sessions for the given user."""
    return self.ai_repository.get_chat_sessions(user.email)
  
  async def chat(self, session_id: str, user: User, input: str, portfolio_uri: str, facility_uri: str | None = None, document_uri: str | None = None, verbose: bool = False) -> Generator[str, None, None]:
    # Initialize the chat history manager
    chat_history = self.ai_repository.chat_history_client(user_email=user.email, session_id=session_id)

    @tool
    def search_building_information(query: str):
      """This tool is useful when you need to lookup information specific to the portfolio or building the user is referring to. It returns more context that will help you answer their question. Provide a query that will be used to search for the information."""
      document_query = DocumentQuery(query=query, portfolio_uri=portfolio_uri, facility_uri=facility_uri, document_uri=document_uri)
      return str(self.document_repository.search(document_query))
    
    search = SerpAPIWrapper()
    search_tool = Tool(
      name="google_search",
      description="useful for when you need to get information from the web",
      func=search.run
    )

    user_context = user.full_name
    portfolio_context = str(self.portfolio_repository.get_portfolio(portfolio_uri=portfolio_uri).model_dump())

    if facility_uri:
      self.prompt.messages[0] += "\n\nCurrent Facility Context: {facility_context}"
      facility_context = str(self.facility_repository.get_facility(facility_uri=facility_uri).model_dump())

    tools = [search_building_information, search_tool]
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0, streaming=True)
    agent = create_openai_tools_agent(llm, tools, self.prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=verbose).with_config(
      {"run_name": "Agent"}
    )

    # Create a list of messages to store in the chat history
    messages_to_add_to_chat: List[BaseMessage] = [
      HumanMessage(content=input)
    ]

    async for event in agent_executor.astream_events({
      "input": input,
      "chat_history": chat_history.messages,
      "user_context": user_context,
      "portfolio_context": portfolio_context,
      "facility_context": facility_context if facility_uri else None
    }, version="v1"):
      kind = event["event"]
      if kind == "on_chain_start":
        if (
            event["name"] == "Agent"
        ):  # Was assigned when creating the agent with `.with_config({"run_name": "Agent"})`
          pass
            # print(
            #     f"Starting agent: {event['name']} with input: {event['data'].get('input')}"
            # )
      elif kind == "on_chain_end":
        if (
            event["name"] == "Agent"
        ):  # Was assigned when creating the agent with `.with_config({"run_name": "Agent"})`
            output = event["data"].get("output")['output']
            if output:
              messages_to_add_to_chat.append(AIMessage(content=output))
      if kind == "on_chat_model_stream":
        content = event["data"]["chunk"].content
        if content:
          yield content
      elif kind == "on_tool_start":
        tool_name = event["name"]
        tool_input = event["data"]
        tool_id = event["run_id"]
        tool_id = hashlib.sha256(tool_id.encode()).hexdigest()[:10]
        messages_to_add_to_chat.append(
          AIMessage(content="", tool_calls=[
            {"name": tool_name, "args": tool_input, "id": tool_id}
          ])
        )

      elif kind == "on_tool_end":
        tool_name = event["name"]
        tool_output = event["data"].get("output")
        tool_id = event["run_id"]
        tool_id = hashlib.sha256(tool_id.encode()).hexdigest()[:10]
        messages_to_add_to_chat.append(
          ToolMessage(content=tool_output, tool_call_id=tool_id)
        )

    # Add the messages to the chat history
    chat_history.add_messages(messages_to_add_to_chat)