import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

IS_VERCEL = os.getenv("VERCEL", False)
TOKEN_PATH = "/tmp/token.json" if IS_VERCEL else os.path.join(os.path.dirname(__file__), "token.json")
