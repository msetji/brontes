import unittest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from openoperator.infrastructure.knowledge_graph import KnowledgeGraph
import time

class TestKnowledgeGraph(unittest.TestCase):
  @classmethod
  def setUpClass(self):
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
    self.neo4j_container = neo4j_container

    username = "neo4j"
    password = "neo4j-password"
    url = f"bolt://{neo4j_container.get_container_host_ip()}:7687"

    self.kg = KnowledgeGraph(neo4j_uri=url, neo4j_user=username, neo4j_password=password)

  @classmethod
  def tearDownClass(self):
    self.neo4j_container.stop()

  def test_graph_setup(self):
    """Test if the graph is setup with the correct constraints"""
    with self.kg.create_session() as session:
      constraints = session.run("SHOW CONSTRAINTS").data()
      assert any("n10s_unique_uri" in constraint['name'] for constraint in constraints)

      # Make sure the neosemantics plugin is setup
      graph_config = session.run("MATCH (n:`_GraphConfig`) RETURN n").data()
      self.assertTrue(len(graph_config) == 1)
      self.assertTrue(graph_config[0]['n'] is not None)

  def test_create_session(self):
    with self.kg.create_session() as session:
      self.assertIsNotNone(session)
  
if __name__ == '__main__':
    unittest.main()