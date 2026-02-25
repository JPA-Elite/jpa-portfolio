import math
from flask import redirect, url_for, render_template, request
from backend.Services.PortfolioService import PortfolioService
from backend.Services.VisitService import VisitService
from backend.Repositories.PortfolioRepository import PortfolioRepository
from backend.Repositories.VisitRepository import VisitRepository
from backend.Services.VideoService import VideoService
from backend.Repositories.VideoRepository import VideoRepository
from backend.Services.GalleryService import GalleryService
from backend.Repositories.GalleryRepository import GalleryRepository
from backend.Services.KeyProjectService import KeyProjectService
from backend.Repositories.KeyProjectRepository import KeyProjectRepository
from backend.Services.GalleryLikeService import GalleryLikeService
from backend.Repositories.GalleryLikeRepository import GalleryLikeRepository
from backend.utils import capture_image, get_random_tags
from backend.configurations import (
    ADD_PORTFOLIO_PAGE,
    CONCERN_PAGE,
    ERROR_404_PAGE,
    GALLERY_PAGE,
    IMAGE_PATH,
    MODES,
    PROFILE_IMAGE,
    PROFILE_IMAGE_GIF,
    INTRO_PAGE,
    PROFILE_PAGE,
    RESUME_PDF,
    VLOG_PAGE,
    MUSIC_PAGE,
    DEVICE_INFO_VISIT_PAGE,
    DONATION_PAGE,
    SortOrder,
    get_locale,
)
from flask_babel import gettext  # type: ignore
from markupsafe import escape  # type: ignore
import requests

# Initialize Services
portfolio_service = PortfolioService(repository=PortfolioRepository())
visit_service = VisitService(repository=VisitRepository())
gallery_service = GalleryService(repository=GalleryRepository())
video_service = VideoService(repository=VideoRepository())
key_project_service = KeyProjectService(repository=KeyProjectRepository())
gallery_like_service = GalleryLikeService(repository=GalleryLikeRepository())

# ************************** PAGES ********************************

_KEY_PROJECT_LOCALES = ("en", "ceb", "fil_PH", "fr")

