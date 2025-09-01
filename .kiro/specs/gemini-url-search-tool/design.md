# 設計書

## 概要

Gemini APIのURL検索機能を活用したWeb情報収集ツールの設計書です。既存のプロジェクト構造に統合し、フリーワード検索と部品仕様検索の両方に対応した実用的なツールを構築します。

## アーキテクチャ

### システム構成

```
┌─────────────────────────────────────────────────────────────┐
│                    Gemini URL Search Tool                    │
├─────────────────────────────────────────────────────────────┤
│  UI Layer (Streamlit)                                       │
│  ├── 検索インターフェース                                      │
│  ├── 結果表示・選択                                           │
│  ├── コンテンツ要約表示                                        │
│  └── 評価・管理ダッシュボード                                   │
├─────────────────────────────────────────────────────────────┤
│  Service Layer                                              │
│  ├── SearchService (検索処理)                                │
│  ├── ContentService (コンテンツ取得・要約)                     │
│  ├── StorageService (結果保存・管理)                          │
│  └── EvaluationService (実用性評価)                          │
├─────────────────────────────────────────────────────────────┤
│  Core Layer                                                 │
│  ├── GeminiClient (API呼び出し)                              │
│  ├── URLParser (URL解析・検証)                               │
│  ├── ContentExtractor (コンテンツ抽出)                        │
│  └── DatabaseManager (SQLite操作)                           │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── SQLite Database (検索履歴・結果保存)                      │
│  ├── Configuration (設定管理)                                │
│  └── Cache (API結果キャッシュ)                                │
└─────────────────────────────────────────────────────────────┘
```

### 技術スタック

- **フロントエンド**: Streamlit (独立したWebアプリ)
- **バックエンド**: Python 3.8+
- **AI API**: Google Gemini API (2.5-flash, 1.5-flash)
- **データベース**: SQLite (軽量・ポータブル)
- **HTTP クライアント**: requests, aiohttp
- **データ処理**: pandas (最小限の使用)
- **設定管理**: python-dotenv, json

## コンポーネントと インターフェース

### 1. GeminiClient (コアAPI クライアント)

```python
class GeminiClient:
    def __init__(self, api_key: str, models: List[str])
    
    async def search_urls(self, query: str, search_type: SearchType) -> List[SearchResult]
    async def analyze_content(self, url: str) -> ContentAnalysis
    async def summarize_content(self, content: str, focus: str = None) -> Summary
    
    def _handle_rate_limit(self, retry_count: int) -> None
    def _validate_response(self, response: Any) -> bool
```

**主要機能:**
- Gemini APIへの非同期リクエスト処理
- レート制限とエラーハンドリング
- 複数モデルでのフォールバック機能
- レスポンス検証とパース処理

### 2. SearchService (検索処理サービス)

```python
class SearchService:
    def __init__(self, gemini_client: GeminiClient, storage: StorageService)
    
    async def search_general(self, keywords: str) -> SearchResults
    async def search_component_specs(self, manufacturer: str, part_number: str) -> SearchResults
    
    def _build_search_prompt(self, query: str, search_type: SearchType) -> str
    def _filter_results(self, results: List[SearchResult]) -> List[SearchResult]
    def _rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]
```

**検索プロンプト設計:**
- **一般検索**: "以下のキーワードに関連する有用なWebサイトのURLを検索してください: {keywords}"
- **部品仕様検索**: "メーカー「{manufacturer}」の品番「{part_number}」の公式仕様書・データシートのURLを検索してください"

### 3. ContentService (コンテンツ処理サービス)

```python
class ContentService:
    def __init__(self, gemini_client: GeminiClient)
    
    async def fetch_content(self, url: str) -> WebContent
    async def extract_key_info(self, content: WebContent, content_type: ContentType) -> ExtractedInfo
    async def generate_summary(self, content: WebContent, focus_areas: List[str]) -> Summary
    
    def _detect_content_type(self, url: str, content: str) -> ContentType
    def _clean_content(self, raw_content: str) -> str
```

