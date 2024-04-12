import unittest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from openoperator.infrastructure.knowledge_graph import KnowledgeGraph
import time

class TestKnowledgeGraph(unittest.TestCase):
  def setUp(self):
    username = "neo4j"
    password = "neo4j-password"
    url = "bolt://172.17.0.1:7687"
    neo4j_container = (
        DockerContainer(image="neo4j_with_plugins")
        .with_exposed_ports(7687)
        .with_bind_ports(7687, 7687)
      )
    neo4j_container.start()
    time.sleep(30)
    # wait_for_logs(neo4j_container, "Started", timeout=30)
    print("Neo4J Logs:", neo4j_container.get_logs())
    self.neo4j_container = neo4j_container

    self.kg = KnowledgeGraph(neo4j_uri=url, neo4j_user=username, neo4j_password=password)

  def tearDown(self):
    self.neo4j_container.stop()

  def test_create_session(self):
    with self.kg.create_session() as session:
      assert session is not None

if __name__ == '__main__':
    unittest.main()