from typing import List, Optional
from dataclasses import asdict

from brontes.infrastructure import KnowledgeGraph
from brontes.domain.models import Portfolio, Facility

class PortfolioRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg

  def get_portfolio(self, portfolio_uri: str) -> Optional[Portfolio]:
    try:
      with self.kg.create_session() as session:
        result = session.run("MATCH (p:Customer {uri: $uri}) MATCH (p)-[:HAS_FACILITY]->(f:Facility) with p, collect(f) as facilities RETURN p as portfolio, facilities", uri=portfolio_uri)
        data = result.single()
        if data is None:
          raise Exception(f"Portfolio {portfolio_uri} not found")
        portfolio = Portfolio(uri=data['portfolio']['uri'], name=data['portfolio']['name'])
        facilities = [Facility(**facility) for facility in data['facilities']]
        portfolio.facilities = facilities
        return portfolio
    except Exception as e:
      raise e
    
  def create_portfolio(self, portfolio: Portfolio, user_email: str) -> Optional[Portfolio]:
    try:
      with self.kg.create_session() as session:
        query = "MATCH (u:User {email: $email}) CREATE (p:Customer:Resource $portfolio) CREATE (u)-[:HAS_ACCESS_TO]->(p) RETURN p"
        result = session.run(query=query, name=portfolio.name, uri=portfolio.uri, email=user_email, portfolio=asdict(portfolio))
        record = result.single()
        if record is None:
          raise Exception(f"Error creating portfolio {portfolio.uri}")
        return Portfolio(uri=record['p']['uri'], name=record['p']['name'])
    except Exception as e:
      raise e
    
  def list(self, email: str) -> List[Portfolio]:
    """List the portfolios a user has access to."""
    try:
      with self.kg.create_session() as session:
        result = session.run("""MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]->(p:Customer) 
                                MATCH (p)-[:HAS_FACILITY]->(f:Facility)
                                WITH p, f
                                ORDER BY p.name, f.name
                                WITH p, COLLECT(f) AS facilities
                                RETURN p AS portfolio, facilities""", email=email)
        data = result.data()
        portfolios: List[Portfolio] = []
        for record in data:
          portfolio = Portfolio(uri=record['portfolio']['uri'], name=record['portfolio']['name'])
          facilities = [
            Facility(uri=facility['uri'], name=facility['name'], latitude=facility.get('latitude'), longitude=facility.get('longitude'), address=facility.get('address')) 
            for facility in record['facilities']
          ]
          portfolio.facilities = facilities
          portfolios.append(portfolio)
        return portfolios
    except Exception as e:
      raise e
