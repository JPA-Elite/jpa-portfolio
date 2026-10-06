import math
import time
from flask import redirect, url_for, render_template, request
from app.Services.VideoService import VideoService
from app.Repositories.VideoRepository import VideoRepository
from app.Services.GalleryService import GalleryService
from app.Repositories.GalleryRepository import GalleryRepository
from app.Services.KeyProjectService import KeyProjectService
from app.Repositories.KeyProjectRepository import KeyProjectRepository
from app.Services.BuiltAppService import BuiltAppService
from app.Repositories.BuiltAppRepository import BuiltAppRepository
from app.Services.CompanyRoadmapService import CompanyRoadmapService
from app.Repositories.CompanyRoadmapRepository import CompanyRoadmapRepository
from app.Services.GalleryLikeService import GalleryLikeService
from app.Repositories.GalleryLikeRepository import GalleryLikeRepository
from app.Requests.web.PageRequest import PageRequest
from app.utils import get_random_tags
from app.configurations import (
    ADD_PORTFOLIO_PAGE,
    APP_DETAILS_PAGE,
    CONCERN_PAGE,
    ERROR_404_PAGE,
    GALLERY_PAGE,
    IMAGE_PATH,
    PROFILE_IMAGE,
    PROFILE_IMAGE_GIF,
    INTRO_PAGE,
    PROFILE_PAGE,
    RESUME_PDF,
    VLOG_PAGE,
    MUSIC_PAGE,
    DONATION_PAGE,
    BOOKING_PAGE,
    SortOrder,
    get_locale,
)
from flask_babel import gettext
from markupsafe import escape
import requests

# Initialize Services
gallery_service = GalleryService(repository=GalleryRepository())
video_service = VideoService(repository=VideoRepository())
key_project_service = KeyProjectService(repository=KeyProjectRepository())
built_app_service = BuiltAppService(repository=BuiltAppRepository())
company_roadmap_service = CompanyRoadmapService(repository=CompanyRoadmapRepository())
gallery_like_service = GalleryLikeService(repository=GalleryLikeRepository())

# ************************** PAGES ********************************

from app.constants.portfolio_locales import KEY_PROJECT_LOCALES as _KEY_PROJECT_LOCALES
from app.data.seeds.key_project_seeds import KEY_PROJECT_SEED_I18N as _KEY_PROJECT_SEED_I18N
from app.data.seeds.career_roadmap_seeds import CAREER_ROADMAP_SEED_I18N as _CAREER_ROADMAP_SEED_I18N


from app.utils_i18n import locale_key as _locale_key
from app.utils_i18n import normalized_text_map as _normalized_project_text_map
from app.utils_i18n import merge_seed_localized_map as _merge_seed_localized_map
from app.utils_i18n import localized_value_from_map as _localized_value_from_map
from app.utils_i18n import normalized_list_map as _normalized_localized_list_map
from app.utils_i18n import merge_seed_localized_list_map as _merge_seed_localized_list_map
from app.utils_i18n import localized_list_from_map as _localized_list_from_map


from app.Services.PortfolioDisplayService import localized_roadmap_employment_type as _employment_type_source
from app.Services.PortfolioDisplayService import resolve_project_stack_display as _resolve_project_stack_display
from app.Services.PortfolioDisplayService import resolve_built_app_display as _built_app_display_source


def _localized_roadmap_employment_type(value):
    return _employment_type_source(value, gettext_fn=gettext)


def _resolve_built_app_display(app_dict):
    return _built_app_display_source(app_dict, locale_value=get_locale())


_seed_check_at: dict = {}


def _should_seed(key, ttl_seconds=300):
    now = time.monotonic()
    last = _seed_check_at.get(key, 0.0)
    if now - last < ttl_seconds:
        return False
    _seed_check_at[key] = now
    return True


def index_route():
    return redirect(url_for("pages.profile"))

