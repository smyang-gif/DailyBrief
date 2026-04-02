import os
import json
import webbrowser
import threading
import time
from concurrent.futures import ThreadPoolExecutor

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from flask import Flask, render_template, jsonify, redirect, request
from services.google_auth import get_flow, get_credentials, save_credentials
from services.gmail import fetch_unread_emails
from services.calendar import fetch_today_events
from services.slack import fetch_unread_slack
from services.briefing import generate_briefing
from services.cache import load_cache, save_cache, get_last_fetch_time
from services.token_usage import get_usage_summary
import config

app = Flask(__name__)
app.secret_key = "dailybrief-local-only"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/briefing")
def api_briefing():
    try:
        google_ok = get_credentials() is not None
        slack_ok = bool(config.SLACK_USER_TOKEN)
        claude_ok = bool(config.ANTHROPIC_API_KEY)

        if not google_ok:
            return jsonify({
                "needs_auth": True,
                "status": {"google": google_ok, "slack": slack_ok, "claude": claude_ok},
            })

        # 캐시가 있으면 즉시 반환 (fresh=1이 아닌 한)
        force_fresh = request.args.get("fresh", "0") == "1"
        cached = load_cache()

        if cached and not force_fresh:
            cached["from_cache"] = True
            return jsonify(cached)

        # 전체 로드 — Gmail, Calendar, Slack 병렬 실행
        with ThreadPoolExecutor(max_workers=3) as pool:
            email_future = pool.submit(fetch_unread_emails) if google_ok else None
            event_future = pool.submit(fetch_today_events) if google_ok else None
            slack_future = pool.submit(fetch_unread_slack) if slack_ok else None

        emails = email_future.result() if email_future else []
        events = event_future.result() if event_future else []
        slack = slack_future.result() if slack_future else {"mentions": [], "dms": [], "channels": []}

        briefing = None
        if claude_ok and (emails or events or slack):
            try:
                briefing = generate_briefing(emails or [], events or [], slack)
            except Exception as e:
                briefing = f"AI 브리핑 생성 실패: {str(e)}"

        result = {
            "needs_auth": False,
            "briefing": briefing,
            "events": events or [],
            "emails": emails or [],
            "slack": slack or {"mentions": [], "dms": [], "channels": []},
            "from_cache": False,
        }
        save_cache(result)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "needs_auth": False}), 500


@app.route("/oauth/google")
def oauth_google():
    flow = get_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return redirect(auth_url)


@app.route("/oauth/google/callback")
def oauth_google_callback():
    flow = get_flow()
    auth_response = request.url.replace("http://", "https://")
    flow.fetch_token(authorization_response=auth_response)
    save_credentials(flow.credentials)
    return redirect("/")


@app.route("/api/token-usage")
def api_token_usage():
    try:
        return jsonify(get_usage_summary())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/debug")
def api_debug():
    try:
        creds = get_credentials()
        google_ok = creds is not None
        slack_ok = bool(config.SLACK_USER_TOKEN)
        claude_ok = bool(config.ANTHROPIC_API_KEY)

        debug = {
            "google_ok": google_ok,
            "slack_ok": slack_ok,
            "claude_ok": claude_ok,
            "errors": [],
        }

        if google_ok:
            try:
                emails = fetch_unread_emails()
                debug["emails_count"] = len(emails) if emails else 0
            except Exception as e:
                debug["errors"].append(f"gmail: {str(e)}")

            try:
                events = fetch_today_events()
                debug["events_count"] = len(events) if events else 0
            except Exception as e:
                debug["errors"].append(f"calendar: {str(e)}")

        if slack_ok:
            try:
                slack = fetch_unread_slack()
                debug["slack_mentions"] = len(slack["mentions"]) if slack else 0
                debug["slack_dms"] = len(slack["dms"]) if slack else 0
                debug["slack_channels"] = len(slack["channels"]) if slack else 0
            except Exception as e:
                debug["errors"].append(f"slack: {str(e)}")

        return jsonify(debug)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def open_browser():
    webbrowser.open("http://localhost:5001")


if __name__ == "__main__":
    print("\n  Daily Brief - http://localhost:5001\n")
    threading.Timer(1.0, open_browser).start()
    app.run(host="localhost", port=5001, debug=False)
