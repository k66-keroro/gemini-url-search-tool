# Design Document

## Overview

PC製造部門向け実用ダッシュボードは、既存のSQLiteデータ処理基盤を活用したWebベースの生産管理ツールです。夜間処理テキストファイルと1時間ごとの実績データを基に、Streamlit + Plotlyで構築したシンプルで実用的なダッシュボードです。生産実績・進捗管理、マスタ不備・エラー検出、在庫滞留分析の3つの主要機能に特化しています。

## Architecture

### システム全体構成

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Streamlit Dashboard                                        │
│  - 生産実績・進捗表示                                       │
│  - マスタ不備・エラー一覧                                   │
│  - 在庫滞留分析                                             │
│  - 日次レポート生成                                         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                      │
├─────────────────────────────────────────────────────────────┤
│  Production Analytics │  Error Detection  │  Inventory Analysis │
│  - 実績vs計画分析     │  - マスタ不備検出 │  - 滞留期間計算     │
│  - 進捗率計算         │  - データ整合性   │  - 滞留アラート     │
│  - トレンド分析       │  - エラー分類     │  - 入出庫履歴分析   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Enhanced SQLite Manager                                    │
│  - 夜間処理テキスト読み込み                                 │
│  - 1時間ごと実績データ処理                                  │
│  - データ品質チェック                                       │
│  - レポート出力                                             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Data Storage                           │
├─────────────────────────────────────────────────────────────┤
│  SQLite Database     │  Text Files       │  Export Files    │
│  - 既存製造データ    │  - 夜間処理出力   │  - Excel/PDFレポート│
│  - 実績データ        │  - 1時間ごと実績  │  - 分析結果       │
│  - マスタデータ      │  - エラーログ     │  - 設定ファイル   │
└─────────────────────────────────────────────────────────────┘
```

### 技術スタック

**Frontend:**
- Streamlit 1.28+ (メインダッシュボード)
- Plotly 5.17+ (データ可視化)
- pandas 2.1+ (データ処理・表示)

**Data Processing:**
- 既存SQLiteManager (拡張)
- pandas 2.1+ (データ処理)
- NumPy 1.24+ (数値計算)

**Infrastructure:**
- SQLite 3.40+ (既存データベース活用)
- Python 3.8+ (既存環境)

## Components and Interfaces

### 1. Dashboard Components

#### Production Analytics
```python
class ProductionAnalytics:
    """生産実績・進捗分析コンポーネント"""
    
    def get_daily_performance(self, date: str) -> ProductionSummary:
        """日別生産実績を取得"""
        pass
    
    def calculate_progress_rate(self, date: str) -> float:
        """計画に対する進捗率を計算"""
        pass
    
    def get_hourly_trends(self, date: str) -> List[HourlyData]:
        """1時間ごとの実績トレンドを取得"""
        pass
```

#### Error Detection
```python
class ErrorDetection:
    """マスタ不備・エラー検出コンポーネント"""
    
    def detect_master_errors(self) -> List[MasterError]:
        """マスタ不備を検出"""
        pass
    
    def validate_data_consistency(self) -> List[DataError]:
        """データ整合性をチェック"""
        pass
    
    def categorize_errors(self, errors: List[Error]) -> Dict[str, List[Error]]:
        """エラーを分類"""
        pass
```

#### Inventory Analysis
```python
class InventoryAnalysis:
    """在庫滞留分析コンポーネント"""
    
    def calculate_stagnation_period(self, item_code: str) -> int:
        """品目の滞留期間を計算"""
        pass
    
    def get_stagnant_items(self, threshold_days: int) -> List[StagnantItem]:
        """滞留品目を抽出"""
        pass
    
    def analyze_inventory_movement(self, item_code: str) -> InventoryMovement:
        """入出庫履歴を分析"""
        pass
```

### 2. Data Processing Interface

#### File Processing
```python
class DataProcessor:
    """データ処理インターフェース"""
    
    def process_night_batch_files(self, file_path: str) -> ProcessResult:
        """夜間処理テキストファイルを処理"""
        pass
    
    def process_hourly_data(self, file_path: str) -> ProcessResult:
        """1時間ごと実績データを処理"""
        pass
    
    def export_report(self, report_type: str, format: str) -> str:
        """レポートをエクスポート"""
        pass
```

### 3. Data Models

#### Core Data Models
```python
@dataclass
class ProductionSummary:
    date: str
    planned_quantity: int
    actual_quantity: int
    progress_rate: float
    error_count: int

@dataclass
class HourlyData:
    hour: int
    quantity: int
    cumulative_quantity: int
    efficiency: float

@dataclass
class MasterError:
    error_type: str
    item_code: str
    description: str
    severity: str
    detected_at: datetime

@dataclass
class StagnantItem:
    item_code: str
    item_name: str
    stagnation_days: int
    current_stock: int
    last_movement_date: datetime
```

## Error Handling

### エラー分類と対応

1. **ファイル処理エラー**
   - ファイル読み込みエラー → エラーメッセージ表示
   - データ形式エラー → スキップして処理継続
   - エンコーディングエラー → 自動検出・変換

2. **データ処理エラー**
   - 計算エラー → デフォルト値使用
   - メモリ不足 → チャンク処理
   - データ不整合 → エラーリストに記録

3. **表示エラー**
   - グラフ描画エラー → エラーメッセージ表示
   - データ不足 → 「データなし」表示
   - レポート生成エラー → 部分的な出力

### エラーログ

```python
class SimpleErrorHandler:
    def log_error(self, error: Exception, context: str):
        """エラーログ記録"""
        pass
    
    def show_user_message(self, message: str):
        """ユーザー向けメッセージ表示"""
        pass
```

## Testing Strategy

### テスト戦略

1. **単体テスト**
   - データ処理ロジックのテスト
   - 計算機能のテスト
   - ファイル読み込み機能のテスト

2. **統合テスト**
   - ダッシュボード表示テスト
   - レポート生成テスト
   - データベース連携テスト

3. **ユーザーテスト**
   - 実際のデータを使用した動作確認
   - 画面操作の確認
   - レポート出力の確認

### テスト環境

```python
# テスト設定
TEST_DATABASE = "test_manufacturing.db"

# テストデータ生成
class TestDataGenerator:
    def generate_sample_production_data(self) -> pd.DataFrame:
        """サンプル生産データ生成"""
        pass
    
    def generate_sample_error_data(self) -> pd.DataFrame:
        """サンプルエラーデータ生成"""
        pass
```

## Performance Considerations

### パフォーマンス最適化

1. **データ処理最適化**
   - pandasの効率的な使用
   - 大量データのチャンク処理
   - 不要なデータの事前フィルタリング

2. **表示最適化**
   - Streamlitキャッシュの活用
   - グラフ描画の最適化
   - ページング機能の実装

3. **ファイル処理最適化**
   - 効率的なファイル読み込み
   - メモリ使用量の監視
   - 処理時間の短縮

### 監視

```python
class SimplePerformanceMonitor:
    def track_processing_time(self, operation: str, duration: float):
        """処理時間追跡"""
        pass
    
    def track_memory_usage(self):
        """メモリ使用量監視"""
        pass
```