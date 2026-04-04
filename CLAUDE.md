# CLAUDE.md — Ikkyu Capital

> このファイルはClaude Code / Cursorが毎回読み込む「記憶」です。
> Ikkyu Capitalの設計思想、分析フレームワーク、技術ルールが書かれています。

## 🏛 Ikkyu Capital とは

Hiroki（素材セクター バイサイドアナリスト、2025年4月〜）が構築する
**AI-Powered One-Man Investment Firm**。

- **7部門・23エージェント**がデータ取得→分析→コメント生成→表示を自動化
- **4ファンド戦略**: Long Only / Long Short / Market Neutral / High Dividend
- **3層カバレッジ**: L1担当45銘柄 + L2海外~20社 + L3国内中小型~15社（計80社）
- **月額コスト**: ~$45（Claude Code Pro $20 + Claude API ~$5 + Cursor $20）

## 👑 設計原則（必ず守ること）

1. **AIは参謀。CEOが意思決定する。** Buy/Sell/TPの最終判断は必ずHiroki
2. **Pythonが計算し、Claudeが言語化し、Hirokiが判断する。** 三権分立
3. **使ってから育てる。** 完璧を目指さず最小構成で稼働→実戦で改善
4. **PCは窓、本体はクラウド。** GitHub + OneDrive中心。PC非依存
5. **どこからでも指揮できる。** Desktop + Dispatch + CEO Portal

## 🏗 組織図 v3.0

```
👑 CEO/CIO（Hiroki）— 💻Desktop · 📱Dispatch · 🌐Portal
├── 📋 CIO室（4）— メモDrafter / Call検証 / IR準備 / FM対応
├── 📊 リサーチ部（4）— Spread / Cycle / China / Earnings
├── 🌍 海外情報部（2）— Readthrough Generator / Global Peer Monitor
├── 🔬 クオンツ部（3）— Signal Engine / Backtest Lab / Performance
├── 📈 運用部（5）— Portfolio Constructor / Exposure / Fund Perf / Rebalance / Paper PF
├── 🛡 リスク管理部（3）— Anomaly / Sensitivity / Impact Commentator
├── 📝 レポート部（4）— Morning Integrator / Earnings Flash / Scenario / Alert
└── ⚙️ IT/インフラ部（4）— Data Fetcher / Profile Manager / Portal / Orchestrator
```

## 📊 素材セクター分析フレームワーク

### スプレッド計算式
- **鉄鋼メタルスプレッド** = HRC − (鉄鉱石 × 1.6 + 原料炭 × 0.5)
- **石化スプレッド** = エチレン CFR Asia − ナフサ CFR Japan（$300が損益分岐）
- **銅製錬マージン** = TC/RC + Free Metal + 副産物 − 製造コスト
- **石油精製マージン** = 石油製品加重平均 − 原油購入価格（$5-6/bblが分岐点）

### サイクル判定（4フェーズ）
- Phase 1: 供給不足・価格上昇（在庫減少）→ 買い場
- Phase 2: 投資ラッシュ・ピーク（楽観）→ 売り場
- Phase 3: 供給過剰・価格暴落（在庫積増）→ 待ち
- Phase 4: 淘汰・投資停止（悲観ピーク）→ 次の買い場

### 決算分析テクニック
- **在庫影響除去**: 実力OP = 報告OP − 在庫評価影響（石油元売・非鉄で必須）
- **感応度**: 鉄鉱石$10→日本製鉄±¥350億、LME銅$100→住友鉱山±¥25億
- **ブリッジ**: マージン/原料/数量/為替/コスト削減の要因分解

### バリュエーション手法
- EV/EBITDA（素材の標準）、ミッドサイクルPE（サイクル調整）
- P/NAV（鉱山・E&P）、SOTP（複合企業）、コスト曲線（長期価格アンカー）
- **PERの罠**: シクリカルはPER最低時に売り、最高時に買うのが正しい

### Claude APIの5つの役割
1. **統合者** — バラバラのデータを「で、結局どうなの？」にまとめる
2. **翻訳者** — 数字→FM向け日本語ストーリーに変換
3. **比較者** — 海外決算→担当企業への差分抽出（Readthrough）
4. **検証者** — 過去のCallが当たったか外れたかの客観評価
5. **起草者** — 投資メモ・IR準備資料の初稿作成

### ルールベースコメント（Claude API不要・if文で生成）
- 鉄鉱石▲3%超 → 「⚠急落。日本製鉄に¥175億コスト改善」
- BDI 5日連続上昇 → 「📈ドライバルク市況改善」
- LME銅在庫が3ヶ月MAを下回る → 「需給タイト」

## 🇯🇵 カバレッジ銘柄（主要）

