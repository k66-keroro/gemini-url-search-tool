# API ドキュメント

## 概要

Gemini URL Search Tool の主要APIクラスとメソッドの詳細ドキュメントです。

## コアAPI

### GeminiClient

Gemini APIとの通信を担当するクライアントクラス。

#### 初期化

```python
from src.core.gemini_client import GeminiClient

client = GeminiClient(
    api_key="your_api_key",
    models=["gemini-2.0-flash-exp", "gemini-1.5-flash"],
    max_retries=3,
    timeout=30
)
```

#### メソッド

##### `search_urls(query: str, search_type: SearchType) -> List[SearchResult]`

指定されたクエリでURL検索を実行します。

**パラメータ:**
- `query` (str): 検索クエリ
- `search_type` (SearchType): 検索タイプ（GENERAL または COMPONENT）

**戻り値:**
- `List[SearchResult]`: 検索結果のリスト

**例:**
```python
from src.models.data_models import SearchType

# 一般検索
results = await client.search_urls("Python tutorial", SearchType.GENERAL)

# 部品検索
results = await client.search_urls("Arduino UNO R3", SearchType.COMPONENT)
```

##### `analyze_content(url: str) -> ContentAnalysis`

指定されたURLのコンテンツを分析します。

**パラメータ:**
- `url` (str): 分析対象のURL

**戻り値:**
- `ContentAnalysis`: コンテンツ分析結果

**例:**
```python
analysis = await client.analyze_content("https://example.com")
print(analysis.summary)
```

##### `generate_summary(content: str, focus_areas: List[str] = None) -> str`

コンテンツの要約を生成します。

**パラメータ:**
- `content` (str): 要約対象のコンテンツ
- `focus_areas` (List[str], optional): 重点的に要約する領域

**戻り値:**
- `str`: 生成された要約

**例:**
```python
summary = await client.generate_summary(
    content="長いテキストコンテンツ...",
    focus_areas=["技術仕様", "価格情報"]
)
```

### SearchService

検索機能を提供するサービスクラス。

#### 初期化

```python
from src.core.search_service import SearchService
from src.models.repository import SearchRepository

repository = SearchRepository("data/search_results.db")
search_service = SearchService(
    gemini_client=client,
    search_repository=repository,
    max_results=10
)
```

#### メソッド

##### `search_general(keywords: str) -> SearchResults`

一般的なキーワード検索を実行します。

**パラメータ:**
- `keywords` (str): 検索キーワード

**戻り値:**
- `SearchResults`: 検索結果オブジェクト

**例:**
```python
results = await search_service.search_general("機械学習 Python")
for result in results.results:
    print(f"{result.title}: {result.url}")
```

##### `search_component_specs(manufacturer: str, part_number: str) -> SearchResults`

部品仕様検索を実行します。

**パラメータ:**
- `manufacturer` (str): メーカー名
- `part_number` (str): 品番

**戻り値:**
- `SearchResults`: 検索結果オブジェクト

**例:**
```python
results = await search_service.search_component_specs("Arduino", "UNO R3")
```

##### `get_search_history(filters: SearchFilters = None) -> List[SearchRecord]`

検索履歴を取得します。

**パラメータ:**
- `filters` (SearchFilters, optional): フィルタ条件

**戻り値:**
- `List[SearchRecord]`: 検索履歴のリスト

**例:**
```python
from src.models.data_models import SearchFilters
from datetime import datetime, timedelta

# 過去7日間の検索履歴
filters = SearchFilters(
    start_date=datetime.now() - timedelta(days=7),
    search_type=SearchType.GENERAL
)
history = search_service.get_search_history(filters)
```

### ContentService

コンテンツ処理機能を提供するサービスクラス。

#### 初期化

```python
from src.core.content_service import ContentService

content_service = ContentService(gemini_client=client)
```

#### メソッド

##### `analyze_url(url: str) -> ContentAnalysis`

URLのコンテンツを取得・分析します。

**パラメータ:**
- `url` (str): 分析対象のURL

**戻り値:**
- `ContentAnalysis`: 分析結果

**例:**
```python
analysis = await content_service.analyze_url("https://example.com")
print(f"コンテンツタイプ: {analysis.content_type}")
print(f"要約: {analysis.summary}")
print(f"主要ポイント: {analysis.key_points}")
```

