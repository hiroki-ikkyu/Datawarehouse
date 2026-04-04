# Ikkyu Capital — AI Investment Firm

素材セクター特化のAI投資分析基盤。データ取得・分析・レポート生成を自動化。

## フォルダ構成

```
ikkyu-capital/
├── data/
│   └── sentiment/
│       ├── fear-greed.json
│       └── crypto-fear-greed.json
├── economists/
│   ├── sentiment/
│   ├── commodities/
│   ├── fx/
│   └── china-macro/
├── analysts/
│   └── materials/
│       ├── spreads/
│       ├── cycles/
│       └── profiles/
├── quants/
│   ├── signals/
│   └── backtests/
├── portfolio-mgmt/
│   ├── long-only/
│   ├── long-short/
│   ├── market-neutral/
│   └── high-dividend/
├── risk-mgmt/
│   ├── alerts/
│   └── sensitivity/
├── public-relations/
│   ├── morning-brief/
│   └── earnings-flash/
├── infrastructure/
│   ├── config/
│   ├── templates/
│   └── scripts/
│       ├── fetch_fear_greed.py
│       └── fetch_crypto_fear_greed.py
├── .github/
│   └── workflows/
│       └── daily-update.yml
└── README.md
```
