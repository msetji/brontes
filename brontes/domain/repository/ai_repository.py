from brontes.infrastructure import Postgres, KnowledgeGraph
from langchain_postgres import PostgresChatMessageHistory

class AIRepository:
  """This class is responsible for managing any AI related data storage and retrieval."""
  def __init__(self, postgres: Postgres, kg: KnowledgeGraph):
    self.postgres = postgres
    self.kg = kg

    # Create the table schema (only needs to be done once)
    self.chat_history_table_name = "chat_history"
    PostgresChatMessageHistory.create_tables(postgres.conn, self.chat_history_table_name)

  def chat_history_client(self, user_email: str, session_id: str):
    """Get the chat history client for the given session ID. If the session ID does not exist, a new chat history client will be created."""
    with self.kg.create_session() as session:
      data = session.run("MATCH (u:User {email: $email}) MERGE (chat_session:ChatSession {id: $session_id}) MERGE (u)-[:hasChatSession]->(chat_session) RETURN u, chat_session", email=user_email, session_id=session_id).data()
      if not data:
        raise ValueError("Error storing user session ID")
    return PostgresChatMessageHistory(
        self.chat_history_table_name,
        session_id,
        sync_connection=self.postgres.conn
    )
  
  def get_chat_sessions(self, user_email: str):
    """Get all chat sessions for the given user."""
    with self.kg.create_session() as session:
      result = session.run("MATCH (u:User {email: $email})-[:hasChatSession]->(chat_session:ChatSession) RETURN chat_session", email=user_email).data()
      chat_sessions = []
      for record in result:
        chat_session = {
          "session_id": record['chat_session']['id'],
          "messages": []
        }
        chat_messages = PostgresChatMessageHistory(
          self.chat_history_table_name,
          record['chat_session']['id'],
          sync_connection=self.postgres.conn
        ).messages
        chat_session["messages"] = [message.dict() for message in chat_messages]
        chat_sessions.append(chat_session)
      return chat_sessions