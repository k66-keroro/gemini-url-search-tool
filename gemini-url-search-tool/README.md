# Gemini URL Search Tool

🔍 Gemini APIのURL検索機能を活用したWeb情報収集ツール

## 概要

このツールは、Google Gemini APIを使用してキーワード検索からURL選択、コンテンツ要約までを自動化する独立したWebアプリケーションです。研究、開発、情報収集の効率化を目的として設計されています。

### 主な用途
1. **フリーワード検索**: 一般的なキーワードでのWeb情報収集
2. **部品仕様検索**: メーカー名と品番による技術文書の効率的な収集
3. **コンテンツ分析**: 検索結果の自動要約と構造化
4. **情報管理**: 検索履歴と結果の保存・管理

## 主要機能

### 🔍 検索機能
- **フリーワード検索**: キーワードやフレーズでの関連URL検索
- **部品仕様検索**: メーカー名と品番による専門的な検索
- **インテリジェント結果フィルタリング**: 関連性と品質による自動ランキング
- **重複除去**: 同一コンテンツの自動検出と除去

### 📄 コンテンツ処理
- **自動要約**: 選択したURLのコンテンツを構造化して要約
- **技術仕様抽出**: 部品仕様書からの主要パラメータ抽出
- **大容量コンテンツ対応**: チャンク分割による効率的な処理
- **多言語対応**: 日本語・英語コンテンツの処理

### 💾 データ管理
- **検索履歴**: 全ての検索クエリと結果の保存
- **コンテンツ保存**: 有用な情報のローカルデータベース保存
- **メタデータ管理**: タイムスタンプ、カテゴリ、キーワードの自動付与
- **評価システム**: 検索結果の有用性評価とフィードバック

### 📊 分析・評価
- **実用性評価**: 検索精度と効果の測定・分析
- **パフォーマンス監視**: 検索時間、成功率の追跡
- **使用統計**: 検索パターンと改善提案の生成
- **ダッシュボード**: 視覚的な統計情報の表示

## システム要件

- **Python**: 3.8以上
- **OS**: Windows, macOS, Linux
- **メモリ**: 最小512MB、推奨1GB以上
- **ストレージ**: 最小100MB（データベース用）
- **ネットワーク**: インターネット接続（Gemini API用）

## インストール

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd gemini-url-search-tool
```

### 2. Python仮想環境の作成（推奨）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. 必要なディレクトリの作成
```bash
mkdir -p data logs
```

## 設定

### 1. 環境変数の設定
```bash
cp .env.example .env
```

`.env`ファイルを編集して以下を設定：
```env
# 必須: Gemini API キー
GEMINI_API_KEY=your_gemini_api_key_here

# オプション設定
DEBUG=false
LOG_LEVEL=INFO
DATABASE_PATH=data/search_results.db
ENABLE_CACHE=true
CACHE_DURATION_HOURS=24
```

### 2. Gemini API キーの取得
1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたAPIキーを`.env`ファイルに設定

### 3. 設定ファイルのカスタマイズ
`config.json`で詳細設定を調整可能：

```json
{
  "gemini": {
    "models": ["gemini-2.0-flash-exp", "gemini-1.5-flash"],
    "max_retries": 3,
    "timeout": 30
  },
  "search": {
    "max_results": 10,
    "enable_caching": true,
    "cache_duration_hours": 24
  },
  "content": {
    "max_content_size": 1048576,
    "summary_max_length": 1000
  }
}
```

## 使用方法

### 基本的な使用手順

1. **アプリケーションの起動**
```bash
streamlit run main.py
```

2. **ブラウザでアクセス**
   - URL: http://localhost:8501
   - 自動的にブラウザが開きます

3. **検索の実行**
   - 検索タイプを選択（一般検索 or 部品検索）
   - キーワードまたはメーカー名・品番を入力
   - 「検索実行」ボタンをクリック

4. **結果の確認**
   - 検索結果一覧から興味のあるURLを選択
   - コンテンツの要約を確認
   - 必要に応じて結果を保存・評価

### 検索タイプ別の使用例

#### フリーワード検索
```
検索キーワード: "Python 機械学習 入門"
→ Python機械学習に関する記事、チュートリアル、ドキュメントを検索
```

#### 部品仕様検索
```
メーカー名: "Arduino"
品番: "UNO R3"
→ Arduino UNO R3の公式仕様書、データシートを優先的に検索
```

### 高度な機能

#### 検索結果の管理
- **保存**: 有用な結果を「保存」ボタンでローカルに保存
- **評価**: 5段階評価で結果の有用性を記録
- **履歴**: サイドバーから過去の検索履歴を確認

#### 設定のカスタマイズ
- **表示設定**: 結果表示数、要約の長さ
- **検索設定**: タイムアウト時間、リトライ回数
- **キャッシュ設定**: キャッシュの有効期間

## API ドキュメント

### 主要クラスとメソッド

#### SearchService
```python
from src.core.search_service import SearchService

