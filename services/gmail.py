from datetime import datetime
from googleapiclient.discovery import build
from services.google_auth import get_credentials


def fetch_unread_emails(max_results=15, after_timestamp=0):
    creds = get_credentials()
    if not creds:
        return None

    service = build("gmail", "v1", credentials=creds)

    q = "is:unread"
    if after_timestamp > 0:
        after_epoch = int(after_timestamp)
        q += f" after:{after_epoch}"

    results = service.users().messages().list(
        userId="me",
        q=q,
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    # 배치 요청으로 메일 상세를 한 번에 가져오기 (개별 호출 대비 훨씬 빠름)
    emails = []

    def make_callback(msg_id):
        def callback(request_id, response, exception):
            if exception:
                return
            headers = {h["name"]: h["value"] for h in response.get("payload", {}).get("headers", [])}
            emails.append({
                "id": msg_id,
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", "(제목 없음)"),
                "date": headers.get("Date", ""),
                "snippet": response.get("snippet", ""),
            })
        return callback

    batch = service.new_batch_http_request()
    for msg in messages:
        batch.add(
            service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ),
            callback=make_callback(msg["id"]),
        )
    batch.execute()

    return emails