_KEY_PROJECT_SEED_I18N = {
    "kp-jaom-connect": {
        "title": {
            "en": "JAOM-CONNECT",
            "ceb": "JAOM-CONNECT",
            "fil_PH": "JAOM-CONNECT",
            "fr": "JAOM-CONNECT",
        },
        "description": {
            "en": "Community platform project with Angular and Laravel featuring user flows, content pages, and admin-ready backend integrations.",
            "ceb": "Proyekto sa community platform gamit ang Angular ug Laravel nga adunay user flows, content pages, ug backend integrations nga andam para sa admin.",
            "fil_PH": "Proyekto ng community platform gamit ang Angular at Laravel na may user flows, content pages, at backend integrations na handa para sa admin.",
            "fr": "Community platform project with Angular and Laravel featuring user flows, content pages, and admin-ready backend integrations.",
        },
        "stack": {
            "en": "Angular • Laravel",
            "ceb": "Angular • Laravel",
            "fil_PH": "Angular • Laravel",
            "fr": "Angular • Laravel",
        },
    },
    "kp-ai-voice": {
        "title": {
            "en": "AI Voice Recognition",
            "ceb": "AI Voice Recognition",
            "fil_PH": "AI Voice Recognition",
            "fr": "AI Voice Recognition",
        },
        "description": {
            "en": "Experimental Python project focused on speech recognition workflows and audio-processing exploration.",
            "ceb": "Eksperimental nga Python project nga naka-focus sa speech recognition workflows ug pag-eksplorar sa audio processing.",
            "fil_PH": "Eksperimental na Python project na nakatuon sa speech recognition workflows at pag-explore ng audio processing.",
            "fr": "Experimental Python project focused on speech recognition workflows and audio-processing exploration.",
        },
        "stack": {
            "en": "Python",
            "ceb": "Python",
            "fil_PH": "Python",
            "fr": "Python",
        },
    },
    "kp-billing-gpay": {
        "title": {
            "en": "BillingSolution-G-Pay",
            "ceb": "BillingSolution-G-Pay",
            "fil_PH": "BillingSolution-G-Pay",
            "fr": "BillingSolution-G-Pay",
        },
        "description": {
            "en": "Laravel-based billing workflow prototype for payment-oriented business operations and tracking.",
            "ceb": "Laravel-based billing workflow prototype para sa payment-oriented nga operasyon sa negosyo ug tracking.",
            "fil_PH": "Laravel-based billing workflow prototype para sa payment-oriented na operasyon ng negosyo at tracking.",
            "fr": "Laravel-based billing workflow prototype for payment-oriented business operations and tracking.",
        },
        "stack": {
            "en": "Laravel",
            "ceb": "Laravel",
            "fil_PH": "Laravel",
            "fr": "Laravel",
        },
    },
    "kp-tourist-booking": {
        "title": {
            "en": "TouristSpot Booking System",
            "ceb": "TouristSpot Booking System",
            "fil_PH": "TouristSpot Booking System",
            "fr": "TouristSpot Booking System",
        },
        "description": {
            "en": "Booking management system concept for tourism reservations, schedules, and customer interactions.",
            "ceb": "Konsepto sa booking management system para sa tourism reservations, schedules, ug customer interactions.",
            "fil_PH": "Konsepto ng booking management system para sa tourism reservations, schedules, at customer interactions.",
            "fr": "Booking management system concept for tourism reservations, schedules, and customer interactions.",
        },
        "stack": {
            "en": "Laravel",
            "ceb": "Laravel",
            "fil_PH": "Laravel",
            "fr": "Laravel",
        },
    },
    "kp-tech-booking": {
        "title": {
            "en": "Technician Booking System",
            "ceb": "Technician Booking System",
            "fil_PH": "Technician Booking System",
            "fr": "Technician Booking System",
        },
        "description": {
            "en": "Service booking flow prototype connecting customers with technicians through structured scheduling.",
            "ceb": "Prototype sa service booking flow nga nagkonektar sa customers ug technicians pinaagi sa organisadong scheduling.",
            "fil_PH": "Prototype ng service booking flow na nag-uugnay sa customers at technicians sa pamamagitan ng maayos na scheduling.",
            "fr": "Service booking flow prototype connecting customers with technicians through structured scheduling.",
        },
        "stack": {
            "en": "Angular • Laravel",
            "ceb": "Angular • Laravel",
            "fil_PH": "Angular • Laravel",
            "fr": "Angular • Laravel",
        },
    },
    "kp-socio-fanline": {
        "title": {
            "en": "Socio-Fanline",
            "ceb": "Socio-Fanline",
            "fil_PH": "Socio-Fanline",
            "fr": "Socio-Fanline",
        },
        "description": {
            "en": "Frontend-focused concept project exploring social-style UI layouts and presentation design.",
            "ceb": "Frontend-focused nga konsepto nga proyekto nga nag-eksplorar sa social-style UI layouts ug presentation design.",
            "fil_PH": "Frontend-focused na concept project na nag-eexplore ng social-style UI layouts at presentation design.",
            "fr": "Frontend-focused concept project exploring social-style UI layouts and presentation design.",
        },
        "stack": {
            "en": "HTML • CSS",
            "ceb": "HTML • CSS",
            "fil_PH": "HTML • CSS",
            "fr": "HTML • CSS",
        },
    },
}


def _locale_key(locale_value):
    locale_str = str(locale_value or "en")
    if locale_str.startswith("fil"):
        return "fil_PH"
    if locale_str.startswith("ceb"):
        return "ceb"
    if locale_str.startswith("fr"):
        return "fr"
    return "en"


def _normalized_project_text_map(value):
    if isinstance(value, dict):
        return {
            locale: str(value.get(locale, "") or "").strip()
            for locale in _KEY_PROJECT_LOCALES
        }

    if isinstance(value, str):
        text = value.strip()
        if text:
            return {
                "en": text,
                "ceb": "",
                "fil_PH": "",
                "fr": "",
            }

    return {locale: "" for locale in _KEY_PROJECT_LOCALES}