##### `extract_technical_specs(content: str) -> Dict[str, Any]`

技術仕様を抽出します。

**パラメータ:**
- `content` (str): 対象コンテンツ

**戻り値:**
- `Dict[str, Any]`: 抽出された技術仕様

**例:**
```python
specs = await content_service.extract_technical_specs(content)
print(f"仕様: {specs}")
```

### StorageService

データ保存・管理機能を提供するサービスクラス。

#### 初期化

```python
from src.core.storage_service import StorageService

storage_service = StorageService(db_path="data/search_results.db")
```

#### メソッド

##### `save_search_result(search_record: SearchRecord) -> int`

検索結果を保存します。

**パラメータ:**
- `search_record` (SearchRecord): 保存する検索記録

**戻り値:**
- `int`: 保存されたレコードのID

##### `save_content_analysis(analysis: ContentAnalysis) -> int`

コンテンツ分析結果を保存します。

**パラメータ:**
- `analysis` (ContentAnalysis): 保存する分析結果

**戻り値:**
- `int`: 保存されたレコードのID

##### `get_saved_content(content_id: int) -> ContentAnalysis`

保存されたコンテンツ分析を取得します。

**パラメータ:**
- `content_id` (int): コンテンツID

**戻り値:**
- `ContentAnalysis`: 分析結果

### EvaluationService

評価・分析機能を提供するサービスクラス。

#### 初期化

```python
from src.evaluation.evaluation_service import EvaluationService

evaluation_service = EvaluationService(storage_service=storage_service)
```

#### メソッド

##### `calculate_search_metrics(time_range: DateRange) -> SearchMetrics`

検索メトリクスを計算します。

**パラメータ:**
- `time_range` (DateRange): 計算対象の期間

**戻り値:**
- `SearchMetrics`: 計算されたメトリクス

##### `track_user_interaction(interaction: UserInteraction) -> None`

ユーザーインタラクションを記録します。

**パラメータ:**
- `interaction` (UserInteraction): インタラクション情報

## データモデル

### SearchResult

検索結果を表すデータクラス。

```python
@dataclass
class SearchResult:
    url: str                    # 検索結果のURL
    title: str                  # ページタイトル
    description: str            # 説明文
    rank: int                   # ランキング順位
    is_official: bool = False   # 公式ソースかどうか
    confidence_score: float = 0.0  # 信頼度スコア
    source_type: str = "web"    # ソースタイプ
    language: str = "ja"        # 言語
    created_at: datetime = None # 作成日時
```

### ContentAnalysis

コンテンツ分析結果を表すデータクラス。

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
    language: str = "ja"        # 言語
    confidence_score: float = 0.0  # 信頼度
    created_at: datetime = None # 作成日時
```

### SearchRecord

検索記録を表すデータクラス。

```python
@dataclass
class SearchRecord:
    id: Optional[int] = None    # レコードID
    query: str = ""             # 検索クエリ
    search_type: SearchType = SearchType.GENERAL  # 検索タイプ
    manufacturer: Optional[str] = None  # メーカー名（部品検索時）
    part_number: Optional[str] = None   # 品番（部品検索時）
    results_count: int = 0      # 結果数
    search_time: float = 0.0    # 検索時間
    created_at: datetime = None # 作成日時
    results: List[SearchResult] = field(default_factory=list)  # 検索結果
```

### SearchMetrics

検索メトリクスを表すデータクラス。

```python
@dataclass
class SearchMetrics:
    total_searches: int = 0         # 総検索数
    avg_search_time: float = 0.0    # 平均検索時間
    success_rate: float = 0.0       # 成功率
    avg_usefulness_rating: float = 0.0  # 平均有用性評価
    time_saved_total: int = 0       # 総時間節約（分）
    most_common_queries: List[str] = field(default_factory=list)  # 頻出クエリ
    improvement_suggestions: List[str] = field(default_factory=list)  # 改善提案
```

## エラーハンドリング

### カスタム例外

#### SearchError

検索関連のエラー。

```python
from src.utils.error_handler import SearchError

try:
    results = await search_service.search_general("query")
