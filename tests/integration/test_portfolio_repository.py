import pytest
from brontes.infrastructure.repos import PortfolioRepository
from brontes.domain.models import Portfolio

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
  with pytest.raises(Exception) as e:
    portfolio_repository.create_portfolio(portfolio=portfolio, user_email=user_email)
  # Assert
  assert str(e.value) == "Error creating portfolio https://syyclops.com/test%20portfolio"
  
def test_list_portfolios_for_user(knowledge_graph):
  # Arrange
  portfolio_repository = PortfolioRepository(kg=knowledge_graph)
  user_email = "example@example.com"
  # Act
  portfolios = portfolio_repository.list(email=user_email)
  # Assert
  assert len(portfolios) == 1

def test_portfolios_bad_user(knowledge_graph):
  # Arrange
  portfolio_repository = PortfolioRepository(kg=knowledge_graph)
  user_email = "bad_user@example.com"
  # Act
  portfolios = portfolio_repository.list(email=user_email)
  # Assert
  assert len(portfolios) == 0
