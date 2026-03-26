from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import config

_user_map_cache = {}
_my_user_id_cache = None


def _get_client():
    return WebClient(token=config.SLACK_USER_TOKEN)


def _get_user_map(client):
    global _user_map_cache
    if _user_map_cache:
        return _user_map_cache
    try:
        result = client.users_list()
        _user_map_cache = {u["id"]: u.get("real_name", u.get("name", u["id"])) for u in result["members"]}
        return _user_map_cache
    except SlackApiError:
        return {}


def fetch_unread_slack(after_timestamp=0):
    global _my_user_id_cache

    client = _get_client()
    if not config.SLACK_USER_TOKEN:
        return None

    user_map = _get_user_map(client)

    if not _my_user_id_cache:
        auth = client.auth_test()
        _my_user_id_cache = auth["user_id"]
    my_user_id = _my_user_id_cache

    unread = {"mentions": [], "dms": [], "channels": []}

    try:
        convos = client.users_conversations(types="public_channel,private_channel,mpim,im", limit=200)
    except SlackApiError:
        return unread

    oldest = str(after_timestamp) if after_timestamp > 0 else None

    # unread_count_display가 conversations.list에 포함되지 않으므로
    # conversations_info를 호출해야 하지만, 읽지 않은 채널만 필터링하기 위해
    # 먼저 최근 활동이 있는 채널만 골라서 API 호출을 최소화
    channels = convos.get("channels", [])

    # DM과 채널을 분리하고, 최대 30개만 확인 (가장 최근 활동 기준)
    channels = channels[:30]

    for ch in channels:
        ch_id = ch["id"]
        ch_name = ch.get("name", "DM")
        is_im = ch.get("is_im", False)

        try:
            info = client.conversations_info(channel=ch_id)
            channel_data = info.get("channel", {})
        except SlackApiError:
            continue

        unread_count = channel_data.get("unread_count_display", 0)
        if not unread_count:
            continue

        try:
            history_args = {"channel": ch_id, "limit": min(unread_count, 5)}
            if oldest:
                history_args["oldest"] = oldest
            history = client.conversations_history(**history_args)
        except SlackApiError:
            continue

        messages = []
        has_mention = False

        for msg in history.get("messages", []):
            text = msg.get("text", "")
            user_id = msg.get("user", "")
            user_name = user_map.get(user_id, user_id)

            if f"<@{my_user_id}>" in text:
                has_mention = True
                unread["mentions"].append({
                    "channel": ch_name,
                    "channel_id": ch_id,
                    "user": user_name,
                    "text": text.replace(f"<@{my_user_id}>", "@나"),
                    "ts": msg.get("ts", ""),
                })

            messages.append({
                "user": user_name,
                "text": text[:200],
                "ts": msg.get("ts", ""),
            })

        if is_im:
            dm_user = user_map.get(ch.get("user", ""), ch_name)
            unread["dms"].append({
                "user": dm_user,
                "channel_id": ch_id,
                "unread_count": unread_count,
                "recent_messages": messages[:3],
            })
        else:
            unread["channels"].append({
                "name": ch_name,
                "channel_id": ch_id,
                "unread_count": unread_count,
                "has_mention": has_mention,
                "recent_messages": messages[:3],
            })

    unread["channels"].sort(key=lambda x: (not x["has_mention"], -x["unread_count"]))
    return unread
