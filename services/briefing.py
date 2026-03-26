import anthropic
import json
from datetime import datetime
import config


def generate_briefing(emails, events, slack):
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # 데이터 요약 구성
    context_parts = []

    # 일정
    if events:
        lines = []
        for e in events:
            time_str = e["start"][11:16] if "T" in e["start"] else "종일"
            attendees = ", ".join(e["attendees"][:5]) if e["attendees"] else ""
            lines.append(f"- {time_str} {e['summary']}" + (f" (참석: {attendees})" if attendees else ""))
        context_parts.append(f"## 오늘 일정 ({len(events)}건)\n" + "\n".join(lines))

    # 메일
    if emails:
        lines = []
        for e in emails[:15]:
            lines.append(f"- From: {e['from']}\n  Subject: {e['subject']}\n  내용: {e['snippet'][:100]}")
        context_parts.append(f"## 읽지 않은 메일 ({len(emails)}건)\n" + "\n".join(lines))

    # 슬랙
    if slack:
        lines = []
        if slack.get("mentions"):
            for m in slack["mentions"]:
                lines.append(f"- [멘션] #{m['channel']} {m['user']}: {m['text'][:100]}")
        if slack.get("dms"):
            for d in slack["dms"]:
                lines.append(f"- [DM] {d['user']} ({d['unread_count']}건 미읽)")
                for msg in d["recent_messages"][:2]:
                    lines.append(f"  > {msg['user']}: {msg['text'][:80]}")
        if slack.get("channels"):
            for c in slack["channels"]:
                mention_tag = " ⚡멘션" if c["has_mention"] else ""
                lines.append(f"- #{c['name']} ({c['unread_count']}건 미읽{mention_tag})")
                for msg in c["recent_messages"][:2]:
                    lines.append(f"  > {msg['user']}: {msg['text'][:80]}")
        context_parts.append(f"## Slack 미읽 메시지\n" + "\n".join(lines))

    if not context_parts:
        return "새로운 메일, 일정, 슬랙 메시지가 없습니다. 여유로운 아침이네요!"

    context = "\n\n".join(context_parts)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": f"""다음은 오늘({datetime.now().strftime('%Y년 %m월 %d일 %A')}) 아침 브리핑 데이터입니다.

{context}

위 내용을 바탕으로 한국어 데일리 브리핑을 작성해주세요:

1. **오늘의 핵심 요약** (3~5줄): 오늘 가장 중요한 것들을 우선순위로 정리
2. **주의 필요 항목**: 긴급하거나 답장이 필요한 건, 준비가 필요한 미팅 등
3. **일정 흐름**: 시간순으로 오늘 하루 흐름

간결하고 실용적으로. 불필요한 인사말이나 장식 없이 바로 핵심만.""",
            }
        ],
    )

    return message.content[0].text
