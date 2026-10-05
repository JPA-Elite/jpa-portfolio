from app.constants.portfolio_locales import KEY_PROJECT_LOCALES


def locale_key(locale_value):
    locale_str = str(locale_value or "en")
    if locale_str.startswith("fil"):
        return "fil_PH"
    if locale_str.startswith("ceb"):
        return "ceb"
    if locale_str.startswith("fr"):
        return "fr"
    return "en"


def normalized_text_map(value):
    if isinstance(value, dict):
        return {
            locale: str(value.get(locale, "") or "").strip()
            for locale in KEY_PROJECT_LOCALES
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
    return {locale: "" for locale in KEY_PROJECT_LOCALES}


def merge_seed_localized_map(value, seed_map=None):
    base = normalized_text_map(value)
    if not seed_map:
        return base
    seed_map = {
        locale: str(seed_map.get(locale, "") or "").strip()
        for locale in KEY_PROJECT_LOCALES
    }
    english_value = (base.get("en") or "").strip()
    merged = dict(base)
    for locale in KEY_PROJECT_LOCALES:
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


def localized_value_from_map(value_map, locale_value, default_value=""):
    locale = locale_key(locale_value)
    return (
        (value_map.get(locale) or "").strip()
        or (value_map.get("en") or "").strip()
        or default_value
    )


def normalized_list_map(value):
    if isinstance(value, dict):
        normalized = {}
        for locale in KEY_PROJECT_LOCALES:
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
    return {locale: [] for locale in KEY_PROJECT_LOCALES}


def merge_seed_localized_list_map(value, seed_map=None):
    base = normalized_list_map(value)
    if not seed_map:
        return base
    normalized_seed = {}
    for locale in KEY_PROJECT_LOCALES:
        seed_value = seed_map.get(locale, []) if isinstance(seed_map, dict) else []
        if isinstance(seed_value, list):
            normalized_seed[locale] = [str(x).strip() for x in seed_value if str(x).strip()]
        elif isinstance(seed_value, str):
            normalized_seed[locale] = [line.strip() for line in seed_value.splitlines() if line.strip()]
        else:
            normalized_seed[locale] = []
    merged = {locale: list(base.get(locale, [])) for locale in KEY_PROJECT_LOCALES}
    english_value = merged.get("en", [])
    for locale in KEY_PROJECT_LOCALES:
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


def localized_list_from_map(value_map, locale_value):
    locale = locale_key(locale_value)
    selected = value_map.get(locale) or value_map.get("en") or []
    return [str(x).strip() for x in selected if str(x).strip()]


def same_text_map(text):
    cleaned = str(text or "").strip()
    return {locale: cleaned for locale in KEY_PROJECT_LOCALES}


def same_list_map(items):
    cleaned = [str(x).strip() for x in (items or []) if str(x).strip()]
    return {locale: list(cleaned) for locale in KEY_PROJECT_LOCALES}


def get_i18n_text_map(source, field_name, fr_field_name=None):
    get = source.get if hasattr(source, "get") else lambda key, default="": default
    result = {
        "en": str(get(field_name, "") or "").strip(),
        "ceb": str(get(f"{field_name}_ceb", "") or "").strip(),
        "fil_PH": str(get(f"{field_name}_fil", "") or "").strip(),
    }
    if fr_field_name is not None:
        result["fr"] = str(get(fr_field_name, "") or "").strip()
    else:
        result["fr"] = str(get(f"{field_name}_fr", "") or "").strip()
    return result
