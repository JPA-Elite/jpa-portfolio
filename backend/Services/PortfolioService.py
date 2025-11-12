from Repositories.Interfaces.IPortfolioRepository import IPortfolioRepository
from Models.SystemInfo import SystemInfo
from flask import request, url_for
from user_agents import parse  # type: ignore
import platform
from datetime import datetime
import pytz  # type: ignore
import requests

class PortfolioService:
    def __init__(self, repository: IPortfolioRepository):
        self.repository = repository

    def get_client_ip(self):
        """Get the real client IP address (handling proxies)"""
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        return ip.split(",")[0]  # Extract first IP if behind proxies

    def get_ip_location(self, ip):
        """Fetch location details using an IP Geolocation API"""
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json")
            data = response.json()

            return {
                "ip": ip,
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"),
                "country": data.get("country", "Unknown"),
                "location": data.get("loc", "Unknown"),  # Latitude & Longitude
            }
        except Exception:
            return {"ip": ip, "city": "Unknown", "region": "Unknown", "country": "Unknown", "location": "Unknown"}

    def add_system_info(self, cloudinary_url=None):
        """Capture and store system information in the database."""
        try:
            # Get user agent from request headers
            user_agent_string = request.headers.get("User-Agent")
            user_agent = parse(user_agent_string)

            # Get user's IP address and location
            user_ip = self.get_client_ip()
            location_info = self.get_ip_location(user_ip)

            # Get current date and time in Philippines timezone
            tz = pytz.timezone("Asia/Manila")
            current_time = datetime.now(tz)
            formatted_time = current_time.strftime("%m/%d/%Y - %I:%M %p")

            # Get system information
            system_info = SystemInfo(
                system=platform.system(),
                node=platform.node(),
                release=platform.release(),
                version=platform.version(),
                platform=platform.platform(),
                architecture=platform.architecture(),
                user_agent=user_agent_string,
                device=user_agent.device.family,
                brand=user_agent.device.brand,
                model=getattr(user_agent.device, "model", "Unknown Model"),
                browser=user_agent.browser.family,
                browser_version=user_agent.browser.version_string,
                os=user_agent.os.family,
                os_version=user_agent.os.version_string,
                page=url_for(request.endpoint),
                timestamp=formatted_time,
                image_capture=cloudinary_url,
                ip_address=location_info["ip"],  # Add IP Address
                city=location_info["city"],  # Add City
                region=location_info["region"],  # Add Region
                country=location_info["country"],  # Add Country
                location=location_info["location"],  # Latitude & Longitude
            )

            # Insert system information into the database
            result = self.repository.insert_system_info(system_info.to_dict())
            return {
                "message": "System information added successfully",
                "status": "success",
                "id": str(result.inserted_id),
            }

        except Exception as e:
            # Catch any exceptions and return an error message
            return {"message": str(e), "status": "error"}
