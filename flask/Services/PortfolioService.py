from Repositories.PortfolioRepository import PortfolioRepository
from Models.Portfolio import Portfolio
from Models.SystemInfo import SystemInfo
from flask import request, url_for
import platform


class PortfolioService:
    def __init__(self):
        self.repository = PortfolioRepository()

    def add_portfolio(self, name: str, email: str):
        portfolio = Portfolio(name, email)
        return self.repository.insert_portfolio(portfolio.to_dict())

    def add_system_info(self):
        """Capture and store system information in the database."""
        try:
            # Get system information
            system_info = SystemInfo(
                system=platform.system(),
                node=platform.node(),
                release=platform.release(),
                version=platform.version(),
                platform=platform.platform(),
                architecture=platform.architecture(),
                page=url_for(request.endpoint),
            )

            # Try to insert system information into the database
            result = self.repository.insert_system_info(system_info.to_dict())
            return {
                "message": "System information added successfully",
                "status": "success",
                "id": str(result.inserted_id),
            }

        except Exception as e:
            # Catch any exceptions and return an error message
            return {"message": str(e), "status": "error"}