except SearchError as e:
    print(f"検索エラー: {e.message}")
    print(f"エラーコード: {e.error_code}")
```

#### ContentFetchError

コンテンツ取得関連のエラー。

```python
from src.utils.error_handler import ContentFetchError

try:
    analysis = await content_service.analyze_url("https://example.com")
except ContentFetchError as e:
    print(f"コンテンツ取得エラー: {e.message}")
    print(f"URL: {e.url}")
```

#### ValidationError

バリデーション関連のエラー。

```python
from src.utils.error_handler import ValidationError

try:
    # 無効なURLでの検索
    results = await search_service.search_general("")
except ValidationError as e:
    print(f"バリデーションエラー: {e.message}")
    print(f"フィールド: {e.field}")
```

## 設定オプション

### config.json 設定項目

```json
{
  "app": {
    "name": "アプリケーション名",
    "version": "バージョン",
    "debug": false
  },
  "gemini": {
    "models": ["使用するモデルのリスト"],
    "max_retries": 3,
    "timeout": 30,
    "rate_limit_delay": 1.0
  },
  "search": {
    "max_results": 10,
    "default_search_type": "general",
    "enable_caching": true,
    "cache_duration_hours": 24
  },
  "content": {
    "max_content_size": 1048576,
    "chunk_size": 4096,
    "summary_max_length": 1000,
    "extraction_timeout": 60
  },
  "database": {
    "path": "data/search_results.db",
    "backup_enabled": true,
    "cleanup_days": 30
  },
  "ui": {
    "page_title": "ページタイトル",
    "page_icon": "🔍",
    "layout": "wide",
    "sidebar_state": "expanded"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log",
    "max_size_mb": 10,
    "backup_count": 5
  }
}
```

## 使用例

### 完全な検索フロー

```python
import asyncio
from src.core.gemini_client import GeminiClient
from src.core.search_service import SearchService
from src.core.content_service import ContentService
from src.models.repository import SearchRepository

async def complete_search_flow():
    # 初期化
    client = GeminiClient(api_key="your_api_key")
    repository = SearchRepository("data/search_results.db")
    search_service = SearchService(client, repository)
    content_service = ContentService(client)
    
    # 検索実行
    search_results = await search_service.search_general("Python 機械学習")
    
    # 最初の結果を分析
    if search_results.results:
        first_result = search_results.results[0]
        analysis = await content_service.analyze_url(first_result.url)
        
        print(f"タイトル: {first_result.title}")
        print(f"URL: {first_result.url}")
        print(f"要約: {analysis.summary}")
        print(f"主要ポイント: {analysis.key_points}")

# 実行
asyncio.run(complete_search_flow())
```

### バッチ処理

```python
async def batch_analysis():
    client = GeminiClient(api_key="your_api_key")
    content_service = ContentService(client)
    
    urls = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]
    
    # 並列処理で複数URLを分析
    tasks = [content_service.analyze_url(url) for url in urls]
    analyses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, analysis in enumerate(analyses):
        if isinstance(analysis, Exception):
            print(f"URL {urls[i]} の分析に失敗: {analysis}")
        else:
            print(f"URL {urls[i]} の要約: {analysis.summary}")

asyncio.run(batch_analysis())
```

### カスタム評価

```python
from src.evaluation.evaluation_service import EvaluationService
from src.models.data_models import UserInteraction, InteractionType

async def custom_evaluation():
    storage_service = StorageService("data/search_results.db")
    evaluation_service = EvaluationService(storage_service)
    
    # ユーザーインタラクションの記録
    interaction = UserInteraction(
        content_id=1,
        interaction_type=InteractionType.RATING,
        rating=5,
        feedback="非常に有用な情報でした",
        time_saved_minutes=30
    )
    
    evaluation_service.track_user_interaction(interaction)
    
    # メトリクス計算
    from datetime import datetime, timedelta
    from src.models.data_models import DateRange
    
    date_range = DateRange(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )
    
    metrics = evaluation_service.calculate_search_metrics(date_range)
    print(f"総検索数: {metrics.total_searches}")
    print(f"成功率: {metrics.success_rate:.2%}")
    print(f"平均評価: {metrics.avg_usefulness_rating:.1f}/5.0")

asyncio.run(custom_evaluation())
```