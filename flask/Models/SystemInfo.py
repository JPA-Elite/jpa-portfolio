class SystemInfo:
    def __init__(self, system, node, release, version, platform, architecture, page):
        self.system = system
        self.node = node
        self.release = release
        self.version = version
        self.platform = platform
        self.architecture = architecture
        self.page = page

    def to_dict(self):
        """Convert the SystemInfo instance to a dictionary."""
        return {
            "system": self.system,
            "node": self.node,
            "release": self.release,
            "version": self.version,
            "platform": self.platform,
            "architecture": self.architecture,
            "page": self.page
        }
