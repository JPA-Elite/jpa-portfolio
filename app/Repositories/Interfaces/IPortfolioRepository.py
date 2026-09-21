from abc import ABC, abstractmethod

class IPortfolioRepository(ABC):
    @abstractmethod
    def insert_portfolio(self, portfolio_data):
        pass

    @abstractmethod
    def insert_system_info(self, system_info):
        pass

    @abstractmethod
    def find_visit_for_day(self, ip_address, page, visit_date):
        pass

