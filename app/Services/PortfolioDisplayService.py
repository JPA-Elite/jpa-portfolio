from flask_babel import gettext
from app.configurations import get_locale
from app.constants.portfolio_locales import KEY_PROJECT_LOCALES
from app.utils_i18n import locale_key, localized_value_from_map, merge_seed_localized_map


def localized_roadmap_employment_type(value, gettext_fn=None):
    text = str(value or "").strip()
    if not text:
        return ""
    translate = gettext_fn or gettext
    normalized = text.lower().replace("_", "-").replace(" ", "-")
    label_map = {
        "internship": translate("Career_Roadmap_Employment_Internship"),
        "full-time": translate("Career_Roadmap_Employment_Full_Time"),
        "contract": translate("Career_Roadmap_Employment_Contract"),
        "freelance": translate("Career_Roadmap_Employment_Freelance"),
        "experience": translate("Career_Roadmap_Employment_Experience"),
    }
    return label_map.get(normalized, text)


def resolve_project_stack_display(stack_value, locale_value, seed_stack_map=None):
    locale = locale_key(locale_value)
    if isinstance(stack_value, dict):
        stack_map = merge_seed_localized_map(stack_value, seed_stack_map)
        return localized_value_from_map(stack_map, locale, "")
    stack_text = str(stack_value or "").strip()
    if seed_stack_map:
        seed_stack_map = {
            key: str(seed_stack_map.get(key, "") or "").strip()
            for key in KEY_PROJECT_LOCALES
        }
        english_seed = seed_stack_map.get("en", "")
        if not stack_text or stack_text == english_seed:
            return (
                seed_stack_map.get(locale)
                or seed_stack_map.get("en")
                or stack_text
            )
    return stack_text


def resolve_built_app_display(app_dict, locale_value=None):
    locale = locale_key(locale_value if locale_value else get_locale())
    name_map = app_dict.get("name") or {}
    short_map = app_dict.get("short_description") or {}
    full_map = app_dict.get("full_description") or {}
    paragraphs = full_map.get(locale) or full_map.get("en") or []
    snapshots = [
        {
            "id": (s or {}).get("id"),
            "image_url": (s or {}).get("image_url"),
            "sort_order": (s or {}).get("sort_order", index),
        }
        for index, s in enumerate(app_dict.get("snapshots") or [])
        if isinstance(s, dict) and s.get("image_url")
    ]
    return {
        **app_dict,
        "name": (name_map.get(locale) or name_map.get("en") or "").strip(),
        "short_description": (short_map.get(locale) or short_map.get("en") or "").strip(),
        "full_description": [str(p).strip() for p in paragraphs if str(p).strip()],
        "snapshots": snapshots,
    }
