import requests
import json
import os
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "Data", "Sentiment")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "crypto-fear-greed.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

URL = "https://api.alternative.me/fng/?limit=730&date_format=world"


def parse_date(ts: str) -> str:
    """date_format=world returns DD-MM-YYYY; convert to YYYY-MM-DD."""
    try:
        dt = datetime.strptime(ts, "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        # fallback: unix timestamp
        dt = datetime.fromtimestamp(int(ts), tz=JST)
        return dt.strftime("%Y-%m-%d")


def main():
    print(f"Fetching Crypto Fear & Greed data from {URL} ...")
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    raw = data["data"]

    # 日付昇順にソート（APIは降順で返す）
    history = []
    for entry in raw:
        date_str = parse_date(entry["timestamp"])
        value = int(entry["value"])
        label = entry["value_classification"]
        history.append({"date": date_str, "value": value, "label": label})

    history.sort(key=lambda h: h["date"])

    # 現在値: 最新エントリ
    current_value = history[-1]["value"]
    current_label = history[-1]["label"]

    # prev_close: 最新から2番目
    prev_close = history[-2]["value"] if len(history) >= 2 else current_value

    # 1週間前: 7日前に最も近いエントリ
    today = datetime.now(tz=JST).date()
    target_week_ago = today - timedelta(days=7)
    week_ago_value = None
    for entry in reversed(history):
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        if entry_date <= target_week_ago:
            week_ago_value = entry["value"]
            break
    if week_ago_value is None:
        week_ago_value = history[0]["value"] if history else current_value

    now_jst = datetime.now(tz=JST)
    updated = now_jst.strftime("%Y-%m-%dT%H:%M:%S+09:00")

    result = {
        "updated": updated,
        "current": {
            "value": current_value,
            "label": current_label,
        },
        "prev_close": prev_close,
        "week_ago": week_ago_value,
        "history": history,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Saved to {OUTPUT_FILE}")
    print(f"Current: {current_value} ({current_label}), prev_close: {prev_close}, week_ago: {week_ago_value}")
    print(f"History: {len(history)} entries ({history[0]['date']} ~ {history[-1]['date']})")


if __name__ == "__main__":
    main()
