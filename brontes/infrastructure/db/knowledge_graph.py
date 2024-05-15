import os
from typing import Optional, Dict
from neo4j import GraphDatabase
from rdflib_neo4j import Neo4jStoreConfig, Neo4jStore, HANDLE_VOCAB_URI_STRATEGY
from rdflib import Graph, Namespace


class KnowledgeGraph():
  prefixes: Dict[str, Namespace] = {
    "cobie": Namespace("http://checksem.u-bourgogne.fr/ontology/cobie24#"),
    "bacnet": Namespace("http://data.ashrae.org/bacnet/#"),
    "brick": Namespace("https://brickschema.org/schema/1.3/Brick#")
  }

  def __init__(
    self,
    neo4j_uri: Optional[str] = None,
    neo4j_user: Optional[str] = None,
    neo4j_password: Optional[str] = None,        
  ) -> None:
    neo4j_uri = neo4j_uri or os.environ['NEO4J_URI']
    neo4j_user = neo4j_user or os.environ['NEO4J_USER']
    neo4j_password = neo4j_password or os.environ['NEO4J_PASSWORD']
    
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password), max_connection_lifetime=200)
    neo4j_driver.verify_connectivity()
    self.neo4j_driver = neo4j_driver

    # Create the necessary constraints
    self.create_constraints()

    # Set up auth data to be used by the graph store
    self.auth_data = {"uri": neo4j_uri,"database": "neo4j","user": neo4j_user,"pwd": neo4j_password}

    # Load the ontologies into the graph
    # self.load_ontologies()

  def create_constraints(self):
    """Initalize the graph with the necessary configuration."""
    # Set up the graph
    with self.neo4j_driver.session() as session:
      session.run("CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS FOR (r:Resource) REQUIRE r.uri IS UNIQUE")
      session.run("CREATE CONSTRAINT email IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")

  def graph_store(self, batching = True):
    """Create a graph store with the necessary configuration."""
    config = Neo4jStoreConfig(
      auth_data=self.auth_data,
      custom_prefixes=self.prefixes,
      handle_vocab_uri_strategy=HANDLE_VOCAB_URI_STRATEGY.IGNORE,
      batching=batching
    )
    neo4j_store = Neo4jStore(config=config)
    return Graph(store=neo4j_store)

  def load_ontologies(self):
    """Load all the ontology data into the knowledge graph."""
    urls = [
      "https://raw.githubusercontent.com/syyclops/open-operator/main/ontology/Brick.ttl",
      "https://raw.githubusercontent.com/syyclops/brontes/main/scripts/master_cobie/master_cobie.ttl"
    ]
    try:
      g = self.graph_store(batching=True)
      for url in urls:
        g.parse(url, format="ttl")
      g.close(commit_pending_transaction=True)
    except Exception as e:
      raise e

  def create_session(self):
    """Creates a session for the neo4j driver."""
    try:
      return self.neo4j_driver.session()
    except Exception as e:
      raise e
  
  def close(self):
    """Closes the neo4j driver connection."""
    self.neo4j_driver.close()

  def __del__(self):
    """Closes the neo4j driver connection when the object is deleted."""
    self.close()
              
  def import_rdf_data(self, url: str, format: str = "ttl", inline: bool = False):
    """Import RDF data into the knowledge graph."""
    try:
      g = self.graph_store(batching=False)
      g.parse(url, format=format)
    except Exception as e:
      raise e