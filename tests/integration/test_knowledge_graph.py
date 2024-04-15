from openoperator.infrastructure.knowledge_graph import KnowledgeGraph
import pytest

@pytest.fixture(scope="session")
def neo4j_config(neo4j_container):
  return {
    "neo4j_user": "neo4j",
    "neo4j_password": "neo4j-password",
    "neo4j_uri": f"bolt://{neo4j_container.get_container_host_ip()}:7687"
  }

def test_graph_setup(neo4j_container, neo4j_config):
  kg = KnowledgeGraph(**neo4j_config)

  with kg.create_session() as session:
    constraints = session.run("SHOW CONSTRAINTS").data()
    assert any("n10s_unique_uri" in constraint['name'] for constraint in constraints)

    # Make sure the neosemantics plugin is setup
    graph_config = session.run("MATCH (n:`_GraphConfig`) RETURN n").data()
    assert len(graph_config) == 1
    assert graph_config[0]['n'] is not None

def test_create_session(neo4j_container, neo4j_config):
  kg = KnowledgeGraph(**neo4j_config)

  with kg.create_session() as session:
    assert session is not None
