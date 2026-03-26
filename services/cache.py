import json
import os
import time

CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache.json")


def load_cache():
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_cache(data):
    data["_cached_at"] = time.time()
    with open(CACHE_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False)


def get_last_fetch_time():
    cache = load_cache()
    if cache:
        return cache.get("_cached_at", 0)
    return 0
