
def test_graph_setup(knowledge_graph):

  with knowledge_graph.create_session() as session:
    constraints = session.run("SHOW CONSTRAINTS").data()
    assert any("n10s_unique_uri" in constraint['name'] for constraint in constraints)

    # Make sure the neosemantics plugin is setup
    graph_config = session.run("MATCH (n:`_GraphConfig`) RETURN n").data()
    assert len(graph_config) == 1
    assert graph_config[0]['n'] is not None

def test_create_session(knowledge_graph):
  with knowledge_graph.create_session() as session:
    assert session is not None
