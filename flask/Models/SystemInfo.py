class SystemInfo:
    def __init__(
        self,
        system,
        node,
        release,
        version,
        platform,
        architecture,
        user_agent,
        device,
        brand,
        model,
        browser,
        browser_version,
        os,
        os_version,
        page,
        timestamp,
        ip_address=None,
        city=None,
        region=None,
        country=None,
        location=None,
        _id=None,
        image_capture=None
    ):
        self._id = _id
        self.system = system
        self.node = node
        self.release = release
        self.version = version
        self.platform = platform
        self.architecture = architecture
        self.user_agent = user_agent
        self.device = device
        self.brand = brand
        self.model = model
        self.browser = browser
        self.browser_version = browser_version
        self.os = os
        self.os_version = os_version
        self.page = page
        self.timestamp = timestamp
        self.image_capture = image_capture

        # New: Location-related attributes
        self.ip_address = ip_address
        self.city = city
        self.region = region
        self.country = country
        self.location = location

    def to_dict(self):
        """Convert the object to a dictionary for database storage."""
        data = {
            "system": self.system,
            "node": self.node,
            "release": self.release,
            "version": self.version,
            "platform": self.platform,
            "architecture": self.architecture,
            "user_agent": self.user_agent,
            "device": self.device,
            "brand": self.brand,
            "model": self.model,
            "browser": self.browser,
            "browser_version": self.browser_version,
            "os": self.os,
            "os_version": self.os_version,
            "page": self.page,
            "timestamp": self.timestamp,
            "image_capture": self.image_capture,
            "ip_address": self.ip_address,
            "city": self.city,
            "region": self.region,
            "country": self.country,
            "location": self.location
        }

        # Include _id if present
        if self._id is not None:
            data["_id"] = self._id

        return data
