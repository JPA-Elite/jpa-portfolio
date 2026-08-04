import math
from flask import redirect, url_for, render_template, request
from app.Services.PortfolioService import PortfolioService
from app.Repositories.PortfolioRepository import PortfolioRepository
from app.Services.VideoService import VideoService
from app.Repositories.VideoRepository import VideoRepository
from app.Services.GalleryService import GalleryService
from app.Repositories.GalleryRepository import GalleryRepository
from app.Services.KeyProjectService import KeyProjectService
from app.Repositories.KeyProjectRepository import KeyProjectRepository
from app.Services.CompanyRoadmapService import CompanyRoadmapService
from app.Repositories.CompanyRoadmapRepository import CompanyRoadmapRepository
from app.Services.GalleryLikeService import GalleryLikeService
from app.Repositories.GalleryLikeRepository import GalleryLikeRepository
from app.Requests.web.PageRequest import PageRequest
from app.utils import capture_image, get_random_tags
from app.configurations import (
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
    DONATION_PAGE,
    BOOKING_PAGE,
    SortOrder,
    get_locale,
)
from flask_babel import gettext
from markupsafe import escape
import requests

# Initialize Services
portfolio_service = PortfolioService(repository=PortfolioRepository())
gallery_service = GalleryService(repository=GalleryRepository())
video_service = VideoService(repository=VideoRepository())
key_project_service = KeyProjectService(repository=KeyProjectRepository())
company_roadmap_service = CompanyRoadmapService(repository=CompanyRoadmapRepository())
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
            "en": "Community platform project with Angular and Laravel featuring user flows, content pages, and admin-ready app integrations.",
            "ceb": "Proyekto sa community platform gamit ang Angular ug Laravel nga adunay user flows, content pages, ug app integrations nga andam para sa admin.",
            "fil_PH": "Proyekto ng community platform gamit ang Angular at Laravel na may user flows, content pages, at app integrations na handa para sa admin.",
            "fr": "Community platform project with Angular and Laravel featuring user flows, content pages, and admin-ready app integrations.",
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

