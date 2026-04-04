"""
日次スプレッド・比率・MAシグナル計算。
data/commodities/daily-prices.json を読み、data/spreads/daily-spreads.json に保存する。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[3]
PRICES_FILE = REPO_ROOT / "data" / "commodities" / "daily-prices.json"
OUT_DIR = REPO_ROOT / "data" / "spreads"
OUT_FILE = OUT_DIR / "daily-spreads.json"

COMMODITY_KEYS = ["copper", "gold", "wti", "brent", "usdjpy"]
COPPER_LB_TO_TON = 2204.62


def _history_to_map(hist: list[dict[str, Any]] | None) -> dict[str, float]:
    if not hist:
        return {}
    return {str(row["date"]): float(row["value"]) for row in hist if "date" in row and "value" in row}


def _sorted_values(hist: list[dict[str, Any]] | None) -> list[float]:
    m = _history_to_map(hist)
    if not m:
        return []
    dates = sorted(m.keys())
    return [m[d] for d in dates]


def rolling_mean(vals: list[float], end_i: int, window: int) -> float | None:
    if end_i < 0 or end_i >= len(vals) or end_i < window - 1:
        return None
    start = end_i - window + 1
    return sum(vals[start : end_i + 1]) / window


def cross_signal_from_history(vals: list[float], ma20_json: float, ma60_json: float) -> tuple[bool, str | None]:
    """Returns (ma20_above_ma60, cross_signal)."""
    n = len(vals)
    if n < 2:
        return (ma20_json > ma60_json, None)

    ma20_t = rolling_mean(vals, n - 1, 20)
    ma60_t = rolling_mean(vals, n - 1, 60)
    ma20_y = rolling_mean(vals, n - 2, 20)
    ma60_y = rolling_mean(vals, n - 2, 60)

    if ma20_t is None or ma60_t is None:
        return (ma20_json > ma60_json, None)

    above = ma20_t > ma60_t

    if ma20_y is not None and ma60_y is not None:
        if ma20_y < ma60_y and ma20_t > ma60_t:
            return (above, "ゴールデンクロス🔔")
        if ma20_y > ma60_y and ma20_t < ma60_t:
            return (above, "デッドクロス🔔")

    mid = (ma20_t + ma60_t) / 2.0
    if mid > 0 and abs(ma20_t - ma60_t) / mid <= 0.01:
        return (above, "クロス接近⚠️")

    return (above, None)


def brent_wti_block(b: dict[str, Any], w: dict[str, Any]) -> dict[str, Any]:
    current = float(b["current"]) - float(w["current"])
    prev = float(b["prev_close"]) - float(w["prev_close"])
    change = current - prev

    mb = _history_to_map(b.get("history"))
    mw = _history_to_map(w.get("history"))
    common = sorted(set(mb.keys()) & set(mw.keys()))
    history = [{"date": d, "value": round(mb[d] - mw[d], 2)} for d in common]

    return {
        "name": "Brent-WTI Spread",
        "unit": "$/bbl",
        "current": round(current, 2),
        "prev": round(prev, 2),
        "change": round(change, 2),
        "history": history,
    }


def gold_copper_ratio_block(g: dict[str, Any], c: dict[str, Any]) -> dict[str, Any]:
    g_cur = float(g["current"])
    c_lb = float(c["current"])
    cu_ton = c_lb * COPPER_LB_TO_TON
    ratio_current = g_cur / cu_ton if cu_ton else 0.0

    mg = _history_to_map(g.get("history"))
    mc = _history_to_map(c.get("history"))
    dates = sorted(set(mg.keys()) & set(mc.keys()))
    ratios: list[float] = []
    for d in dates:
        r = mg[d] / (mc[d] * COPPER_LB_TO_TON)
        ratios.append(r)

    if len(ratios) >= 20:
        ratio_ma20 = sum(ratios[-20:]) / 20.0
    elif ratios:
        ratio_ma20 = sum(ratios) / len(ratios)
    else:
        ratio_ma20 = ratio_current

    interpretation = "リスクオフ傾向" if ratio_current > ratio_ma20 else "リスクオン傾向"

    return {
        "name": "Gold/Copper Ratio",
        "current": round(ratio_current, 4),
        "ma20": round(ratio_ma20, 4),
        "interpretation": interpretation,
    }


def main() -> None:
    if not PRICES_FILE.is_file():
        raise SystemExit(f"not found: {PRICES_FILE}")

    with PRICES_FILE.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    commodities: dict[str, Any] = data.get("commodities") or {}

    spreads: dict[str, Any] = {}
    b = commodities.get("brent")
    w = commodities.get("wti")
    g = commodities.get("gold")
    c = commodities.get("copper")

    if (
        isinstance(b, dict)
        and isinstance(w, dict)
        and not b.get("error")
        and not w.get("error")
    ):
        spreads["brent_wti"] = brent_wti_block(b, w)

    if (
        isinstance(g, dict)
        and isinstance(c, dict)
        and not g.get("error")
        and not c.get("error")
    ):
        spreads["gold_copper_ratio"] = gold_copper_ratio_block(g, c)

    ma_signals: dict[str, Any] = {}
    for key in COMMODITY_KEYS:
        co = commodities.get(key)
        if not isinstance(co, dict) or co.get("error"):
            ma_signals[key] = {"ma20_above_ma60": False, "cross_signal": None}
            continue

        vals = _sorted_values(co.get("history"))
        ma20_j = float(co.get("ma20", 0))
        ma60_j = float(co.get("ma60", 0))
        above, sig = cross_signal_from_history(vals, ma20_j, ma60_j)
        ma_signals[key] = {"ma20_above_ma60": above, "cross_signal": sig}

    placeholder_for_bloomberg = {
        "steel_metal_spread": "Bloombergデータ待ち（6月〜）: HRC - 鉄鉱石×1.6 - 原料炭×0.5",
        "petchem_spread": "Bloombergデータ待ち: エチレン - ナフサ",
        "copper_tcrc": "Bloombergデータ待ち: TC/RC",
        "refining_margin": "Bloombergデータ待ち: 精製マージン",
    }

    updated = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")

    payload = {
        "updated": updated,
        "spreads": spreads,
        "ma_signals": ma_signals,
        "placeholder_for_bloomberg": placeholder_for_bloomberg,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