# 初期化
search_service = SearchService(gemini_client, search_repository)

# 一般検索
results = await search_service.search_general("Python tutorial")

# 部品検索
results = await search_service.search_component_specs("Arduino", "UNO R3")
```

#### ContentService
```python
from src.core.content_service import ContentService

# 初期化
content_service = ContentService(gemini_client)

# コンテンツ取得と分析
analysis = await content_service.analyze_url("https://example.com")

# 要約生成
summary = await content_service.generate_summary(content, focus_areas=["技術仕様"])
```

#### GeminiClient
```python
from src.core.gemini_client import GeminiClient

# 初期化
client = GeminiClient(api_key="your_api_key")

# URL検索
search_results = await client.search_urls("search query", SearchType.GENERAL)

# コンテンツ分析
analysis = await client.analyze_content("https://example.com")
```

### データモデル

#### SearchResult
```python
@dataclass
class SearchResult:
    url: str                    # 検索結果のURL
    title: str                  # ページタイトル
    description: str            # 説明文
    rank: int                   # ランキング順位
    is_official: bool = False   # 公式ソースかどうか
    confidence_score: float = 0.0  # 信頼度スコア
```

#### ContentAnalysis
```python
@dataclass
class ContentAnalysis:
    url: str                    # 分析対象URL
    content_type: str           # コンテンツタイプ
    summary: str                # 要約文
    key_points: List[str]       # 主要ポイント
    technical_specs: Dict[str, Any]  # 技術仕様
    extraction_time: float      # 処理時間
    content_size: int           # コンテンツサイズ
```

### 使用例

#### 基本的な検索フロー
```python
import asyncio
from src.core.gemini_client import GeminiClient
from src.core.search_service import SearchService
from src.models.repository import SearchRepository

async def search_example():
    # クライアント初期化
    client = GeminiClient(api_key="your_api_key")
    repository = SearchRepository("data/search_results.db")
    search_service = SearchService(client, repository)
    
    # 検索実行
    results = await search_service.search_general("Python tutorial")
    
    # 結果の表示
    for result in results:
        print(f"Title: {result.title}")
        print(f"URL: {result.url}")
        print(f"Description: {result.description}")
        print("---")

# 実行
asyncio.run(search_example())
```

#### コンテンツ分析の例
```python
from src.core.content_service import ContentService

async def analyze_example():
    client = GeminiClient(api_key="your_api_key")
    content_service = ContentService(client)
    
    # URL分析
    analysis = await content_service.analyze_url("https://example.com")
    
    print(f"Summary: {analysis.summary}")
    print(f"Key Points: {analysis.key_points}")
    print(f"Technical Specs: {analysis.technical_specs}")

asyncio.run(analyze_example())
```

## プロジェクト構造

```
gemini-url-search-tool/
├── README.md                   # このファイル
├── requirements.txt            # Python依存関係
├── config.json                 # アプリケーション設定
├── .env.example               # 環境変数テンプレート
├── main.py                    # メインエントリーポイント
├── src/                       # ソースコード
│   ├── core/                  # コア機能
│   │   ├── gemini_client.py   # Gemini API クライアント
│   │   ├── search_service.py  # 検索サービス
│   │   ├── content_service.py # コンテンツ処理
│   │   └── storage_service.py # データ保存
│   ├── ui/                    # ユーザーインターフェース
│   │   ├── search_app.py      # メインアプリ
│   │   └── components/        # UIコンポーネント
│   ├── models/                # データモデル
│   │   ├── data_models.py     # データクラス定義
│   │   └── database.py        # データベース操作
│   ├── utils/                 # ユーティリティ
│   │   ├── error_handler.py   # エラーハンドリング
│   │   └── validators.py      # バリデーション
│   └── evaluation/            # 評価・分析
│       └── evaluation_service.py
├── data/                      # データファイル
│   ├── search_results.db      # SQLiteデータベース
│   └── cache/                 # キャッシュファイル
├── logs/                      # ログファイル
│   └── app.log
└── tests/                     # テストファイル
    ├── test_gemini_client.py
    ├── test_search_service.py
    └── test_integration.py
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. API認証エラー
**症状**: `Authentication failed` または `Invalid API key`
```
Error: Authentication failed with Gemini API
```

