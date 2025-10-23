from flask import request
from enum import Enum

# ************************** CONSTANTS ********************************

IMAGE_PATH = "/static/images/"
DOCUMENT_PATH = "/static/documents/"
JSON_PATH = "/static/json/"

PROFILE_IMAGE = f"{IMAGE_PATH}1x1_the_eys_will_move_and_also_its_m.png"
PROFILE_IMAGE_GIF = f"{IMAGE_PATH}08a08500-b5ae-41da-9c7c-d99b34a4dc2c_video.gif"
RESUME_PDF = f"{DOCUMENT_PATH}joshua_algadipe.pdf"
CHAT_ICON = f"{IMAGE_PATH}chat.png"
GALLERY_JSON_PATH = f"{JSON_PATH}gallery.json"
VLOG_JSON_PATH =  f"{JSON_PATH}vlog.json"

# pages
INTRO_PAGE = "pages/intro.html"
PROFILE_PAGE = "pages/profile.html"
GALLERY_PAGE = "pages/gallery.html"
VLOG_PAGE = "pages/vlog.html"
MUSIC_PAGE = "pages/music.html"
CONCERN_PAGE = "pages/concern.html"
ADD_PORTFOLIO_PAGE = "pages/add_portfolio.html"
DONATION_PAGE = "pages/donation.html"
DEVICE_INFO_VISIT_PAGE = "pages/visitors.html"
ERROR_404_PAGE = "error/404.html"

# admin pages
ADMIN_LOGIN_PAGE = "admin/login.html"
ADMIN_DASHBOARD_PAGE = "admin/dist/dashboard.html"
ADMIN_MUSIC_PAGE = "admin/dist/music.html"
ADMIN_GALLERY_PAGE = "admin/dist/gallery.html"
ADMIN_VIDEO_PAGE = "admin/dist/video.html"
ADMIN_SETTINGS_PAGE = "admin/dist/settings.html"

LANGUAGES = {
    "en": "English",
    "ceb": "Cebuano",
    "fr": "French",
    "fil_PH": "Tagalog",
}

BABEL_DEFAULT_LOCALE = "en"
EN_LOCALE = "en"
CEB_LOCALE = "ceb"
FR_LOCALE = "fr"
TL_LOCALE = "fil_PH"

# mode options
MODE_PROFESSIONAL = "professional"
MODE_CASUAL = "casual"
MODES = [MODE_PROFESSIONAL, MODE_CASUAL]

# ************************** FUNCTIONS ********************************


def get_locale():
    lang = request.cookies.get("lang") or request.accept_languages.best_match(
        LANGUAGES.keys()
    )
    return lang


# ************************** ENUMS ********************************

class SortOrder(Enum):
    ASC = 1
    DESC = -1

class SortOrderStr(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

class HTTPMethod(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'