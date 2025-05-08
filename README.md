# ChangeAlert-Detector

## 📋 プロジェクト概要

本プロジェクト「ChangeAlert-Detector」は、指定したWebサイトの変更を自動監視し、変更があった場合に即座に通知するシステムです。マーケティング部門による競合分析、開発チームによるAPI仕様変更の検知、運用チームによるサイト安定性の監視など、様々なビジネスシーンで活用できます。

主な機能は以下の通りです：
- 複数サイトの並行監視（URLごとに監視頻度を柔軟に設定可能）
- インテリジェントな変更検出（単純なハッシュ比較と詳細な差分抽出）
- 変更発生時のスクリーンショット自動取得
- 複数通知チャネル対応（メール/Slack）
- 時系列での変更履歴の可視化と分析

# 🛠️ ツリー構成

```
ChangeAlert-Detector/
│
├── config/
│   ├── settings.json            # 設定ファイル（監視間隔、開始日、終了日など）
│   ├── urls.csv                 # 監視対象URLリスト（CSV）
│   └── @env                     # 環境変数ファイル（SMTP設定など - 使用時に@を.に変更）
│
├── reports/
│   ├── 20250508/                # 日付別フォルダ
│   │   ├── CSV/
│   │   │   └── report_20250508040000.csv   # 監視結果CSV
│   │   └── PICTURE/
│   │       ├── screenshot_20250508040015.png  # 変更検出時のスクリーンショット
│   │       ├── timeline_20250508040050.png    # 変更頻度の時系列グラフ
│   │       └── url_changes_20250508040055.png # URL別変更回数グラフ
│   └── ...                      # 他の日付ディレクトリ
│
├── logs/
│   ├── Execution_logFolder/     # 実行ログフォルダ（loguruで出力）
│   │   └── 20250508.log         # 実行ログ（同日分のログは追記）
│   ├── log_json/                # JSONログフォルダ
│   │   └── 20250508.json        # ログのJSON形式
│   └── log.json                 # 追加のJSONログファイル
│
├── data/                        # 監視処理で自動生成されるデータフォルダ
│   └── history/                 # 監視履歴データ保存フォルダ（実行時に自動生成）
│       ├── a1b2c3d4e5.json      # URL毎の監視履歴（ハッシュ化したファイル名）
│       └── ...                  # 他のURL監視履歴
│
├── src/
│   ├── __init__.py              # 初期化ファイル
│   ├── monitor.py               # メインの監視ロジック
│   ├── utils.py                 # ヘルパー関数（差分検出、ハッシュ化など）
│   ├── notifier.py              # 通知（メール、Slackなど）関連
│   ├── visualizer.py            # 視覚化（グラフ生成）
│   ├── screenshot.py            # スクリーンショット取得（playwright利用）
│   └── logger.py                # ログ関連のユーティリティ
│
├── .gitignore                   # Git除外ファイル設定
├── requirements.txt             # 必要なライブラリのリスト
├── run_monitor.bat              # バッチファイル（監視ツール実行用）
└── README.md                    # プロジェクト概要説明
```

**重要事項**:
1. 環境変数ファイル `@env` は、使用時に `@` を `.` に変更して `.env` として利用してください。これは機密情報を含むファイルをGitで管理しないための対策です。

2. `data/history/` ディレクトリは、ツールの初回実行時に自動的に生成されます。このディレクトリには、各監視対象URLの過去の状態（ハッシュ値とコンテンツ）が保存され、変更検出に使用されます。

3. `logs/log.json` は監視ツール実行時に生成される追加のログファイルです。

## 🛠️ 使用技術

- **Python 3.8+**: コアアプリケーションの実装言語
- **Playwright**: ヘッドレスブラウザを活用した高品質なスクリーンショット取得
- **BeautifulSoup4**: HTML解析による効率的な差分検出
- **Pandas/Matplotlib/Seaborn**: データ処理・視覚化
- **Loguru**: 高度な構造化ログ機能
- **Requests**: HTTP通信
- **asyncio**: 非同期処理によるパフォーマンス最適化
- **dotenv**: 環境変数による安全な設定管理
- **Windows Task Scheduler**: 定期実行の自動化（運用環境）

## 📊 処理フロー

```
┌──────────────────────────┐       ┌──────────────────────────┐       ┌──────────────────────────┐
│                          │       │                          │       │                          │
│    設定読込・初期化       ├──────▶│    Webサイト監視処理     ├──────▶│    変更検出時の処理       │
│                          │       │                          │       │                          │
└──────────────────────────┘       └──────────────────────────┘       └──────────────┬───────────┘
                                                                                     │
                                    ┌──────────────────────────┐                     │
                                    │                          │                     │
                                    │    レポート・グラフ生成   │◀────────────────────┤
                                    │                          │                     │
                                    └──────────────┬───────────┘                     │
                                                   │                                 │
                                                   │           ┌──────────────────────────┐
                                                   │           │                          │
                                                   └──────────▶│    通知送信（メール/Slack）│◀───┘
                                                               │                          │
                                                               └──────────────────────────┘
```

詳細ステップ：

1. **設定読込・初期化**
   - settings.jsonから監視設定を読込
   - urls.csvから監視対象URLリストを読込
   - .envファイルから通知設定を読込
   - ロギングシステムの初期化

2. **Webサイト監視処理**
   - 各URLに対してコンテンツを取得
   - 前回の状態とのハッシュ比較
   - 差分検出アルゴリズムの実行

3. **変更検出時の処理**
   - 変更内容の詳細な分析
   - Playwrightによるスクリーンショット取得
   - 変更データのストレージへの保存

4. **レポート・グラフ生成**
   - CSVレポートの生成
   - 時系列変更グラフの生成
   - URL別の変更頻度分析

