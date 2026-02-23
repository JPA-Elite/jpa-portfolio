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

    locale = get_locale()
    key_projects = [project.to_dict() for project in key_project_service.get_active_key_projects()]
    key_project_columns = {
        "shipped": [],
        "building": [],
        "planned": [],
    }

    for project in key_projects:
        title_map = project.get("title") or {}
        description_map = project.get("description") or {}
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
            "display_title": title_map.get(locale) or title_map.get("en") or "Untitled Project",
            "display_description": description_map.get(locale) or description_map.get("en") or "",
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
