from abc import ABC, abstractmethod

from backend.Models.Portfolio import Portfolio
from backend.Models.SystemInfo import SystemInfo


class IPortfolioRepository(ABC):
    @abstractmethod
    def insert_portfolio(self, portfolio_data: Portfolio):
        pass

    @abstractmethod
    def insert_system_info(self, system_info: SystemInfo):
        pass