5. **通知送信**
   - メール通知（変更詳細とスクリーンショット添付）
   - Slack通知（Webhookを使用）

## 💡 特徴・工夫した点

### 1. パフォーマンスと拡張性の最適化

- **非同期処理の活用**: `asyncio`と`playwright`の非同期APIを組み合わせ、複数サイトの並行監視を実現。監視サイト数が増えても線形的なパフォーマンス劣化を防止
- **モジュール化アーキテクチャ**: 機能ごとに明確に分離されたモジュール構成により、新機能の追加や既存機能の拡張が容易
- **設定駆動型設計**: コードを変更せずに設定ファイルの調整だけで動作をカスタマイズ可能

```
# 設定例：モニタリング間隔とURLごとの監視頻度の違い
- settings.json: interval=5（デフォルト5分間隔）
- urls.csv: check_frequency=60（特定URLは1時間間隔）
```

### 2. インテリジェントな差分検出

- **2段階差分検出アルゴリズム**:
  1. SHA-256ハッシュによる高速な変更有無の事前判定
  2. 変更検出時のみBeautifulSoupによる詳細な差分抽出（処理効率化）
- **ノイズ除去機能**: 日時表示やカウンターなど、意味のない変更を自動的に除外
- **DOM構造解析**: 純粋なテキスト比較ではなく、HTML構造を考慮した本質的な変更検出

### 3. 実用的なロギングと例外処理

- **構造化ログ**: Loguruを活用した高度なログ管理
  - テキスト形式（人間可読）とJSON形式（機械処理用）の同時出力
  - ログレベルによる色分け表示でデバッグ効率向上
- **堅牢な例外処理**: 予期せぬエラーが全体の処理を停止させないよう設計
  - 各URLの監視は独立して実行され、1つのURLの失敗が他に影響しない
  - ネットワークエラーや一時的な障害に対する適切なリトライ機構

## 🚀 セットアップ手順

### 前提条件
- Python 3.8以上
- pipパッケージマネージャー
- Windowsの場合はPowerShellかコマンドプロンプト

### インストール手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/yourusername/ChangeAlert-Detector.git
cd ChangeAlert-Detector

# 2. 仮想環境の作成と有効化（任意だが推奨）
python -m venv venv
# Windowsの場合:
venv\Scripts\activate
# macOS/Linuxの場合:
source venv/bin/activate

# 3. 依存パッケージのインストール
pip install -r requirements.txt

# 4. Playwrightブラウザのインストール
python -m playwright install chromium

# 5. 設定ファイルの準備
# 設定ファイルのテンプレートをコピー
cp config/settings.json.example config/settings.json
cp config/urls.csv.example config/urls.csv
cp config/.env.example config/.env

# 6. 設定ファイルを編集（各自の環境に合わせて）
# お好みのエディタで編集してください
```

### 動作確認

```bash
# 手動実行（Windows）
run_monitor.bat

# または（クロスプラットフォーム）
python -m src.monitor
```

実行後、`reports/YYYYMMDD/`ディレクトリに結果が出力されます。

## 💻 実運用例

### ユースケース1: 競合サイト監視

マーケティング部門が競合他社のウェブサイトを監視し、価格変更や新製品の発表などを即座に検知するシナリオ。

```
# urls.csv設定例
url,name,check_frequency,notification
https://competitor1.com/products,競合A社製品ページ,60,true
https://competitor2.com/pricing,競合B社価格ページ,120,true
```

### ユースケース2: A/Bテスト監視

開発チームがA/Bテストの各バージョンを監視し、意図しない変更や問題を検知するシナリオ。

```
# A/Bテスト用設定例
url,name,check_frequency,notification
https://example.com/test-A,Aバージョン,5,true
https://example.com/test-B,Bバージョン,5,true
```

### ユースケース3: API仕様変更検知

外部APIの仕様ドキュメントを監視し、変更があった場合に開発チームに通知するシナリオ。

```
# API監視設定例
url,name,check_frequency,notification
https://api.example.com/docs,API仕様書,1440,true
```

## 📈 出力結果

監視実行後、以下の結果ファイルが生成されます：

1. **CSVレポート**:
   - 場所: `reports/YYYYMMDD/CSV/report_YYYYMMDDHHMMSS.csv`
   - 内容: URLごとの監視結果（タイムスタンプ、変更の有無、ステータスコードなど）

2. **グラフ画像**:
   - 場所: `reports/YYYYMMDD/PICTURE/timeline_YYYYMMDDHHMMSS.png`
   - 内容: 変更頻度の時系列グラフや、URL別の変更回数バーチャートなど

3. **スクリーンショット**:
   - 場所: `reports/YYYYMMDD/PICTURE/screenshot_YYYYMMDDHHMMSS.png`
   - 内容: 変更が検出されたページのスクリーンショット

4. **ログファイル**:
   - 場所: `logs/Execution_logFolder/YYYYMMDD.log`（テキスト形式）
   - 場所: `logs/log_json/YYYYMMDD.json`（JSON形式）
   - 内容: 実行ログ（処理内容、エラー情報など）

## 🔧 今後の展望

1. **機械学習による変更重要度判定**
   - 検出した変更の重要度を自動判定し、重要な変更のみを通知するフィルタリング機能

2. **差分表示の強化**
   - 変更前後のビジュアル差分比較機能
   - 画像認識による視覚的変更の検出

3. **監視対象の拡張**
   - PDFファイルやAPI応答など、HTML以外のコンテンツ監視対応
   - JavaScript実行後のDOM状態監視（SPA対応強化）

4. **クロスプラットフォーム対応**
   - Linux/Mac対応とDockerコンテナ化
   - クラウドサービスとしての提供（SaaS化）
