import json
import os
import urllib.request
import urllib.error

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")


def is_available():
    return bool(UPSTASH_URL and UPSTASH_TOKEN)


def _request(command):
    url = UPSTASH_URL
    headers = {
        "Authorization": f"Bearer {UPSTASH_TOKEN}",
        "Content-Type": "application/json",
    }
    data = json.dumps(command).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError):
        return None


def get(key):
    result = _request(["GET", key])
    if result and result.get("result"):
        try:
            return json.loads(result["result"])
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def set(key, value):
    encoded = json.dumps(value, ensure_ascii=False)
    result = _request(["SET", key, encoded])
    return result is not None
