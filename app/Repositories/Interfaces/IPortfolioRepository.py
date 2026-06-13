from abc import ABC, abstractmethod

class IPortfolioRepository(ABC):
    @abstractmethod
    def insert_portfolio(self, portfolio_data):
        pass

    @abstractmethod
    def insert_system_info(self, system_info):
        pass