**要約プロンプト設計:**
- **一般コンテンツ**: "以下のWebページ内容を要約し、主要なポイントを3-5個の箇条書きで示してください"
- **技術仕様**: "以下の技術文書から、仕様・寸法・性能パラメータを抽出し、構造化して要約してください"

### 4. StorageService (データ保存サービス)

```python
class StorageService:
    def __init__(self, db_path: str)
    
    def save_search_result(self, search: SearchRecord) -> int
    def save_content_analysis(self, analysis: ContentAnalysis) -> int
    def get_search_history(self, filters: SearchFilters) -> List[SearchRecord]
    def get_saved_content(self, content_id: int) -> ContentAnalysis
    
    def detect_duplicate(self, url: str) -> Optional[ContentAnalysis]
    def update_evaluation(self, content_id: int, rating: int, feedback: str) -> None
```

### 5. EvaluationService (評価・分析サービス)

```python
class EvaluationService:
    def __init__(self, storage: StorageService)
    
    def calculate_search_metrics(self, time_range: DateRange) -> SearchMetrics
    def analyze_query_patterns(self) -> QueryAnalysis
    def generate_effectiveness_report(self) -> EffectivenessReport
    
    def track_user_interaction(self, interaction: UserInteraction) -> None
    def get_improvement_suggestions(self) -> List[Suggestion]
```

## データモデル

### データベーススキーマ

```sql
-- 検索履歴テーブル
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    search_type TEXT NOT NULL, -- 'general' or 'component'
    manufacturer TEXT,         -- 部品検索時のメーカー名
    part_number TEXT,         -- 部品検索時の品番
    results_count INTEGER,
    search_time REAL,         -- 検索実行時間（秒）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 検索結果テーブル
CREATE TABLE search_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_id INTEGER REFERENCES search_history(id),
    url TEXT NOT NULL,
    title TEXT,
    description TEXT,
    rank_position INTEGER,
    is_official_source BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- コンテンツ分析テーブル
CREATE TABLE content_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER REFERENCES search_results(id),
    url TEXT NOT NULL,
    content_type TEXT,        -- 'general', 'specification', 'datasheet'
    summary TEXT,
    key_points TEXT,          -- JSON形式で保存
    technical_specs TEXT,     -- JSON形式で技術仕様保存
    extraction_time REAL,
    content_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ユーザー評価テーブル
CREATE TABLE user_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER REFERENCES content_analysis(id),
    usefulness_rating INTEGER CHECK(usefulness_rating BETWEEN 1 AND 5),
    accuracy_rating INTEGER CHECK(accuracy_rating BETWEEN 1 AND 5),
    feedback TEXT,
    time_saved_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 設定テーブル
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### データクラス定義

```python
@dataclass
class SearchResult:
    url: str
    title: str
    description: str
    rank: int
    is_official: bool = False
    confidence_score: float = 0.0

@dataclass
class ContentAnalysis:
    url: str
    content_type: str
    summary: str
    key_points: List[str]
    technical_specs: Dict[str, Any]
    extraction_time: float
    content_size: int

@dataclass
class SearchMetrics:
    total_searches: int
    avg_search_time: float
    success_rate: float
    avg_usefulness_rating: float
    time_saved_total: int
```

## エラーハンドリング

### エラー分類と対応策

1. **API関連エラー**
   - レート制限: 指数バックオフで再試行
   - 認証エラー: 設定画面へ誘導
   - サービス停止: 代替モデルへフォールバック

2. **ネットワークエラー**
   - タイムアウト: 段階的タイムアウト延長
   - 接続エラー: オフラインモードへ切り替え
   - DNS解決失敗: プロキシ設定確認

3. **コンテンツ処理エラー**
   - 文字化け: エンコーディング自動検出
   - 大容量コンテンツ: チャンク分割処理
   - 解析失敗: 簡易要約モードへ切り替え

### エラー処理フロー

```python
class ErrorHandler:
    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'timeout_escalation': [5, 10, 30]
        }
    
    async def handle_api_error(self, error: Exception, context: str) -> ErrorResponse:
        if isinstance(error, RateLimitError):
            return await self._handle_rate_limit(error)
        elif isinstance(error, AuthenticationError):
            return self._handle_auth_error(error)
        # ... その他のエラー処理
    
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        # 既存のloggerシステムと統合
```

## テスト戦略

### テストレベル

1. **単体テスト**
   - GeminiClient のAPI呼び出し
   - データベース操作の正確性
   - エラーハンドリングの動作確認

2. **統合テスト**
   - サービス間の連携動作
   - データフローの整合性
   - UI-バックエンド間の通信

3. **E2Eテスト**
   - 検索から要約までの完全フロー
   - 異なる検索タイプでの動作確認
   - エラーシナリオでの復旧確認

### テストデータ

```python
# テスト用のモックデータ
MOCK_SEARCH_QUERIES = [
    "Python プログラミング 入門",
    "Arduino センサー 使い方",
    "React フロントエンド 開発"
]