def _merge_seed_localized_map(value, seed_map=None):
    base = _normalized_project_text_map(value)
    if not seed_map:
        return base

    seed_map = {
        locale: str(seed_map.get(locale, "") or "").strip()
        for locale in _KEY_PROJECT_LOCALES
    }
    english_value = (base.get("en") or "").strip()
    merged = dict(base)

    for locale in _KEY_PROJECT_LOCALES:
        current = (merged.get(locale) or "").strip()
        seed_value = (seed_map.get(locale) or "").strip()

        if not current and seed_value:
            merged[locale] = seed_value
            continue

        # Seeded records stored English text in all locale slots.
        if (
            locale != "en"
            and seed_value
            and english_value
            and current == english_value
        ):
            merged[locale] = seed_value

    if not merged.get("en") and seed_map.get("en"):
        merged["en"] = seed_map["en"]

    return merged


def _localized_value_from_map(value_map, locale_value, default_value=""):
    locale = _locale_key(locale_value)
    return (
        (value_map.get(locale) or "").strip()
        or (value_map.get("en") or "").strip()
        or default_value
    )


def _resolve_project_stack_display(stack_value, locale_value, seed_stack_map=None):
    locale = _locale_key(locale_value)

    if isinstance(stack_value, dict):
        stack_map = _merge_seed_localized_map(stack_value, seed_stack_map)
        return _localized_value_from_map(stack_map, locale, "")

    stack_text = str(stack_value or "").strip()
    if seed_stack_map:
        seed_stack_map = {
            key: str(seed_stack_map.get(key, "") or "").strip()
            for key in _KEY_PROJECT_LOCALES
        }
        english_seed = seed_stack_map.get("en", "")
        if not stack_text or stack_text == english_seed:
            return (
                seed_stack_map.get(locale)
                or seed_stack_map.get("en")
                or stack_text
            )

    return stack_text


def index_route():
    return handle_log_parameter() or render_template(INTRO_PAGE)

def profile_route():
    profile_name = gettext("profile_name")
    profile_intro = gettext("profile_intro")
    profile_age = gettext("profile_age")
    profile_introvert = gettext("profile_introvert")
    profile_job = gettext("profile_job")
    profile_goals = gettext("profile_goals")
    profile_desc = f"{escape(profile_intro)} {escape(profile_age)}<br>{escape(profile_introvert)}<br>{escape(profile_job)} {escape(profile_goals)}"

    voice_icon = url_for("static", filename="images/voice.png", _external=True)

    try:
        key_project_service.seed_default_projects_if_empty()
    except Exception as exc:
        # Keep the profile page resilient if Cloudinary/network is unavailable during first seed.
        print(f"Key project default seed failed: {exc}")

    locale = _locale_key(get_locale())
    key_projects = [project.to_dict() for project in key_project_service.get_active_key_projects()]
    key_project_columns = {
        "shipped": [],
        "building": [],
        "planned": [],
    }

    for project in key_projects:
        seed_i18n = _KEY_PROJECT_SEED_I18N.get(str(project.get("id") or "").strip())
        title_map = _merge_seed_localized_map(
            project.get("title"),
            (seed_i18n or {}).get("title"),
        )
        description_map = _merge_seed_localized_map(
            project.get("description"),
            (seed_i18n or {}).get("description"),
        )
        modal_slides = []

        cover_url = project.get("image_url")
        if cover_url:
            modal_slides.append({
                "src": cover_url,
                "titles": title_map or {"en": "Project Preview"},
                "descriptions": description_map or {"en": ""},
            })

        for slide in project.get("slides", []) or []:
            slide = slide or {}
            slide_title = slide.get("title") or {}
            slide_description = slide.get("description") or {}
            slide_url = slide.get("image_url")
            if not slide_url:
                continue
            modal_slides.append({
                "src": slide_url,
                "titles": slide_title or title_map or {"en": "Project Slide"},
                "descriptions": slide_description or description_map or {"en": ""},
            })

        display_project = {
            **project,
            "display_title": _localized_value_from_map(
                title_map, locale, "Untitled Project"
            ),
            "display_description": _localized_value_from_map(description_map, locale, ""),
            "display_stack": _resolve_project_stack_display(
                project.get("stack", ""),
                locale,
                (seed_i18n or {}).get("stack"),
            ),
            "modal_slides": modal_slides,
        }
        status = display_project.get("status") or "planned"
        if status not in key_project_columns:
            status = "planned"
        key_project_columns[status].append(display_project)

    return handle_log_parameter() or render_template(
        PROFILE_PAGE,
        profile_image=PROFILE_IMAGE,
        profile_image_gif=PROFILE_IMAGE_GIF,
        resume_pdf=RESUME_PDF,
        title="My Portfolio",
        profile_name=profile_name,
        profile_desc=profile_desc,
        key_project_columns=key_project_columns,
        voice_icon=voice_icon,
    )

