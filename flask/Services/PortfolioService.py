from Repositories.PortfolioRepository import PortfolioRepository
from Models.Portfolio import Portfolio
from Models.SystemInfo import SystemInfo
from flask import request, url_for
from user_agents import parse  # type: ignore
import platform
from datetime import datetime
import pytz  # type: ignore


class PortfolioService:
    def __init__(self):
        self.repository = PortfolioRepository()

    def add_system_info(self):
        """Capture and store system information in the database."""
        try:
            # Get user agent from the request headers
            user_agent_string = request.headers.get("User-Agent")
            user_agent = parse(user_agent_string)

            # Get current date and time in Philippines timezone
            tz = pytz.timezone("Asia/Manila")
            current_time = datetime.now(tz)
            formatted_time = current_time.strftime(
                "%m/%d/%Y - %I:%M %p"
            )  # e.g., '09/16/2024 - 5:21 PM'

            # Get system information
            system_info = SystemInfo(
                system=platform.system(),
                node=platform.node(),
                release=platform.release(),
                version=platform.version(),
                platform=platform.platform(),
                architecture=platform.architecture(),
                user_agent= user_agent_string,
                device=user_agent.device.family,  # e.g., 'iPhone', 'Android'
                brand=user_agent.device.brand,  # e.g., 'Apple', 'Samsung'
                model=getattr(
                    user_agent.device, "model", "Unknown Model"
                ),  # Safe access to model
                browser=user_agent.browser.family,  # e.g., 'Mobile Safari'
                browser_version=user_agent.browser.version_string,  # e.g., '5.1'
                os=user_agent.os.family,  # e.g., 'iOS'
                os_version=user_agent.os.version_string,  # e.g., '5.1'
                page=url_for(request.endpoint),
                timestamp=formatted_time,  # Add formatted timestamp
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