def profile_route():
    profile_name = gettext("profile_name")
    profile_intro = gettext("profile_intro")
    profile_age = gettext("profile_age")
    profile_introvert = gettext("profile_introvert")
    profile_job = gettext("profile_job")
    if profile_job.strip() in ("", "profile_job"):
        profile_job = ""
    profile_goals = gettext("profile_goals")
    if profile_goals.strip() in ("", "profile_goals"):
        profile_goals = ""
    profile_desc = "<br>".join(
        part for part in [
            f"{escape(profile_intro)} {escape(profile_age)}".strip(),
            f"{escape(profile_introvert)}".strip(),
            f"{escape(profile_job)} {escape(profile_goals)}".strip(),
        ]
        if part
    )

    voice_icon = url_for("static", filename="images/voice.webp", _external=True)

    if _should_seed("key_projects"):
        try:
            key_project_service.seed_default_projects_if_empty()
        except Exception as exc:
            print(f"Key project default seed failed: {exc}")

    if _should_seed("company_roadmaps"):
        try:
            company_roadmap_service.seed_default_company_roadmaps_if_empty()
        except Exception as exc:
            print(f"Company roadmap default seed failed: {exc}")

    if _should_seed("built_apps"):
        try:
            built_app_service.seed_default_built_apps_if_empty()
        except Exception as exc:
            print(f"Built app default seed failed: {exc}")

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

    for _column_key, _projects in key_project_columns.items():
        column_gallery = []
        for _project in _projects:
            _project_slides = list(_project.get("modal_slides") or [])
            _project["_column_gallery_offset"] = len(column_gallery)
            if _project_slides:
                column_gallery.extend(_project_slides)

        for _project in _projects:
            _project_slides = list(_project.get("modal_slides") or [])
            if len(_project_slides) > 1:
                _project["modal_gallery_items"] = _project_slides
                _project["modal_gallery_start_index"] = 0
            elif len(column_gallery) > 1 and _project_slides:
                _project["modal_gallery_items"] = column_gallery
                _project["modal_gallery_start_index"] = int(_project.get("_column_gallery_offset", 0))
            else:
                _project["modal_gallery_items"] = _project_slides
                _project["modal_gallery_start_index"] = 0

    for _projects in key_project_columns.values():
        for _project in _projects:
            _project.pop("_column_gallery_offset", None)

    company_roadmap_entries = []
    for entry in [x.to_dict() for x in company_roadmap_service.get_active_company_roadmaps()]:
        roadmap_seed_i18n = _CAREER_ROADMAP_SEED_I18N.get(str(entry.get("id") or "").strip(), {})
        role_title_map = _merge_seed_localized_map(
            entry.get("role_title_i18n") or entry.get("role_title"),
            roadmap_seed_i18n.get("role_title"),
        )
        definition_map = _merge_seed_localized_map(
            entry.get("definition_i18n") or entry.get("definition"),
            roadmap_seed_i18n.get("definition"),
        )
        summary_map = _merge_seed_localized_map(
            entry.get("summary_i18n") or entry.get("summary"),
            roadmap_seed_i18n.get("summary"),
        )
        highlights_map = _merge_seed_localized_list_map(
            entry.get("highlights_i18n") or entry.get("highlights"),
            roadmap_seed_i18n.get("highlights"),
        )

        activities = []
        for activity_index, activity in enumerate(entry.get("activities", []) or []):
            activity = activity or {}
            image_url = activity.get("image_url")
            if not image_url:
                continue
            seeded_activities = roadmap_seed_i18n.get("activities") or []
            activity_seed = seeded_activities[activity_index] if activity_index < len(seeded_activities) else {}
            title_map = _merge_seed_localized_map(
                activity.get("title_i18n") or activity.get("title"),
                (activity_seed or {}).get("title"),
            )
            caption_map = _merge_seed_localized_map(
                activity.get("caption_i18n") or activity.get("caption"),
                (activity_seed or {}).get("caption"),
            )
            activities.append({
                "image_url": image_url,
                "title": _localized_value_from_map(title_map, locale, str(activity.get("title") or "").strip()),
                "caption": _localized_value_from_map(caption_map, locale, str(activity.get("caption") or "").strip()),
            })

        if not activities and entry.get("cover_image_url"):
            activities.append({
                "image_url": entry.get("cover_image_url"),
                "title": gettext("Career_Roadmap_Work_Highlight"),
                "caption": "",
            })

        company_roadmap_entries.append({
            **entry,
            "company_name": str(entry.get("company_name") or "").strip(),
            "role_title": _localized_value_from_map(role_title_map, locale, str(entry.get("role_title") or "").strip()),
            "period": str(entry.get("period") or "").strip(),
            "employment_type": _localized_roadmap_employment_type(entry.get("employment_type") or "experience"),
            "location": str(entry.get("location") or "").strip(),
            "definition": _localized_value_from_map(definition_map, locale, str(entry.get("definition") or "").strip()),
            "summary": _localized_value_from_map(summary_map, locale, str(entry.get("summary") or "").strip()),
            "highlights": _localized_list_from_map(highlights_map, locale),
            "cover_image_url": entry.get("cover_image_url"),
            "activities_display": activities[:6],
            "accent_color": str(entry.get("accent_color") or "#2962ff"),
        })

    return render_template(
        PROFILE_PAGE,
        profile_image=PROFILE_IMAGE,
        profile_image_gif=PROFILE_IMAGE_GIF,
        resume_pdf=RESUME_PDF,
        title="My Portfolio",
        profile_name=profile_name,
        profile_desc=profile_desc,
        key_project_columns=key_project_columns,
        company_roadmap_entries=company_roadmap_entries,
        voice_icon=voice_icon,
        built_apps=[_resolve_built_app_display(app.to_dict()) for app in built_app_service.get_active_built_apps()],
    )


