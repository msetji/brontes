from brontes.infrastructure.repos import PortfolioRepository
from brontes.domain.models import Portfolio
from brontes.utils import create_uri

class PortfolioService:
  def __init__(self, portfolio_repository: PortfolioRepository, base_uri: str = "https://syyclops.com/"):
    self.portfolio_repository = portfolio_repository
    self.base_uri = base_uri

  def get_portfolio(self, portfolio_uri: str) -> Portfolio:
    return self.portfolio_repository.get_portfolio(portfolio_uri)
  
  def create_portfolio(self, name: str, user_email: str) -> Portfolio:
    portfolio_uri = f"{self.base_uri}/{create_uri(name)}"
    portfolio = Portfolio(uri=portfolio_uri, name=name, email=user_email)
    return self.portfolio_repository.create_portfolio(portfolio)
  
  def list(self, email: str) -> list[Portfolio]:
    return self.portfolio_repository.list(email)