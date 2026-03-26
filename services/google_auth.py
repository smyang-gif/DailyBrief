import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import config


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


def get_credentials():
    if not os.path.exists(config.TOKEN_PATH):
        return None

    creds = Credentials.from_authorized_user_file(config.TOKEN_PATH, config.GOOGLE_SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(config.TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds if creds and creds.valid else None


def save_credentials(creds):
    with open(config.TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
