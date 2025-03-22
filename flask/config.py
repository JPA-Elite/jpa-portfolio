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
CONCERN_PAGE = "pages/concern.html"
ADD_PORTFOLIO_PAGE = "pages/add_portfolio.html"
DONATION_PAGE = "pages/donation.html"
DEVICE_INFO_VISIT_PAGE = "pages/visitors.html"
ERROR_404_PAGE = "error/404.html"

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