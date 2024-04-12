import unittest
from testcontainers.neo4j import Neo4jContainer
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from openoperator.infrastructure.knowledge_graph import KnowledgeGraph

class TestKnowledgeGraph(unittest.TestCase):
  def setUp(self):
    username = "neo4j"
    password = "neo4j-password"
    url = "bolt://localhost:7687"
    self.neo4j_container = (
        DockerContainer(image="neo4j_with_plugins")
        .with_exposed_ports(7687)
        .with_bind_ports(7687, 7687)
      )
    self.neo4j_container.start()

    wait_for_logs(self.neo4j_container, "Started")

    self.knowledge_graph = KnowledgeGraph(neo4j_uri=url, neo4j_user=username, neo4j_password=password)

  def tearDown(self):
    self.neo4j_container.stop()

  # @wait_container_is_ready
  # def ensure_container_is_ready(self):
  #     return self.neo4j_container.get_connection_url()

  def test_create_session(self):
    with self.knowledge_graph.neo4j_driver.session() as session:
      assert session is not None
      session.close()


if __name__ == '__main__':
    unittest.main()