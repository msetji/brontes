from typing import List, Generator
import os
import ast
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
# from langchain_groq import ChatGroq
from langchain_community.chat_models.perplexity import ChatPerplexity
# from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from concurrent.futures import ThreadPoolExecutor, as_completed

from brontes.domain.repository import DocumentRepository, PortfolioRepository, AIRepository, FacilityRepository
from brontes.domain.model import DocumentQuery, User

class AIAssistantService:
  def __init__(self, document_repository: DocumentRepository, portfolio_repository: PortfolioRepository, facility_repository: FacilityRepository, ai_repository: AIRepository):
    self.document_repository = document_repository
    self.portfolio_repository = portfolio_repository
    self.vector_store = document_repository.vector_store
    self.ai_repository = ai_repository
    self.facility_repository = facility_repository

  def get_user_chat_session_history(self, user: User) -> List[str]:
    """Get all chat sessions for the given user."""
    return self.ai_repository.get_chat_sessions(user.email)
  
  async def chat(self, session_id: str, user: User, input: str, portfolio_uri: str, facility_uri: str | None = None, document_uri: str | None = None, verbose: bool = False) -> Generator[str, None, None]:
    def process_query(query):
      query =  DocumentQuery(query=query, portfolio_uri=portfolio_uri, facility_uri=facility_uri, document_uri=document_uri, limit=4)
      return self.document_repository.search(query)

    def execute_queries_concurrently(query_list):
      results = []
      # Using ThreadPoolExecutor to run queries in parallel
      with ThreadPoolExecutor(max_workers=len(query_list)) as executor:
          # Creating a future object for each query
          future_to_query = {executor.submit(process_query, query): query for query in query_list}
          
          # Collecting results as they complete
          for future in as_completed(future_to_query):
              try:
                  result = future.result()
                  results.extend(result)
              except Exception as exc:
                  print(f'Query {future_to_query[future]} generated an exception: {exc}')
      return results
              
    # user_context = user.full_name
    # portfolio_context = str(self.portfolio_repository.get_portfolio(portfolio_uri=portfolio_uri).model_dump())

    # if facility_uri:
    #   # self.prompt.messages[0] += "\n\nCurrent Facility Context: {facility_context}"
    #   facility = self.facility_repository.get_facility(facility_uri=facility_uri)
    #   facility_name = facility.name
    #   # facility_context = str(facility.model_dump())

    # Initialize chat history manager
    chat_history = self.ai_repository.chat_history_client(user_email=user.email, session_id=session_id)

    # small_llama_chat = ChatGroq(temperature=0, groq_api_key=os.environ["GROQ_API_KEY"], model_name="llama3-8b-8192")
    # big_llama_chat = ChatGroq(temperature=0, groq_api_key=os.environ["GROQ_API_KEY"], model_name="llama3-70b-8192")
    # gpt_chat = ChatOpenAI(temperature=0, model="gpt-4-turbo")
    # pplx_sonar_chat = ChatPerplexity(temperature=0, model="sonar-medium-chat", pplx_api_key=os.environ["PPLX_API_KEY"])
    pplx_llama_8b = ChatPerplexity(temperature=0, model="llama-3-8b-instruct", pplx_api_key=os.environ["PPLX_API_KEY"])
    pplx_llama_70 = ChatPerplexity(temperature=0, model="llama-3-70b-instruct", pplx_api_key=os.environ["PPLX_API_KEY"])

    # search_for_info_prompt = ChatPromptTemplate.from_messages([
    #   ("system", """Given a chat history between an ai and a user, analyze the question and determine if the ai should search for information in the building's documents. If the ai should search for information then return yes otherwise return no. Only Response with yes or no"""),
    #   ("human", "Chat History: {chat_history}\n\nAnalyze this message history and determine if the AI should search for information in the building's documents.")
    # ])
    # chain = search_for_info_prompt | pplx_llama_70 
    # response = chain.invoke({
    #   "chat_history": str([message.json() for message in chat_history.messages] + [HumanMessage(input).json()])
    # })
    # search_for_info = response.content
    # print("Search for info?")
    # print(search_for_info)

  # if search_for_info == "yes":
    generate_queries_prompt = ChatPromptTemplate.from_messages([
      ("human", """Analyze the question and come up with 4 search queries to find information from a buildings documents. Only return the four query strings in an array and nothing else. Here is an example:
Question: what are the locations of all my air handling units
      
Queries: ['air handling units', 'ahu', 'ahu spaces', 'where are the air handling units located']

Question: {input}
      
Queries:"""),
    ])

    chain = generate_queries_prompt | pplx_llama_8b

    try:
      response = chain.invoke({
        "input": input
      })
      queries = response.content
      queries = ast.literal_eval(queries.strip())
      print("Queries:")
      print(queries)
    except Exception as e:
      raise Exception("Failed to generate queries for the given input. Please try again.")

    document_context = ""

    combined_results = execute_queries_concurrently(queries)

    # print("Sources:")
    # print(combined_results[:2])

    chunk_index = 1
    for document_metadata_chunk in combined_results:
      document_context += f"## Document Metadata Chunk Index: {chunk_index}\n"
      document_context += f"**Document Url**: {document_metadata_chunk.metadata['document_url']}\n"
      if "page_number" in document_metadata_chunk.metadata:
        document_context += f"**Page Number**: {document_metadata_chunk.metadata['page_number']}\n"
      document_context += f"**Document Chunk Content**: {document_metadata_chunk.content}\n\n## End of Document Chunk\n\n"

      chunk_index += 1

    # print("Document Context:")
    # print(document_context)

    prompt = ChatPromptTemplate.from_messages([
("system", """When generating text, ALWAYS provide inline citations using markdown format. Use the following format for each citation: [Document Chunk Index](URL of the document). You don't need to say which chunk you got the information from, just answer the question and provide the citations. If you don't know the answer, clearly indicate so instead of making assumptions or providing incorrect information.

## Example Response:
The chillers in the building are located in the basement.[1](https://syyclops.com/example/doc.pdf)
 
## Answer Quality:
Please keep answers concise and to the point. Aim for short paragraphs of 2-3 sentences each. Ensure answers are accurate and reliable."""),
      MessagesPlaceholder("chat_history"),
      ("human", "Use this context to answer the question.\n\n{document_context}\n\nQuestion: {input}")
    ])

    chain = prompt | pplx_llama_70
    ai_response = ""
    for chunk in chain.stream(
      {
        # "user_context": user_context,
        # "portfolio_context": portfolio_context,
        # "facility_context": facility_context if facility_uri else None,
        "input": input,
        "chat_history": chat_history.messages,
        # "facility_name": facility_name,
        "document_context": document_context
      }
    ):
      ai_response += chunk.content
      yield chunk.content
    chat_history.add_messages([
      HumanMessage(input),
      AIMessage(ai_response)
    ])
    return