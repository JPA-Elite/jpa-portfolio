from flask import request, url_for

from app.domains import (
    PROFESSIONAL_PERSONAL_PATHS,
    SITE_LANDING,
    SITE_PROFESSIONAL,
    SITE_SOCIAL,
    current_site,
    get_domain_config,
)


PROFESSIONAL = SITE_PROFESSIONAL
SOCIAL = SITE_SOCIAL

SITE_NAME = "JPAStack"
AUTHOR = "Joshua Algadipe"
SITE_ALTERNATE_NAMES = ("Joshua Algadipe", "JPAStack Portfolio", "jpastack.com")
SITE_JOB_TITLE = "Software Engineer"
DEFAULT_OG_IMAGE = "images/1x1_the_eys_will_move_and_also_its_m.webp"
DEFAULT_ROBOTS = "index,follow"
NOINDEX_ROBOTS = "noindex,nofollow"

PROFESSIONAL_EXCLUDED_PAGES = frozenset(
    path.lstrip("/") for path in PROFESSIONAL_PERSONAL_PATHS
)

SITE_DEFAULTS = {
    PROFESSIONAL: {
        "title": "Joshua Algadipe — Software Engineer",
        "description": (
            "Portfolio of Joshua Algadipe, a software engineer building reliable web "
            "applications and APIs. Explore selected projects, technical skills, and "
            "experience."
        ),
        "keywords": (
            "Joshua Algadipe, software engineer, full stack developer, backend developer, "
            "Python developer, software portfolio"
        ),
    },
    SOCIAL: {
        "title": "Joshua Algadipe | Personal Portfolio",
        "description": (
            "Step into the personal side of Joshua Algadipe — stories, photos, vlogs, "
            "favorite music, and the projects he is building along the way."
        ),
        "keywords": (
            "Joshua Algadipe, personal portfolio, blog, vlog, gallery, music, projects"
        ),
    },
}

PAGE_SEO = {
    "portfolio": {
        PROFESSIONAL: {
            "title": "Joshua Algadipe — Software Engineer Portfolio",
            "description": (
                "Portfolio of Joshua Algadipe, a software engineer building reliable web "
                "apps and APIs. Explore selected projects, technical skills, experience, "
                "and contact details."
            ),
            "keywords": (
                "Joshua Algadipe, software engineer, full stack developer, backend "
                "developer, Python developer, web developer portfolio, hire software engineer"
            ),
        },
        SOCIAL: {
            "title": "Joshua Algadipe | Personal Portfolio",
            "description": (
                "Explore the personal portfolio of Joshua Algadipe — stories, photos, "
                "vlogs, favorite music, and the projects he is building along the way."
            ),
            "keywords": (
                "Joshua Algadipe, personal portfolio, blog, vlog, gallery, music, projects"
            ),
        },
    },
    "gallery": {
        PROFESSIONAL: {
            "title": "Gallery | Joshua Algadipe — Software Engineer",
            "description": (
                "A visual look at the work and world of Joshua Algadipe, a software "
                "engineer — project moments, events, and everyday scenes."
            ),
            "keywords": (
                "Joshua Algadipe gallery, software engineer portfolio, project photos, "
                "developer portfolio"
            ),
        },
        SOCIAL: {
            "title": "Photo Gallery | Joshua Algadipe",
            "description": (
                "Browse the personal photo gallery of Joshua Algadipe, featuring everyday "
                "moments, travels, events, and creative shots."
            ),
            "keywords": (
                "photo gallery, Joshua Algadipe photos, personal photos, travel, events"
            ),
        },
    },
    "vlog": {
        SOCIAL: {
            "title": "Vlogs & Stories | Joshua Algadipe",
            "description": (
                "Watch vlogs from Joshua Algadipe about life, experiences, and the stories "
                "behind the projects. Personal updates, insights, and moments."
            ),
            "keywords": (
                "Joshua Algadipe vlog, personal vlog, life stories, video blog"
            ),
        },
    },
    "music": {
        SOCIAL: {
            "title": "My Favorite Music Playlist | Joshua Algadipe",
            "description": (
                "Explore Joshua Algadipe's favorite music playlist — a curated mix of "
                "tracks that inspire, motivate, and shape his day."
            ),
            "keywords": (
                "favorite music playlist, Joshua Algadipe music, songs, playlist"
            ),
        },
    },
    "concern": {
        SOCIAL: {
            "title": "Share a Concern | Joshua Algadipe",
            "description": (
                "Have a thought, question, or concern? Reach out to Joshua Algadipe "
                "directly through this page and start a conversation."
            ),
            "keywords": (
                "contact Joshua Algadipe, concerns, feedback, questions, message"
            ),
        },
    },
    "donation": {
        SOCIAL: {
            "title": "Support Joshua Algadipe's Work",
            "description": (
                "Support the creative and personal projects of Joshua Algadipe with a "
                "donation. Your contribution helps keep the work going."
            ),
            "keywords": (
                "donate, support Joshua Algadipe, contribution, projects"
            ),
        },
    },
    "build": {
        PROFESSIONAL: {
            "title": "Hire Me | Book a Project — Joshua Algadipe",
            "description": (
                "Book a project, consultation, or build session with Joshua Algadipe. "
                "Share your requirements and schedule a time to discuss your software idea."
            ),
            "keywords": (
                "hire software engineer, book developer, project consultation, "
                "Joshua Algadipe"
            ),
        },
        SOCIAL: {
            "title": "Build With Me | Joshua Algadipe",
            "description": (
                "Have an idea? Book a build session or appointment with Joshua Algadipe "
                "and let's turn it into something real."
            ),
            "keywords": (
                "book appointment, build session, Joshua Algadipe, collaboration"
            ),
        },
    },
    "app_details": {
        "title": "Built Apps — Joshua Algadipe",
        "description": "Explore apps built by Joshua Algadipe.",
        "keywords": "Joshua Algadipe apps, built apps, software downloads",
    },
    "add_portfolio": {
        "title": "Add Portfolio Entry — Joshua Algadipe",
        "description": "Internal form for adding portfolio entries.",
        "keywords": "",
        "robots": NOINDEX_ROBOTS,
    },
    "visitors": {
        "title": "Device-Info Visits — Joshua Algadipe",
        "description": "Internal visit log.",
        "keywords": "",
        "robots": NOINDEX_ROBOTS,
    },
}

