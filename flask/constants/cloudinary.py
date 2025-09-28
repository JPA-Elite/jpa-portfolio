from enum import Enum

class CloudinaryFolders(Enum):
    DEFAULT = "uploads"
    MUSIC = "portfolio_music"
    VIDEO = "portfolio_videos"
    PROJECT = "portfolio_projects"
    PDF = "portfolio_pdf"

class CloudinaryResourceType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "video" #audio files are uploaded as video type in Cloudinary
    RAW = "raw"
