from brontes.domain.repository import PortfolioRepository
from brontes.domain.model import Portfolio
import pytest

def test_create_portfolio(knowledge_graph):
  # Arrange
  portfolio_repository = PortfolioRepository(kg=knowledge_graph)
  user_email = "example@example.com"
  portfolio = Portfolio(name="Test Portfolio", uri="https://syyclops.com/test%20portfolio")
  # Act
  created_portfolio = portfolio_repository.create_portfolio(portfolio=portfolio, user_email=user_email)
  # Assert
  assert created_portfolio.uri == "https://syyclops.com/test%20portfolio"
  assert created_portfolio.name == "Test Portfolio"

def test_create_portfolio_no_user(knowledge_graph):
  # Arrange
  portfolio_repository = PortfolioRepository(kg=knowledge_graph)
  user_email = "not_a_user_email@email.com"
  portfolio = Portfolio(name="Test Portfolio", uri="https://syyclops.com/test%20portfolio")
  # Act
  with pytest.raises(Exception) as context:
    portfolio_repository.create_portfolio(portfolio=portfolio, user_email=user_email)
  # Assert
  assert "Error creating portfolio" in str(context)

def test_list_portfolios_for_user(knowledge_graph):
  # Arrange
  portfolio_repository = PortfolioRepository(kg=knowledge_graph)
  user_email = "example@example.com"
  # Act
  portfolios = portfolio_repository.list_portfolios_for_user(email=user_email)
  # Assert
  assert len(portfolios) == 1 # Created in apoc.conf
  assert portfolios[0].name == "Example Portfolio"

  facilities = portfolios[0].facilities
  assert len(facilities) == 1
  assert facilities[0].name == "Example Facility"

def test_portfolios_bad_user(knowledge_graph):
  # Arrange
  portfolio_repository = PortfolioRepository(kg=knowledge_graph)
  user_email = "bad_user@example.com"
  # Act
  portfolios = portfolio_repository.list_portfolios_for_user(email=user_email)
  # Assert
  assert len(portfolios) == 0