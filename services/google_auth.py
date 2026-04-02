import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import config
from services import redis_store


def get_redirect_uri():
    base_url = os.getenv("BASE_URL", "http://localhost:5001")
    return f"{base_url}/oauth/google/callback"


def get_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=config.GOOGLE_SCOPES,
        redirect_uri=get_redirect_uri(),
    )


def _load_token_data():
    """Redis 우선, 파일 폴백으로 토큰 데이터 로드"""
    if redis_store.is_available():
        data = redis_store.get("google_token")
        if data:
            return data
    if os.path.exists(config.TOKEN_PATH):
        try:
            with open(config.TOKEN_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def _save_token_data(creds):
    """Redis + 파일 양쪽에 토큰 저장"""
    token_json = creds.to_json()
    token_data = json.loads(token_json)
    if redis_store.is_available():
        redis_store.set("google_token", token_data)
    with open(config.TOKEN_PATH, "w") as f:
        f.write(token_json)


def get_credentials():
    token_data = _load_token_data()
    if not token_data:
        return None

    try:
        creds = Credentials.from_authorized_user_info(token_data, config.GOOGLE_SCOPES)
    except Exception:
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            saved_refresh_token = creds.refresh_token
            creds.refresh(Request())
            if not creds.refresh_token:
                creds.refresh_token = saved_refresh_token
            _save_token_data(creds)
        except Exception:
            return None

    return creds if creds and creds.valid else None


def save_credentials(creds):
    _save_token_data(creds)