def built_app_details_route(slug):
    if _should_seed("built_apps"):
        try:
            built_app_service.seed_default_built_apps_if_empty()
        except Exception as exc:
            print(f"Built app default seed failed: {exc}")

    app = built_app_service.get_active_built_app_by_slug(slug)
    if app is None:
        return render_template(ERROR_404_PAGE, title="Not Found"), 404

    app_data = _resolve_built_app_display(app.to_dict())
    other_apps = [
        _resolve_built_app_display(a.to_dict())
        for a in built_app_service.get_active_built_apps()
        if a.slug != app.slug
    ][:6]

    return render_template(
        APP_DETAILS_PAGE,
        title=f"{app_data['name']} — Built Apps",
        built_app=app_data,
        other_apps=other_apps,
    )

def gallery_route():
    form = PageRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    search_query = data["search_query"]
    tags_query = data["tags_query"]
    items_per_page = 6
    page = data["page"]

    gallery_list, total = gallery_service.search_gallery_paginated(
        search_query,
        tags_query,
        get_locale(),
        page,
        items_per_page,
        SortOrder.DESC
    )

    gallery_data = []
    for gallery in gallery_list:
        gallery_dict = gallery.to_dict()
        gallery_data.append(gallery_dict)

    total_pages = math.ceil(total / items_per_page)
    voice_icon = url_for("static", filename="images/voice.webp", _external=True)
    random_tags = get_random_tags(gallery_service.get_all_tags(100), 12)

    return render_template(
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
    form = PageRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    search_query = data["search_query"]
    tags_query = data["tags_query"]
    items_per_page = 3
    page = data["page"]

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

    return render_template(
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
    return render_template(MUSIC_PAGE, title="My Fav Music")

def concern_route():
    return render_template(CONCERN_PAGE, title="My Concern")

def add_portfolio_form_route():
    return render_template(ADD_PORTFOLIO_PAGE)

def donation_route():
    return render_template(DONATION_PAGE)

def booking_route():
    return render_template(BOOKING_PAGE)

def portfolio_redirect():
    from flask import redirect
    return redirect("/portfolio", code=301)

def is_philippines():

    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)

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

        return True