**解決方法**:
1. `.env`ファイルでAPIキーを確認
2. [Google AI Studio](https://makersuite.google.com/app/apikey)で新しいキーを生成
3. APIキーに余分なスペースや改行がないか確認
4. 環境変数が正しく読み込まれているか確認:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"
```

#### 2. レート制限エラー
**症状**: `Rate limit exceeded` または検索が頻繁に失敗
```
Error: Rate limit exceeded. Please try again later.
```

**解決方法**:
1. `config.json`でリトライ設定を調整:
```json
{
  "gemini": {
    "max_retries": 5,
    "rate_limit_delay": 2.0
  }
}
```
2. 検索頻度を下げる
3. キャッシュ機能を有効にして重複リクエストを避ける

#### 3. データベース接続エラー
**症状**: `Database connection failed` または `Permission denied`
```
Error: Unable to connect to database: data/search_results.db
```

**解決方法**:
1. `data`ディレクトリの作成:
```bash
mkdir -p data
```
2. ファイル権限の確認:
```bash
# Windows
icacls data /grant %USERNAME%:F

# macOS/Linux
chmod 755 data
```
3. データベースファイルの再作成:
```bash
rm data/search_results.db  # 既存ファイルを削除
python -c "from src.models.database import DatabaseManager; DatabaseManager('data/search_results.db').initialize_database()"
```

#### 4. Streamlitアプリが起動しない
**症状**: `ModuleNotFoundError` または `ImportError`
```
ModuleNotFoundError: No module named 'src'
```

**解決方法**:
1. 正しいディレクトリで実行しているか確認:
```bash
pwd  # gemini-url-search-tool ディレクトリにいることを確認
```
2. 依存関係の再インストール:
```bash
pip install -r requirements.txt
```
3. Python パスの確認:
```bash
python -c "import sys; print(sys.path)"
```

#### 5. コンテンツ取得エラー
**症状**: `Content fetch failed` または `Timeout error`
```
Error: Failed to fetch content from URL: https://example.com
```

**解決方法**:
1. ネットワーク接続の確認
2. プロキシ設定（必要な場合）:
```env
# .envファイルに追加
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
```
3. タイムアウト設定の調整:
```json
{
  "content": {
    "extraction_timeout": 120
  }
}
```

#### 6. メモリ不足エラー
**症状**: `MemoryError` または アプリが突然終了
```
MemoryError: Unable to allocate memory
```

**解決方法**:
1. コンテンツサイズ制限の調整:
```json
{
  "content": {
    "max_content_size": 524288,
    "chunk_size": 2048
  }
}
```
2. キャッシュのクリア:
```bash
rm -rf data/cache/*
```
3. 不要なデータの削除:
```python
# データベースのクリーンアップ
from src.models.database import DatabaseManager
db = DatabaseManager('data/search_results.db')
db.cleanup_old_records(days=7)
```

### ログの確認方法

#### ログファイルの場所
- メインログ: `logs/app.log`
- エラーログ: コンソール出力

#### ログレベルの調整
`.env`ファイルで設定:
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

#### 詳細なデバッグ情報の取得
```bash
# デバッグモードで起動
DEBUG=true streamlit run main.py
```

### パフォーマンス最適化

#### 1. キャッシュの活用
```json
{
  "search": {
    "enable_caching": true,
    "cache_duration_hours": 24
  }
}
```

#### 2. データベースの最適化
```python
# 定期的なデータベースメンテナンス
from src.models.database import DatabaseManager
db = DatabaseManager('data/search_results.db')
db.vacuum()  # データベースの最適化
```

#### 3. メモリ使用量の監視
```python
# メモリ使用量の確認
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

### サポートとフィードバック

問題が解決しない場合は、以下の情報を含めてお問い合わせください：

1. **エラーメッセージ**: 完全なエラーメッセージ
2. **環境情報**: OS、Pythonバージョン
3. **設定ファイル**: `config.json`と`.env`（APIキーは除く）
4. **ログファイル**: `logs/app.log`の関連部分
5. **再現手順**: エラーが発生する具体的な手順

## 開発・カスタマイズ

### 開発環境のセットアップ
```bash
# 開発用依存関係のインストール
pip install pytest pytest-asyncio black flake8

# テストの実行
python -m pytest tests/

# コードフォーマット
black src/ tests/

# リンター実行
flake8 src/ tests/
```

### カスタム検索プロンプトの追加
`src/core/search_service.py`の`_build_search_prompt`メソッドを編集して、独自の検索プロンプトを追加できます。

### 新しいコンテンツタイプの対応
`src/core/content_service.py`の`_detect_content_type`メソッドを拡張して、新しいコンテンツタイプに対応できます。

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 更新履歴

### v1.0.0 (2024-01-XX)
- 初回リリース
- フリーワード検索機能
- 部品仕様検索機能
- コンテンツ要約機能
- 検索結果保存・管理機能
- 実用性評価機能