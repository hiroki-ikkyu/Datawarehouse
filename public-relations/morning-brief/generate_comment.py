"""
Claude API で Morning Brief「Today's Call」コメントを生成し、
data/morning-brief/todays-call.json に保存する。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMODITIES_FILE = REPO_ROOT / "data" / "commodities" / "daily-prices.json"
ALERTS_FILE = REPO_ROOT / "data" / "alerts" / "daily-alerts.json"
SPREADS_FILE = REPO_ROOT / "data" / "spreads" / "daily-spreads.json"
OUT_DIR = REPO_ROOT / "data" / "morning-brief"
OUT_FILE = OUT_DIR / "todays-call.json"

COMMODITY_ORDER = ["copper", "gold", "wti", "brent", "usdjpy"]
MODEL = "claude-sonnet-4-20250514"

NO_API_KEY_MSG = "APIキー未設定。環境変数ANTHROPIC_API_KEYを確認してください"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def format_commodities_summary(data: dict[str, Any]) -> str:
    lines: list[str] = []
    com = data.get("commodities") or {}
    for key in COMMODITY_ORDER:
        c = com.get(key)
        if not isinstance(c, dict) or c.get("error"):
            continue
        unit = c.get("unit", "")
        lines.append(
            f"- {c.get('name', key)} ({key}): 現在 {c['current']} {unit}, "
            f"前日比 {c['change_pct']}%, MA20={c.get('ma20')}, MA60={c.get('ma60')}"
        )
    return "\n".join(lines) if lines else "(コモディティデータなし)"


def format_alerts_summary(data: dict[str, Any]) -> str:
    parts: list[str] = []
    summ = data.get("summary")
    if summ:
        parts.append(f"概要: {summ}")
    for a in data.get("alerts") or []:
        if not isinstance(a, dict):
            continue
        parts.append(
            f"- [{a.get('severity')}] {a.get('name')} ({a.get('commodity')}): "
            f"{a.get('change_pct')}%, {a.get('price_alert')}, {a.get('trend')}, "
            f"影響: {a.get('impact', '')}"
        )
    return "\n".join(parts) if parts else "(アラートなし)"


def format_spreads_summary(data: dict[str, Any]) -> str:
    lines: list[str] = []
    sp = data.get("spreads") or {}
    bw = sp.get("brent_wti")
    if isinstance(bw, dict):
        lines.append(
            f"Brent-WTI: 現在 {bw.get('current')} {bw.get('unit', '')}, "
            f"前日スプレッド {bw.get('prev')}, 変化 {bw.get('change')}"
        )
    gcr = sp.get("gold_copper_ratio")
    if isinstance(gcr, dict):
        lines.append(
            f"Gold/Copper比率: 現在 {gcr.get('current')}, MA20 {gcr.get('ma20')}, "
            f"{gcr.get('interpretation', '')}"
        )
    ms = data.get("ma_signals") or {}
    if ms:
        lines.append("MAシグナル:")
        for k, v in ms.items():
            if not isinstance(v, dict):
                continue
            sig = v.get("cross_signal")
            sig_s = sig if sig else "—"
            lines.append(
                f"  - {k}: MA20>MA60={v.get('ma20_above_ma60')}, {sig_s}"
            )
    return "\n".join(lines) if lines else "(スプレッドデータなし)"


def count_alert_severities(alerts_data: dict[str, Any]) -> tuple[int, int]:
    hi = md = 0
    for a in alerts_data.get("alerts") or []:
        if not isinstance(a, dict):
            continue
        s = a.get("severity")
        if s == "high":
            hi += 1
        elif s == "medium":
            md += 1
    return hi, md


def build_prompt(
    commodities_summary: str,
    alerts_summary: str,
    spreads_summary: str,
) -> str:
    return f"""あなたは素材セクター（鉄鋼・非鉄・石油・ガラス・紙・海運）を担当するバイサイドアナリストの
AIアシスタントです。毎朝のMorning Briefの「Today's Call」を1段落（3-5文）で生成してください。

ルール:
- 数字を必ず含める（変化率、価格水準）
- 担当企業への影響を含める（日本製鉄、INPEX、住友鉱山、ENEOS、フジクラ、商船三井）
- 「なぜ上がったか」は推測しない。「何が起きて、何に影響するか」だけ述べる
- 日本語で書く
- 最も重要な変動を最初に述べる（severity highがあればそれ）

本日の市況データ:
{commodities_summary}

アラート:
{alerts_summary}

スプレッド・シグナル:
{spreads_summary}
"""


def call_claude(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=MODEL,
        max_tokens=500,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    block = msg.content[0]
    if block.type != "text":
        raise RuntimeError("unexpected response block type")
    return block.text.strip()


def main() -> None:
    commodities = _load_json(COMMODITIES_FILE)
    alerts = _load_json(ALERTS_FILE)
    spreads = _load_json(SPREADS_FILE)

    commodities_summary = format_commodities_summary(commodities)
    alerts_summary = format_alerts_summary(alerts)
    spreads_summary = format_spreads_summary(spreads)

    high_n, med_n = count_alert_severities(alerts)

    data_used = {
        "commodities": COMMODITY_ORDER.copy(),
        "high_alerts": high_n,
        "medium_alerts": med_n,
    }

    updated = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        todays_call = NO_API_KEY_MSG
    else:
        try:
            prompt = build_prompt(commodities_summary, alerts_summary, spreads_summary)
            todays_call = call_claude(prompt)
        except Exception:
            todays_call = (alerts.get("summary") or "").strip()

    payload = {
        "updated": updated,
        "todays_call": todays_call,
        "data_used": data_used,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open(mode="w", encoding="utf-8") as f:
        json.dump(
            payload,
            f,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    main()