### L1 Tier 1（フルモデル・最優先）
| 銘柄 | コード | セクター |
|------|--------|----------|
| 日本製鉄 | 5401 | 鉄鋼 |
| INPEX | 1605 | E&P |
| 住友金属鉱山 | 5713 | 非鉄（鉱山+製錬）|
| ENEOS HD | 5020 | 石油精製 |
| フジクラ | 5803 | 線材・ケーブル |
| 商船三井 | 9104 | 海運 |

### L2 海外リファレンス（決算Readthrough用）
BHP AU, RIO AU, VALE US, FCX US, MT NA, GLW US, PRY IM, MAERSKB DC, IP US, SUZB3 BZ, ALB US

### L3 国内中小型
東京製鐵(5423), 大和工業(5444), 大同特殊鋼(5471), NEG(5214), DOWA(5714), UACJ(5741)

## 💻 技術ルール

### PWA設計ルール（CEO Portal・全アプリ共通）
- フォント: DM Sans + Noto Sans JP
- 背景: #fff / #f5f5f7（ライトモード Apple-minimal）
- border-radius: 16px
- `env(safe-area-inset-bottom)` for iPhone safe area
- **timeZone: "Asia/Tokyo"** 必須。toISOString() 禁止
- SharedStore: `shared:` prefix の localStorage で他アプリと連携
- ダークモードは CEO Portal の Morning Brief のみ

### GitHub
- ユーザー名: `hiroki-ikkyu`
- リポジトリ群: ceo-portal, datawarehouse, ikkyu-capital, routine-tracker 等
- GitHub Actions: cron `0 21 * * *`（UTC 21:00 = JST 06:00）で毎朝実行
- GitHub Pages でPWAホスティング

### 開発環境
- PC: DAIV Z5-KK（i7-9700/32GB/Win11）
- Claude Code: `--dangerously-skip-permissions` で全自動実行
- Cursor: メインIDE。Settings Sync ON
- Python: venv推奨。pandas, numpy, requests, anthropic
- OneDrive: Excel財務モデル保存先

### データソース
- **今（Phase 1）**: J-Quants API（日本株）+ Trading Economics/FRED（コモディティ無料）
- **6月〜（Phase 2）**: Bloomberg Anywhere BLPAPI 追加

### コスト
- Claude Code Pro: $20/月
- Claude API (Sonnet 4.6): ~$5/月（従量）
- Cursor: $20/月
- J-Quants: 無料プラン
- Bloomberg: 会社負担

## 📁 リポジトリ構造

```
ikkyu-capital/
├── CLAUDE.md                  ← このファイル
├── docs/
│   ├── architecture.md        ← 組織図v3.0詳細
│   ├── sector-knowledge/
│   │   ├── spreads.md         ← スプレッド計算式
│   │   ├── cycles.md          ← サイクルフレームワーク
│   │   ├── china-data.md      ← 中国データの読み方
│   │   ├── valuation.md       ← バリュエーション手法
│   │   ├── signals.md         ← バックテスト済み8シグナル
│   │   └── coverage.md        ← 80社の一覧と分類
│   ├── agent-specs/
│   │   ├── data-fetcher.md
│   │   ├── spread-analyst.md
│   │   ├── signal-engine.md
│   │   └── ...各エージェント仕様
│   ├── dev-rules.md           ← PWA技術ルール
│   └── bloomberg-tickers.md   ← ティッカー完全リファレンス
├── src/
│   ├── fetcher/               ← Data Fetcher
│   ├── spread/                ← Spread Analyst
│   ├── signals/               ← Signal Engine
│   ├── risk/                  ← Risk Monitor
│   ├── comment/               ← Alert Formatter + Claude API
│   └── portal/                ← CEO Portal PWA
├── data/
│   ├── profiles/              ← 会社プロファイルJSON
│   ├── daily/                 ← 日次取得データ
│   └── signals/               ← シグナル出力
├── tests/
└── .github/
    └── workflows/
        └── daily-pipeline.yml ← 毎朝6:00 JSTの自動実行
```

## 🚀 実装フェーズ

### Phase 1（今・4-5月）Bloombergなし
- [ ] Data Fetcher v1（J-Quants + 無料コモディティ）
- [ ] Spread Analyst v1（鉄鋼メタルスプレッド概算）
- [ ] CEO Portal拡張（Morning Brief + Spread Dashboard）
- [ ] ルールベースアラート/コメント
- [ ] Claude APIコメント v1
- [ ] 会社プロファイル 6社（Tier 1）

### Phase 2（6月〜）Bloomberg接続
- [ ] BLPAPI切替
- [ ] 4スプレッド全て精緻化
- [ ] Cycle Analyst v1
- [ ] Risk Monitor v1
- [ ] フルMorning Brief

### Phase 3（7-9月）精緻化
- [ ] China Watcher
- [ ] Earnings Tracker
- [ ] 8シグナル全実装
- [ ] 感応度自動更新
- [ ] Memo Drafter v1

### Phase 4（10-12月）高度化
- [ ] Backtest Lab
- [ ] Performance Tracker
- [ ] 年間振り返り
- [ ] 来年計画