def gallery_route():
    search_query = request.args.get("search", "")
    tags_query = request.args.get("tags", "")
    items_per_page = 6
    page = request.args.get("page", 1, type=int)

    gallery_list, total = gallery_service.search_gallery_paginated(
        search_query,
        tags_query,
        get_locale(),
        page,
        items_per_page,
        SortOrder.DESC
    )

    # Combine gallery data with like counts
    gallery_data = []
    for gallery in gallery_list:
        gallery_dict = gallery.to_dict()
        gallery_data.append(gallery_dict)

    total_pages = math.ceil(total / items_per_page)
    voice_icon = url_for("static", filename="images/voice.png", _external=True)
    random_tags = get_random_tags(gallery_service.get_all_tags(100), 12)

    return handle_log_parameter() or render_template(
        GALLERY_PAGE,
        image_path=IMAGE_PATH,
        gallery_data=gallery_data,
        current_page=page,
        total_pages=total_pages,
        title="My Gallery",
        search_query=search_query,
        tags_query=tags_query,
        voice_icon=voice_icon,
        random_tags=random_tags,
    )

def vlog_route():
    search_query = request.args.get("search", "")
    tags_query = request.args.get("tags", "")
    page = request.args.get("page", 1, type=int)
    items_per_page = 3

    video_list, total = video_service.search_video_paginated(
        search_query,
        tags_query,
        get_locale(),
        page,
        items_per_page,
        SortOrder.DESC
    )

    vlog_data = [video.to_dict() for video in video_list]
    total_pages = math.ceil(total / items_per_page)
    random_tags = get_random_tags(video_service.get_all_tags(100), 12)

    return handle_log_parameter() or render_template(
        VLOG_PAGE,
        vlogs=vlog_data,
        current_page=page,
        total_pages=total_pages,
        title="My Vlogs",
        search_query=search_query,
        tags_query=tags_query,
        random_tags=random_tags,
    )

def music_route():
    return handle_log_parameter() or render_template(MUSIC_PAGE, title="My Fav Music")

def concern_route():
    return handle_log_parameter() or render_template(CONCERN_PAGE, title="My Concern")

def add_portfolio_form_route():
    return handle_log_parameter() or render_template(ADD_PORTFOLIO_PAGE)

def donation_route():
    return handle_log_parameter() or render_template(DONATION_PAGE)

def device_info_route():
    page = int(request.args.get("page", 1))
    per_page = 10
    documents, total_docs = visit_service.get_paginated_system_info(page, per_page)
    total_pages = (total_docs + per_page - 1) // per_page

    return handle_log_parameter() or render_template(
        DEVICE_INFO_VISIT_PAGE,
        documents=[doc.to_dict() for doc in documents],
        current_page=page,
        total_pages=total_pages,
        title="User Visits",
    )

# ************************** PRIVATE FUNCTIONS ********************************
def handle_log_parameter():
    if request.args.get('mode') and request.args.get('mode') not in MODES:
        return render_template(ERROR_404_PAGE, title="Not Found"), 404

    log_query = request.args.get("log", "").lower()
    if log_query == "true":
        cloudinary_url, error = capture_image()
        print(cloudinary_url)
        print(error)

        result = portfolio_service.add_system_info(cloudinary_url=cloudinary_url)
        print(result)
        return redirect(url_for(request.endpoint))

    return None

def is_philippines():
    # Use ipinfo.io for IP geolocation, allow localhost/private IPs
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        # Allow local development and private IPs
        if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10.") or ip == "localhost":
            return True
        geo_url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(geo_url, timeout=2)
        data = response.json()
        country_code = data.get("country", "").upper()
        print(f"Country code: {country_code} | IP: {ip}")
        return country_code == "PH"
    except Exception as e:
        print(f"GeoIP error: {e}")
        # Default to allow if cannot determine
        return True
