from werkzeug.urls import url_encode

from app.extensions import cache


def get_cache_data(func_name, args=None, timeout=None, default=None):
    cache_key = f"{func_name}:{url_encode(args)}" if args else f"{func_name}:all"
    cached_data = cache.get(cache_key)

    if cached_data is None and default is not None:
        cache.set(cache_key, default, timeout=timeout)
        cached_data = default

    return cached_data, cache_key


def clear_cache_by_prefix(prefix: str):
    try:
        store = getattr(cache.cache, "_cache", None)
    except Exception:
        store = None
    if isinstance(store, dict):
        for key in list(store.keys()):
            if isinstance(key, str) and key.startswith(prefix):
                try:
                    cache.delete(key)
                except Exception:
                    pass
        return
    try:
        cache.clear()
    except Exception:
        pass