ENDPOINT_PAGE_KEYS = {
    "pages.index": "portfolio",
    "pages.portfolio": "portfolio",
    "pages.gallery": "gallery",
    "pages.vlog": "vlog",
    "pages.music": "music",
    "pages.concern": "concern",
    "pages.donation": "donation",
    "pages.booking": "build",
    "pages.built_app_details": "app_details",
    "pages.add_portfolio_form": "add_portfolio",
    "pages.visitors": "visitors",
}


def site_variant(site=None):
    resolved = site if site is not None else current_site()
    return PROFESSIONAL if resolved == SITE_PROFESSIONAL else SOCIAL


def page_key_for_endpoint(endpoint):
    return ENDPOINT_PAGE_KEYS.get(endpoint or "", "")


def resolve_page_seo(endpoint=None, site=None, overrides=None):
    variant = site_variant(site)
    page_key = page_key_for_endpoint(endpoint)
    meta = {
        "title": "",
        "description": "",
        "keywords": "",
        "author": AUTHOR,
        "robots": DEFAULT_ROBOTS,
        "og_type": "website",
        "site_name": SITE_NAME,
        "site": variant,
        "page": page_key,
    }
    meta.update(SITE_DEFAULTS[variant])
    page_entry = PAGE_SEO.get(page_key, {}) if page_key else {}
    if "title" in page_entry:
        meta.update(page_entry)
    else:
        meta.update(page_entry.get(variant) or page_entry.get(SOCIAL) or {})
    if overrides:
        meta.update({key: value for key, value in overrides.items() if value is not None})
    if variant == PROFESSIONAL and page_key in PROFESSIONAL_EXCLUDED_PAGES:
        meta["robots"] = NOINDEX_ROBOTS
        meta["canonical"] = ""
    return meta


def _request_site_host(cfg):
    try:
        site = current_site(request.host)
    except Exception:
        return ""
    if site == SITE_PROFESSIONAL:
        return cfg.get("professional_domain") or cfg.get("landing_domain") or ""
    if site == SITE_SOCIAL:
        return cfg.get("social_domain") or cfg.get("landing_domain") or ""
    if site == SITE_LANDING:
        return cfg.get("landing_domain") or ""
    return ""


def _canonical_base(variant):
    try:
        cfg = get_domain_config()
    except Exception:
        cfg = {}
    host = _request_site_host(cfg)
    if not host:
        if variant == PROFESSIONAL:
            host = cfg.get("professional_domain") or cfg.get("landing_domain") or ""
        else:
            host = cfg.get("social_domain") or cfg.get("landing_domain") or ""
    if host:
        return f"https://{host}"
    try:
        return request.url_root.rstrip("/")
    except Exception:
        return ""


def _absolute(variant, value):
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://") or text.startswith("//"):
        return text
    if text.startswith("/"):
        return f"{_canonical_base(variant)}{text}"
    return text


def site_structured_data(meta):
    if meta.get("robots") == NOINDEX_ROBOTS:
        return {}
    base = (_canonical_base(meta.get("site")) or "").rstrip("/")
    if not base:
        return {}
    site_id = f"{base}/#website"
    person_id = f"{base}/#person"
    person = {
        "@type": "Person",
        "@id": person_id,
        "name": AUTHOR,
        "url": f"{base}/",
        "jobTitle": SITE_JOB_TITLE,
    }
    image = meta.get("image")
    if image:
        person["image"] = image
    website = {
        "@type": "WebSite",
        "@id": site_id,
        "url": f"{base}/",
        "name": SITE_NAME,
        "alternateName": list(SITE_ALTERNATE_NAMES),
        "inLanguage": "en",
        "publisher": {"@id": person_id},
    }
    return {"@context": "https://schema.org", "@graph": [website, person]}


def page_seo_context(endpoint=None, site=None, overrides=None):
    meta = resolve_page_seo(endpoint, site, overrides)
    path = ""
    try:
        path = request.path or ""
    except Exception:
        path = ""
    if not path and meta.get("page"):
        path = "/portfolio" if meta["page"] == "portfolio" else ""
    if "canonical" not in meta:
        meta["canonical"] = f"{_canonical_base(meta['site'])}{path}" if path else ""
    image = meta.get("image")
    if not image:
        try:
            image = url_for("static", filename=DEFAULT_OG_IMAGE)
        except Exception:
            image = ""
    meta["image"] = _absolute(meta["site"], image)
    meta["structured_data"] = site_structured_data(meta)
    return meta


def inject_page_seo():
    try:
        endpoint = request.endpoint
        site = current_site(request.host)
    except Exception:
        endpoint = None
        site = None
    return {"page_seo": page_seo_context(endpoint, site)}
