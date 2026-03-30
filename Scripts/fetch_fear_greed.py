import requests
import json
import os
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "Data", "Sentiment")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "fear-greed.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://money.cnn.com/data/fear-and-greed/",
}

START_DATE = "2024-04-01"
URL = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{START_DATE}"


def score_to_rating(score: int) -> str:
    if score <= 24:
        return "Extreme Fear"
    elif score <= 44:
        return "Fear"
    elif score <= 55:
        return "Neutral"
    elif score <= 74:
        return "Greed"
    else:
        return "Extreme Greed"


def ts_ms_to_date(ts_ms: float) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=JST)
    return dt.strftime("%Y-%m-%d")


def main():
    print(f"Fetching Fear & Greed data from {URL} ...")
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # 現在値
    fg = data["fear_and_greed"]
    current_value = round(fg["score"])
    current_label = score_to_rating(current_value)

    # 履歴データ
    hist_raw = data["fear_and_greed_historical"]["data"]
    history = []
    for entry in hist_raw:
        date_str = ts_ms_to_date(entry["x"])
        value = round(entry["y"])
        label = score_to_rating(value)
        history.append({"date": date_str, "value": value, "label": label})

    # 日付順にソート
    history.sort(key=lambda h: h["date"])

    # prev_close: 履歴の最後から2番目（昨日）
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

    # updated タイムスタンプ（JST）
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