_CAREER_ROADMAP_SEED_I18N = {
    "cr-business-intern": {
        "role_title": {
            "en": "Business Intern",
            "ceb": "Business Intern",
            "fil_PH": "Business Intern",
            "fr": "Business Intern",
        },
        "definition": {
            "en": "Foundational internship focused on practical office workflows, communication, and day-to-day business support tasks.",
            "ceb": "Pundasyon nga internship nga naka-focus sa practical nga office workflows, komunikasyon, ug adlaw-adlaw nga business support tasks.",
            "fil_PH": "Foundational internship na nakatuon sa practical office workflows, communication, at araw-araw na business support tasks.",
            "fr": "Foundational internship focused on practical office workflows, communication, and day-to-day business support tasks.",
        },
        "summary": {
            "en": "This role helped build discipline in documentation, coordination, and problem-solving in a real workplace setting.",
            "ceb": "Kini nga role nakatabang sa pagpalig-on sa disiplina sa documentation, coordination, ug problem-solving sa tinuod nga workplace setting.",
            "fil_PH": "Ang role na ito ay nakatulong magpalakas ng disiplina sa documentation, coordination, at problem-solving sa totoong workplace setting.",
            "fr": "This role helped build discipline in documentation, coordination, and problem-solving in a real workplace setting.",
        },
        "highlights": {
            "en": [
                "Supported day-to-day office tasks and documentation workflows.",
                "Communicated with staff and learned formal workplace coordination.",
                "Built early experience in structured problem solving.",
            ],
            "ceb": [
                "Nisuporta sa adlaw-adlaw nga office tasks ug documentation workflows.",
                "Nakigkomunikar sa staff ug nakat-on sa formal workplace coordination.",
                "Nakabuild ug early experience sa structured problem solving.",
            ],
            "fil_PH": [
                "Sumuporta sa araw-araw na office tasks at documentation workflows.",
                "Nakipag-ugnayan sa staff at natutunan ang formal workplace coordination.",
                "Nakabuo ng early experience sa structured problem solving.",
            ],
            "fr": [
                "Supported day-to-day office tasks and documentation workflows.",
                "Communicated with staff and learned formal workplace coordination.",
                "Built early experience in structured problem solving.",
            ],
        },
        "activities": [
            {
                "title": {"en": "Office Support", "ceb": "Office Support", "fil_PH": "Office Support", "fr": "Office Support"},
                "caption": {
                    "en": "Daily admin support and structured tasks.",
                    "ceb": "Adlaw-adlaw nga admin support ug structured tasks.",
                    "fil_PH": "Araw-araw na admin support at structured tasks.",
                    "fr": "Daily admin support and structured tasks.",
                },
            },
            {
                "title": {"en": "Workflow Learning", "ceb": "Workflow Learning", "fil_PH": "Workflow Learning", "fr": "Workflow Learning"},
                "caption": {
                    "en": "Learning business process flow and communication.",
                    "ceb": "Pagkat-on sa business process flow ug communication.",
                    "fil_PH": "Pag-aaral ng business process flow at communication.",
                    "fr": "Learning business process flow and communication.",
                },
            },
        ],
    },
    "cr-trustarc-intern": {
        "role_title": {
            "en": "Software Development Intern",
            "ceb": "Software Development Intern",
            "fil_PH": "Software Development Intern",
            "fr": "Software Development Intern",
        },
        "definition": {
            "en": "Software internship centered on secure API work, app collaboration, and frontend integration in a professional development environment.",
            "ceb": "Software internship nga naka-center sa secure API work, app collaboration, ug frontend integration sa professional development environment.",
            "fil_PH": "Software internship na nakasentro sa secure API work, app collaboration, at frontend integration sa professional development environment.",
            "fr": "Software internship centered on secure API work, app collaboration, and frontend integration in a professional development environment.",
        },
        "summary": {
            "en": "Focused on safer API requests and cross-functional engineering tasks while learning production development practices.",
            "ceb": "Naka-focus sa mas luwas nga API requests ug cross-functional engineering tasks samtang nagkat-on sa production development practices.",
            "fil_PH": "Nakatuon sa mas ligtas na API requests at cross-functional engineering tasks habang natututo ng production development practices.",
            "fr": "Focused on safer API requests and cross-functional engineering tasks while learning production development practices.",
        },
        "highlights": {
            "en": [
                "Helped implement safe and secure API requests.",
                "Worked with app and frontend teams on product tasks.",
                "Experienced enterprise development workflows and reviews.",
            ],
            "ceb": [
                "Nikatabang sa pag-implement sa safe ug secure nga API requests.",
                "Nagtrabaho uban sa app ug frontend teams sa product tasks.",
                "Naka-experience sa enterprise development workflows ug reviews.",
            ],
            "fil_PH": [
                "Tumulong sa pag-implement ng safe at secure na API requests.",
                "Nakipagtrabaho sa app at frontend teams sa product tasks.",
                "Naka-experience ng enterprise development workflows at reviews.",
            ],
            "fr": [
                "Helped implement safe and secure API requests.",
                "Worked with app and frontend teams on product tasks.",
                "Experienced enterprise development workflows and reviews.",
            ],
        },
        "activities": [
            {
                "title": {"en": "API Tasks", "ceb": "API Tasks", "fil_PH": "API Tasks", "fr": "API Tasks"},
                "caption": {
                    "en": "Working on secure API request flows.",
                    "ceb": "Pagtrabaho sa secure API request flows.",
                    "fil_PH": "Paggawa sa secure API request flows.",
                    "fr": "Working on secure API request flows.",
                },
            },
            {
                "title": {"en": "Team Collaboration", "ceb": "Team Collaboration", "fil_PH": "Team Collaboration", "fr": "Team Collaboration"},
                "caption": {
                    "en": "Collaborating across app and frontend tasks.",
                    "ceb": "Pag-collaborate sa app ug frontend tasks.",
                    "fil_PH": "Pakikipag-collaborate sa app at frontend tasks.",
                    "fr": "Collaborating across app and frontend tasks.",
                },
            },
        ],
    },
    "cr-chronostep-intern": {
        "role_title": {
            "en": "App Development Intern",
            "ceb": "App Development Intern",
            "fil_PH": "App Development Intern",
            "fr": "App Development Intern",
        },
        "definition": {
            "en": "app internship focused on internal projects and building maintainable features using Laravel and Vue in a client-driven environment.",
            "ceb": "app internship nga naka-focus sa internal projects ug pagbuild ug maintainable features gamit ang Laravel ug Vue sa client-driven environment.",
            "fil_PH": "app internship na nakatuon sa internal projects at pagbuo ng maintainable features gamit ang Laravel at Vue sa client-driven environment.",
            "fr": "app internship focused on internal projects and building maintainable features using Laravel and Vue in a client-driven environment.",
        },
        "summary": {
            "en": "Contributed to internal systems while strengthening app architecture and implementation skills.",
            "ceb": "Nikatampo sa internal systems samtang gipalig-on ang app architecture ug implementation skills.",
            "fil_PH": "Nag-ambag sa internal systems habang pinalalakas ang app architecture at implementation skills.",
            "fr": "Contributed to internal systems while strengthening app architecture and implementation skills.",
        },
        "highlights": {
            "en": [
                "Developed internal projects for company use.",
                "Used Laravel and Vue for feature implementation.",
                "Learned team-based development and delivery pace.",
            ],
            "ceb": [
                "Nagdevelop ug internal projects para sa company use.",
                "Gigamit ang Laravel ug Vue para sa feature implementation.",
                "Nakat-on sa team-based development ug delivery pace.",
            ],
            "fil_PH": [
                "Nag-develop ng internal projects para sa company use.",
                "Gumamit ng Laravel at Vue para sa feature implementation.",
                "Natutunan ang team-based development at delivery pace.",
            ],
            "fr": [
                "Developed internal projects for company use.",
                "Used Laravel and Vue for feature implementation.",
                "Learned team-based development and delivery pace.",
            ],
        },
        "activities": [
            {
                "title": {"en": "Internal Projects", "ceb": "Internal Projects", "fil_PH": "Internal Projects", "fr": "Internal Projects"},
                "caption": {
                    "en": "Building internal company tools and features.",
                    "ceb": "Pagbuild sa internal company tools ug features.",
                    "fil_PH": "Pagbuo ng internal company tools at features.",
                    "fr": "Building internal company tools and features.",
                },
            },
            {
                "title": {"en": "app Workflow", "ceb": "app Workflow", "fil_PH": "app Workflow", "fr": "app Workflow"},
                "caption": {
                    "en": "Laravel-based app implementation and testing.",
                    "ceb": "Laravel-based app implementation ug testing.",
                    "fil_PH": "Laravel-based app implementation at testing.",
                    "fr": "Laravel-based app implementation and testing.",
                },
            },
        ],
    },
    "cr-chronostep-engineer": {
        "role_title": {
            "en": "Software Engineer",
            "ceb": "Software Engineer",
            "fil_PH": "Software Engineer",
            "fr": "Software Engineer",
        },
        "definition": {
            "en": "Full-time software engineering role building diverse client-focused solutions across app, frontend, and integration requirements.",
            "ceb": "Full-time software engineering role nga nagbuild ug lain-laing client-focused solutions sa app, frontend, ug integration requirements.",
            "fil_PH": "Full-time software engineering role na bumubuo ng iba-ibang client-focused solutions sa app, frontend, at integration requirements.",
            "fr": "Full-time software engineering role building diverse client-focused solutions across app, frontend, and integration requirements.",
        },
        "summary": {
            "en": "Expanded from internship work into production delivery, handling broader responsibilities and multi-technology solutions.",
            "ceb": "Ni-expand gikan sa internship work ngadto sa production delivery, nga nagdala ug mas lapad nga responsibilidad ug multi-technology solutions.",
            "fil_PH": "Lumawak mula internship work tungo sa production delivery, na humahawak ng mas malawak na responsibilidad at multi-technology solutions.",
            "fr": "Expanded from internship work into production delivery, handling broader responsibilities and multi-technology solutions.",
        },
        "highlights": {
            "en": [
                "Delivered client-specific projects using diverse technologies.",
                "Worked across frontend, app, and integration tasks.",
                "Contributed to production-ready features and delivery timelines.",
            ],
            "ceb": [
                "Naka-deliver ug client-specific projects gamit ang diverse technologies.",
                "Nagtrabaho sa frontend, app, ug integration tasks.",
                "Nikatampo sa production-ready features ug delivery timelines.",
            ],
            "fil_PH": [
                "Nag-deliver ng client-specific projects gamit ang diverse technologies.",
                "Nagtrabaho sa frontend, app, at integration tasks.",
                "Nag-ambag sa production-ready features at delivery timelines.",
            ],
            "fr": [
                "Delivered client-specific projects using diverse technologies.",
                "Worked across frontend, app, and integration tasks.",
                "Contributed to production-ready features and delivery timelines.",
            ],
        },
        "activities": [
            {
                "title": {"en": "Client Delivery", "ceb": "Client Delivery", "fil_PH": "Client Delivery", "fr": "Client Delivery"},
                "caption": {
                    "en": "Shipping features for client requirements.",
                    "ceb": "Pag-ship ug features para sa client requirements.",
                    "fil_PH": "Pag-ship ng features para sa client requirements.",
                    "fr": "Shipping features for client requirements.",
                },
            },
            {
                "title": {"en": "Engineering Work", "ceb": "Engineering Work", "fil_PH": "Engineering Work", "fr": "Engineering Work"},
                "caption": {
                    "en": "Multi-stack development and production support.",
                    "ceb": "Multi-stack development ug production support.",
                    "fil_PH": "Multi-stack development at production support.",
                    "fr": "Multi-stack development and production support.",
                },
            },
        ],
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

def _normalized_localized_list_map(value):
    if isinstance(value, dict):
        normalized = {}
        for locale in _KEY_PROJECT_LOCALES:
            locale_value = value.get(locale)
            if isinstance(locale_value, list):
                normalized[locale] = [str(x).strip() for x in locale_value if str(x).strip()]
            elif isinstance(locale_value, str):
                normalized[locale] = [line.strip() for line in locale_value.splitlines() if line.strip()]
            else:
                normalized[locale] = []
        return normalized

    if isinstance(value, list):
        english_list = [str(x).strip() for x in value if str(x).strip()]
        return {
            "en": english_list,
            "ceb": [],
            "fil_PH": [],
            "fr": [],
        }

    if isinstance(value, str):
        english_list = [line.strip() for line in value.splitlines() if line.strip()]
        return {
            "en": english_list,
            "ceb": [],
            "fil_PH": [],
            "fr": [],
        }

    return {locale: [] for locale in _KEY_PROJECT_LOCALES}

def _merge_seed_localized_list_map(value, seed_map=None):
    base = _normalized_localized_list_map(value)
    if not seed_map:
        return base

    normalized_seed = {}
    for locale in _KEY_PROJECT_LOCALES:
        seed_value = seed_map.get(locale, []) if isinstance(seed_map, dict) else []
        if isinstance(seed_value, list):
            normalized_seed[locale] = [str(x).strip() for x in seed_value if str(x).strip()]
        elif isinstance(seed_value, str):
            normalized_seed[locale] = [line.strip() for line in seed_value.splitlines() if line.strip()]
        else:
            normalized_seed[locale] = []

    merged = {locale: list(base.get(locale, [])) for locale in _KEY_PROJECT_LOCALES}
    english_value = merged.get("en", [])

    for locale in _KEY_PROJECT_LOCALES:
        current = merged.get(locale, [])
        seed_value = normalized_seed.get(locale, [])

        if not current and seed_value:
            merged[locale] = seed_value
            continue

        if locale != "en" and seed_value and english_value and current == english_value:
            merged[locale] = seed_value

    if not merged.get("en") and normalized_seed.get("en"):
        merged["en"] = normalized_seed["en"]

    return merged

def _localized_list_from_map(value_map, locale_value):
    locale = _locale_key(locale_value)
    selected = value_map.get(locale) or value_map.get("en") or []
    return [str(x).strip() for x in selected if str(x).strip()]

def _localized_roadmap_employment_type(value):
    text = str(value or "").strip()
    if not text:
        return ""

    normalized = text.lower().replace("_", "-").replace(" ", "-")
    label_map = {
        "internship": gettext("Career_Roadmap_Employment_Internship"),
        "full-time": gettext("Career_Roadmap_Employment_Full_Time"),
        "contract": gettext("Career_Roadmap_Employment_Contract"),
        "freelance": gettext("Career_Roadmap_Employment_Freelance"),
        "experience": gettext("Career_Roadmap_Employment_Experience"),
    }
    return label_map.get(normalized, text)

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
    log_result = handle_log_parameter()
    if log_result is not None:
        return log_result
    return redirect(url_for("pages.profile"))

def profile_route():
    profile_name = gettext("profile_name")
    profile_intro = gettext("profile_intro")
    profile_age = gettext("profile_age")
    profile_introvert = gettext("profile_introvert")
    profile_job = gettext("profile_job")
    profile_goals = gettext("profile_goals")
    profile_desc = f"{escape(profile_intro)} {escape(profile_age)}<br>{escape(profile_introvert)}<br>{escape(profile_job)} {escape(profile_goals)}"

    voice_icon = url_for("static", filename="images/voice.webp", _external=True)

    try:
        key_project_service.seed_default_projects_if_empty()
    except Exception as exc:

        print(f"Key project default seed failed: {exc}")

    try:
        company_roadmap_service.seed_default_company_roadmaps_if_empty()
    except Exception as exc:
        print(f"Company roadmap default seed failed: {exc}")

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

    return handle_log_parameter() or render_template(
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

def booking_route():
    return handle_log_parameter() or render_template(BOOKING_PAGE)

def portfolio_redirect():
    from flask import redirect
    return redirect("/portfolio", code=301)

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

