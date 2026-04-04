"""
ルールベースのコモディティアラート生成。
data/commodities/daily-prices.json を読み、data/alerts/daily-alerts.json に出力する。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[2]
PRICES_FILE = REPO_ROOT / "data" / "commodities" / "daily-prices.json"
OUT_DIR = REPO_ROOT / "data" / "alerts"
OUT_FILE = OUT_DIR / "daily-alerts.json"

# fetch_commodities.py と同じ順序
COMMODITY_ORDER = ["copper", "gold", "wti", "brent", "usdjpy"]

IMPACT: dict[str, str] = {
    "copper": "住友鉱山(5713)に影響。LME銅$100変動で±¥25億",
    "gold": "住友鉱山(5713)の副産物利益に影響。金$100/ozで±¥80億",
    "wti": "INPEX(1605)に影響。原油$1変動で±¥50億",
    "brent": "INPEX(1605)に影響。原油$1変動で±¥50億",
    "usdjpy": "INPEX/日本製鉄/住友鉱山に影響。1円変動で各社±¥15-30億",
}

SHORT_JA: dict[str, str] = {
    "copper": "銅",
    "gold": "金",
    "wti": "WTI原油",
    "brent": "ブレント原油",
    "usdjpy": "ドル円",
}


def price_alert(change_pct: float) -> str:
    if change_pct >= 3:
        return "⚠️ 急騰"
    if change_pct <= -3:
        return "⚠️ 急落"
    if 1 <= change_pct < 3:
        return "📈 上昇"
    if -3 < change_pct <= -1:
        return "📉 下落"
    return "→ 横ばい"


def trend_alert(ma20: float, ma60: float) -> str:
    if ma20 > ma60:
        return "🔼 上昇トレンド（MA20>MA60）"
    if ma20 < ma60:
        return "🔽 下降トレンド（MA20<MA60）"
    return "↔️ トレンド中立（MA20=MA60）"


def severity(change_pct: float) -> str:
    a = abs(change_pct)
    if a >= 3:
        return "high"
    if a >= 1:
        return "medium"
    return "low"


def trend_word(ma20: float, ma60: float) -> str:
    if ma20 > ma60:
        return "上昇トレンド"
    if ma20 < ma60:
        return "下降トレンド"
    return "レンジ"


def movement_word(change_pct: float) -> str:
    if abs(change_pct) < 0.05:
        return "横ばい"
    if change_pct > 0:
        return f"{change_pct:.2f}%上昇"
    return f"{abs(change_pct):.2f}%下落"


def build_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "コモディティデータなし。"
    parts: list[str] = []
    for r in rows:
        key = str(r["commodity"])
        label = SHORT_JA.get(key, str(r.get("name", key)))
        ch = float(r["change_pct"])
        ma20 = float(r["ma20"])
        ma60 = float(r["ma60"])
        tw = trend_word(ma20, ma60)
        parts.append(f"{label}は{movement_word(ch)}、{tw}")
    return "。".join(parts) + "。"


def main() -> None:
    if not PRICES_FILE.is_file():
        raise SystemExit(f"not found: {PRICES_FILE}")

    with PRICES_FILE.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    commodities: dict[str, Any] = data.get("commodities") or {}
    alerts: list[dict[str, Any]] = []
    rows_for_summary: list[dict[str, Any]] = []

    for key in COMMODITY_ORDER:
        c = commodities.get(key)
        if not isinstance(c, dict) or c.get("error"):
            continue

        change_pct = float(c["change_pct"])
        ma20 = float(c["ma20"])
        ma60 = float(c["ma60"])
        current = c["current"]

        row = {
            "commodity": key,
            "name": c.get("name", key),
            "current": current,
            "change_pct": round(change_pct, 2),
            "price_alert": price_alert(change_pct),
            "trend": trend_alert(ma20, ma60),
            "impact": IMPACT.get(key, ""),
            "severity": severity(change_pct),
            "ma20": ma20,
            "ma60": ma60,
        }
        alerts.append(
            {
                "commodity": row["commodity"],
                "name": row["name"],
                "current": row["current"],
                "change_pct": row["change_pct"],
                "price_alert": row["price_alert"],
                "trend": row["trend"],
                "impact": row["impact"],
                "severity": row["severity"],
            }
        )
        rows_for_summary.append(row)

    updated = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")

    payload = {
        "updated": updated,
        "alerts": alerts,
        "summary": build_summary(rows_for_summary),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
