import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import time

from brontes.infrastructure.db.knowledge_graph import KnowledgeGraph 
from brontes.infrastructure.db.timescale import Timescale
from brontes.infrastructure.db.postgres import Postgres

@pytest.fixture(scope="session")
def neo4j_container():
  neo4j_container = (
      DockerContainer(image="neo4j_with_plugins")
      .with_exposed_ports(7687)
      .with_bind_ports(7687, 7687)
  )
  neo4j_container.start()
  try:
      wait_for_logs(neo4j_container, "Started", timeout=30)
      time.sleep(2) # Apoc conf runs
  except Exception as e:
      print("Neo4J Logs:", neo4j_container.get_logs())
      raise e
  yield neo4j_container
  neo4j_container.stop()

@pytest.fixture(scope="session")
def postgres_container():
  postgres_container = DockerContainer("pg").with_exposed_ports(5432).with_bind_ports(5432, 5432)
  postgres_container.start()
  try:
      wait_for_logs(postgres_container, "listening on IPv6 address", timeout=30)
  except Exception as e:
      print(postgres_container.get_logs())
      raise e
  yield postgres_container
  postgres_container.stop()

@pytest.fixture(scope="session")
def knowledge_graph(neo4j_container):
  config = {
    "neo4j_user": "neo4j",
    "neo4j_password": "neo4j-password",
    "neo4j_uri": f"bolt://{neo4j_container.get_container_host_ip()}:7687"
  }
  return KnowledgeGraph(**config)

@pytest.fixture(scope="session")
def timescale(postgres_container):
  conn_string = f'postgresql://postgres:postgres@{postgres_container.get_container_host_ip()}:5432/postgres'
  postgres = Postgres(connection_string=conn_string)
  return Timescale(postgres)