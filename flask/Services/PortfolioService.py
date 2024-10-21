from Repositories.PortfolioRepository import PortfolioRepository
from Models.Portfolio import Portfolio
from Models.SystemInfo import SystemInfo
from flask import request, url_for
from user_agents import parse # type: ignore
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
            # Get user agent from the request headers
            user_agent = request.headers.get('User-Agent')
            user_agent_info = parse(user_agent)

            # Identify the system type
            if user_agent_info.is_mobile:
                system_type = 'Mobile'
                model = user_agent_info.model  # Get mobile model (e.g., 'Vivo', 'Tecno')
            else:
                system_type = platform.system()  # e.g., 'Windows', 'Linux', 'Darwin'
                model = 'N/A'  # No model for desktop devices
                
            # Get system information
            system_info = SystemInfo(
                system=system_type,
                node=platform.node(),
                release=platform.release(),
                version=platform.version(),
                platform=platform.platform(),
                architecture=platform.architecture(),
                model=model,
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
