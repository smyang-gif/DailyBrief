from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from services.google_auth import get_credentials

KST = timezone(timedelta(hours=9))


def fetch_today_events():
    creds = get_credentials()
    if not creds:
        return None

    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(KST)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    results = service.events().list(
        calendarId="primary",
        timeMin=start_of_day,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy="startTime",
        timeZone="Asia/Seoul",
    ).execute()

    events = []
    for event in results.get("items", []):
        start = event["start"].get("dateTime", event["start"].get("date", ""))
        end = event["end"].get("dateTime", event["end"].get("date", ""))

        attendees = []
        for a in event.get("attendees", []):
            name = a.get("displayName", a.get("email", ""))
            attendees.append(name)

        events.append({
            "summary": event.get("summary", "(제목 없음)"),
            "start": start,
            "end": end,
            "location": event.get("location", ""),
            "attendees": attendees,
            "hangout_link": event.get("hangoutLink", ""),
        })

    return events