MOCK_COMPONENT_SEARCHES = [
    ("Arduino", "UNO R3"),
    ("Raspberry Pi", "4 Model B"),
    ("STMicroelectronics", "STM32F103C8T6")
]
```

## セキュリティ考慮事項

### API キー管理
- 環境変数での安全な保存
- 設定ファイルでの暗号化
- ローテーション機能の実装

### データプライバシー
- 検索履歴の匿名化オプション
- 個人情報の自動検出・マスキング
- データ保持期間の設定

### 入力検証
- SQLインジェクション対策
- XSS攻撃の防止
- 悪意のあるURL検出

## パフォーマンス最適化

### キャッシュ戦略
- API レスポンスの一時キャッシュ
- 頻繁にアクセスされるコンテンツの永続化
- LRU キャッシュによるメモリ管理

### 非同期処理
- 複数URL の並列処理
- バックグラウンドでの事前読み込み
- プログレッシブローディング

### データベース最適化
- 適切なインデックス設定
- クエリの最適化
- 定期的なVACUUM実行

## 独立プロジェクト構造

### 新規プロジェクト構造

```
gemini-url-search-tool/         # 独立したプロジェクト
├── README.md
├── requirements.txt
├── config.json                 # 設定ファイル
├── .env.example               # 環境変数テンプレート
├── main.py                    # メインエントリーポイント
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── gemini_client.py
│   │   ├── search_service.py
│   │   ├── content_service.py
│   │   └── storage_service.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── search_app.py       # Streamlitメインアプリ
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── search_interface.py
│   │       ├── results_display.py
│   │       └── evaluation_dashboard.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── data_models.py
│   │   └── database.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   ├── validators.py
│   │   └── logger.py
│   └── evaluation/
│       ├── __init__.py
│       └── evaluation_service.py
├── data/
│   ├── search_results.db      # SQLiteデータベース
│   └── cache/                 # キャッシュファイル
├── logs/
│   └── app.log
└── tests/
    ├── __init__.py
    ├── test_gemini_client.py
    ├── test_search_service.py
    └── test_integration.py
```

### 独立性の確保
- **完全に独立したプロジェクト**: 既存システムへの依存なし
- **シンプルな起動**: `streamlit run main.py` で即座に開始
- **軽量な依存関係**: 最小限のライブラリのみ使用
- **ポータブル**: 他の環境への移植が容易

## 運用・監視

### ログ出力
- 検索クエリと結果の記録
- API使用量の追跡
- エラー発生状況の監視
- パフォーマンスメトリクスの収集

### メンテナンス機能
- データベースの定期クリーンアップ
- キャッシュの最適化
- 設定の自動バックアップ
- 使用統計レポートの生成

## 独立プロジェクトとしての利点

### 開発・運用面
- **軽量**: 最小限の依存関係で高速起動
- **ポータブル**: 他のマシンへの移植が容易
- **実験的**: 既存システムに影響を与えずに試行錯誤可能
- **メンテナンス性**: 独立したバージョン管理とアップデート

### 使用面
- **気軽に試用**: 既存の作業環境を汚さない
- **専用ツール**: URL検索に特化した最適化
- **カスタマイズ**: 個人の使用パターンに合わせた調整
- **学習コスト**: シンプルな機能で習得が容易