from enum import Enum

class CloudinaryFolders(Enum):
    DEFAULT = "uploads"
    MUSIC = "portfolio_music"
    VIDEO = "portfolio_videos"
    PROJECT = "portfolio_projects"
    ROADMAP = "portfolio_company_roadmap"
    PDF = "portfolio_pdf"
    GALLERY = "portfolio_gallery"
    AVATAR = "portfolio_avatars"

class CloudinaryResourceType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "video"
    RAW = "raw"
