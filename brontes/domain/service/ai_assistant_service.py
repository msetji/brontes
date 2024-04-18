from brontes.domain.repository import DocumentRepository, PortfolioRepository
from brontes.domain.model import DocumentQuery, Portfolio
from typing import List, Generator
import copy
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent, Tool
from langchain_community.utilities.serpapi import SerpAPIWrapper

class AIAssistantService:
  def __init__(self, document_repository: DocumentRepository, portfolio_repository: PortfolioRepository):
    self.document_repository = document_repository
    self.portfolio_repository = portfolio_repository
    self.vector_store = document_repository.vector_store

    self.prompt = ChatPromptTemplate.from_messages([
      ("system", """You are now a digital twin. Depending on the context given you may represent a portfolio, facility, system or equipment. As a digital twin your responses should reflect the context. Users should feel like they are speaking directly to their building or portfolio.
Digital twins are able to analyze all of the information about themselves and provide insights and recommendations to their owners, operators, and managers.
Don't call yourself a digital twin, instead embody the role and provide the best possible answers to the user's questions. Talk about yourself and answer questions in the first person, as if you were the building or portfolio.
Your answer should be as short and concise as possible while still being informative.
You are an ASHRAE expert and always try to follow the ASHRAE guidelines.
You use tools when necessary to help you answer the question, and always provide your sources in markdown formatting.
       
Portfolio context: {portfolio_context}"""),
      MessagesPlaceholder("chat_history"),
      ("human", "{input}"),
      MessagesPlaceholder("agent_scratchpad")
    ])
  
  async def chat(self, portfolio_uri: str, messages: List[BaseMessage], facility_uri: str | None = None, document_uri: str | None = None, verbose: bool = False) -> Generator[str, None, None]:
    messages = copy.deepcopy(messages) # Copy the messages so we don't modify the original

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

    portfolio_context = str(self.portfolio_repository.get_portfolio(portfolio_uri=portfolio_uri).model_dump())

    tools = [search_building_information, search_tool]
    llm = ChatOpenAI(model="gpt-4", temperature=0, streaming=True)
    agent = create_openai_tools_agent(llm, tools, self.prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=verbose).with_config(
      {"run_name": "Agent"}
    )

    input_message = messages.pop(-1)
    input = input_message.content

    async for event in agent_executor.astream_events({
      "input": input,
      "chat_history": messages,
      "portfolio_context": portfolio_context,
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
            # if verbose:
            #   print()
            #   print("--")
            #   print(
            #       f"Done agent: {event['name']} with output: {event['data'].get('output')['output']}"
            #   )
            return
      if kind == "on_chat_model_stream":
        content = event["data"]["chunk"].content
        if content:
          yield content
            # Empty content in the context of OpenAI means
            # that the model is asking for a tool to be invoked.
            # So we only print non-empty content
            # print(content, end="|")
      elif kind == "on_tool_start":
        pass
        # if verbose:
        #   print("--")
        #   print(
        #       f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}"
        #   )
      elif kind == "on_tool_end":
        pass
        # if verbose:
        #   print(f"Done tool: {event['name']}")
        #   print(f"Tool output was: {event['data'].get('output')}")
        #   print("--")