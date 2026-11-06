from app.Repositories.Interfaces.IPortfolioRepository import IPortfolioRepository
from app.Models.SystemInfo import SystemInfo
from flask import request
from user_agents import parse
import platform
from datetime import datetime
import pytz
import requests
from app.constants.messages import SYSTEM_INFO_ADD_MSG, VISIT_ALREADY_RECORDED_MSG
from app.domains import SITE_ADMIN, SITE_PROFESSIONAL, SITE_SOCIAL, page_site

class PortfolioService:
    def __init__(self, repository: IPortfolioRepository):
        self.repository = repository

    def get_client_ip(self):
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        return ip.split(",")[0]

    def get_ip_location(self, ip):
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=2.5)
            data = response.json()

            return {
                "ip": ip,
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"),
                "country": data.get("country", "Unknown"),
                "location": data.get("loc", "Unknown"),
            }
        except Exception:
            return {"ip": ip, "city": "Unknown", "region": "Unknown", "country": "Unknown", "location": "Unknown"}

    def record_visit(self, page, user_ip=None, user_agent_string=None, site=None):
        try:
            if user_ip is None:
                user_ip = self.get_client_ip()

            tz = pytz.timezone("Asia/Manila")
            current_time = datetime.now(tz)
            visit_date = current_time.strftime("%Y-%m-%d")

            if self.repository.find_visit_for_day(user_ip, page, visit_date):
                return {"message": VISIT_ALREADY_RECORDED_MSG, "status": "skipped"}

            if user_agent_string is None:
                user_agent_string = request.headers.get("User-Agent")
            user_agent = parse(user_agent_string)
            location_info = self.get_ip_location(user_ip)

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
                page=page,
                site=site if site in (SITE_PROFESSIONAL, SITE_SOCIAL, SITE_ADMIN) else page_site(page),
                timestamp=current_time.strftime("%m/%d/%Y - %I:%M %p"),
                occurred_at=current_time.isoformat(),
                visit_date=visit_date,
                ip_address=location_info["ip"],
                city=location_info["city"],
                region=location_info["region"],
                country=location_info["country"],
                location=location_info["location"],
            )

            result = self.repository.insert_system_info(system_info.to_dict())
            return {
                "message": SYSTEM_INFO_ADD_MSG,
                "status": "success",
                "id": str(result.inserted_id),
            }

        except Exception as e:
            return {"message": str(e), "status": "error"}
