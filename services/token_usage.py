import json
import os
import time

IS_VERCEL = os.getenv("VERCEL", False)
USAGE_PATH = "/tmp/.token_usage.json" if IS_VERCEL else os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".token_usage.json"
)

# Claude Sonnet 4 pricing (per 1M tokens)
PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
}
DEFAULT_PRICING = {"input": 3.0, "output": 15.0}


def _load_usage():
    if not os.path.exists(USAGE_PATH):
        return {"records": [], "totals": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}}
    try:
        with open(USAGE_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"records": [], "totals": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}}


def _save_usage(data):
    with open(USAGE_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_usage(model, input_tokens, output_tokens):
    pricing = PRICING.get(model, DEFAULT_PRICING)
    cost = (input_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"]

    data = _load_usage()
    data["records"].append({
        "timestamp": time.time(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 6),
    })
    data["totals"]["input_tokens"] += input_tokens
    data["totals"]["output_tokens"] += output_tokens
    data["totals"]["cost_usd"] = round(data["totals"]["cost_usd"] + cost, 6)

    _save_usage(data)
    return cost


def get_usage_summary():
    data = _load_usage()
    totals = data["totals"]
    recent = data["records"][-10:] if data["records"] else []

    # Today's usage
    today_start = time.time() - (time.time() % 86400)
    today_records = [r for r in data["records"] if r["timestamp"] >= today_start]
    today_input = sum(r["input_tokens"] for r in today_records)
    today_output = sum(r["output_tokens"] for r in today_records)
    today_cost = sum(r["cost_usd"] for r in today_records)

    return {
        "today": {
            "input_tokens": today_input,
            "output_tokens": today_output,
            "cost_usd": round(today_cost, 6),
            "calls": len(today_records),
        },
        "all_time": {
            "input_tokens": totals["input_tokens"],
            "output_tokens": totals["output_tokens"],
            "cost_usd": round(totals["cost_usd"], 6),
            "calls": len(data["records"]),
        },
        "recent": recent,
    }
