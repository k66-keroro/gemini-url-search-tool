"""
定数定義モジュール

SQLite GUI Toolで使用される定数を定義します。
"""

from pathlib import Path


class Paths:
    """パス関連の定数"""
    
    def __init__(self):
        self.PROJECT_ROOT = Path.cwd()
        self.DATA_DIR = self.PROJECT_ROOT / 'data'
        self.RAW_DATA = self.DATA_DIR / 'raw'
        self.SQLITE_DIR = self.DATA_DIR / 'sqlite'
        self.SQLITE_DB = self.SQLITE_DIR / 'main.db'
        self.LOGS = self.PROJECT_ROOT / 'logs'
        self.CONFIG = self.PROJECT_ROOT / 'config'
        self.DOCS = self.PROJECT_ROOT / 'docs'
        self.SRC = self.PROJECT_ROOT / 'src'


class UI:
    """UI関連の定数"""
    
    # ウィンドウサイズ
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 800
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600
    
    # フォント
    DEFAULT_FONT_FAMILY = "Arial"
    DEFAULT_FONT_SIZE = 10
    MONOSPACE_FONT_FAMILY = "Courier New"
    
    # 色
    PRIMARY_COLOR = "#0078d4"
    SUCCESS_COLOR = "#107c10"
    WARNING_COLOR = "#ff8c00"
    ERROR_COLOR = "#d13438"
    
    # パディング
    DEFAULT_PADDING = 10
    SMALL_PADDING = 5
    LARGE_PADDING = 20
    
    # ウィジェットサイズ
    BUTTON_WIDTH = 100
    ENTRY_WIDTH = 300
    LISTBOX_WIDTH = 200
    TEXT_HEIGHT = 10
    
    # タブ名
    TAB_QUERY = "クエリ実行"
    TAB_SCHEMA = "スキーマ"
    TAB_IMPORT = "インポート"
    TAB_EXPORT = "エクスポート"
    TAB_ANALYZE = "データ分析"
    TAB_CONVERTER = "コードフィールド変換"


class Database:
    """データベース関連の定数"""
    
    # 接続設定
    DEFAULT_TIMEOUT = 30
    MAX_RETRY_COUNT = 3
    
    # クエリ設定
    MAX_RESULT_ROWS = 1000
    QUERY_TIMEOUT = 60
    PREVIEW_ROWS = 10
    
    # SQLite PRAGMA設定
    PRAGMA_SETTINGS = {
        "journal_mode": "WAL",
        "synchronous": "NORMAL",
        "cache_size": 10000,
        "temp_store": "MEMORY"
    }
    
    # サポートされるファイル形式
    SUPPORTED_DB_EXTENSIONS = [".db", ".sqlite", ".sqlite3"]
    
    # テーブル名変換設定
    TABLE_NAME_PREFIX = "t_"
    MAX_TABLE_NAME_LENGTH = 64


class FileFormats:
    """ファイル形式関連の定数"""
    
    # インポート/エクスポート対応形式
    CSV = "CSV"
    TSV = "TSV"
    EXCEL = "Excel"
    
    # ファイル拡張子
    CSV_EXTENSIONS = [".csv"]
    TSV_EXTENSIONS = [".tsv", ".txt"]
    EXCEL_EXTENSIONS = [".xlsx", ".xls"]
    
    # エンコーディング
    ENCODINGS = [
        "utf-8",
        "utf-8-sig",
        "cp932",
        "shift_jis",
        "euc_jp"
    ]
    
    # 区切り文字
    DELIMITERS = {
        "カンマ": ",",
        "タブ": "\t",
        "セミコロン": ";",
        "パイプ": "|"
    }
    
    # ファイルサイズ制限（MB）
    MAX_IMPORT_FILE_SIZE = 100
    MAX_EXPORT_FILE_SIZE = 500


class Analysis:
    """データ分析関連の定数"""
    
    # 分析タイプ
    BASIC_STATS = "基本統計"
    FREQUENCY_DISTRIBUTION = "頻度分布"
    NULL_CHECK = "NULL値チェック"
    DUPLICATE_CHECK = "重複値チェック"
    
    # サンプルサイズ
    DEFAULT_SAMPLE_SIZE = 10000
    MAX_SAMPLE_SIZE = 100000
    
    # 表示制限
    MAX_FREQUENCY_ITEMS = 100
    MAX_DUPLICATE_ITEMS = 100
    MAX_NULL_SAMPLES = 10
    
    # データ型判定
    NUMERIC_TYPES = ["INTEGER", "REAL", "NUMERIC", "FLOAT", "DOUBLE"]
    TEXT_TYPES = ["TEXT", "VARCHAR", "CHAR"]
    DATE_TYPES = ["DATE", "DATETIME", "TIMESTAMP"]


class Messages:
    """メッセージ関連の定数"""
    
    # 成功メッセージ
    SUCCESS_DB_CONNECT = "データベースに接続しました"
    SUCCESS_QUERY_EXECUTE = "クエリを実行しました"
    SUCCESS_DATA_IMPORT = "データをインポートしました"
    SUCCESS_DATA_EXPORT = "データをエクスポートしました"
    SUCCESS_FIELD_CONVERT = "フィールドを変換しました"
    
    # エラーメッセージ
    ERROR_DB_CONNECT = "データベースへの接続に失敗しました"
    ERROR_QUERY_EXECUTE = "クエリの実行に失敗しました"
    ERROR_DATA_IMPORT = "データのインポートに失敗しました"
    ERROR_DATA_EXPORT = "データのエクスポートに失敗しました"
    ERROR_FILE_NOT_FOUND = "ファイルが見つかりません"
    ERROR_INVALID_FORMAT = "ファイル形式が無効です"
    ERROR_PERMISSION_DENIED = "ファイルへのアクセス権限がありません"
    
    # 警告メッセージ
    WARNING_LARGE_FILE = "ファイルサイズが大きいため、処理に時間がかかる場合があります"
    WARNING_MANY_ROWS = "結果の行数が多いため、表示が制限されます"
    WARNING_UNSAVED_CHANGES = "保存されていない変更があります"
    
    # 情報メッセージ
    INFO_NO_DATA = "データがありません"
    INFO_PROCESSING = "処理中..."
    INFO_COMPLETED = "処理が完了しました"


class Validation:
    """バリデーション関連の定数"""
    
    # テーブル名バリデーション
    TABLE_NAME_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    MIN_TABLE_NAME_LENGTH = 1
    MAX_TABLE_NAME_LENGTH = 64
    
    # カラム名バリデーション
    COLUMN_NAME_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    MIN_COLUMN_NAME_LENGTH = 1
    MAX_COLUMN_NAME_LENGTH = 64
    
    # ファイルサイズ制限
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
    
    # 文字列長制限
    MAX_DISPLAY_STRING_LENGTH = 100
    MAX_ERROR_MESSAGE_LENGTH = 500


class Performance:
    """パフォーマンス関連の定数"""
    
    # バッチ処理サイズ
    DEFAULT_BATCH_SIZE = 1000
    LARGE_BATCH_SIZE = 10000
    SMALL_BATCH_SIZE = 100
    
    # タイムアウト設定
    SHORT_TIMEOUT = 5
    MEDIUM_TIMEOUT = 30
    LONG_TIMEOUT = 300
    
    # メモリ使用量制限
    MAX_MEMORY_USAGE_MB = 500
    
    # 並列処理設定
    DEFAULT_THREAD_COUNT = 4
    MAX_THREAD_COUNT = 8


class CodeFieldConverter:
    """コードフィールド変換関連の定数"""
    
    # 変換対象の検出パターン
    CODE_FIELD_PATTERNS = [
        r'.*コード.*',
        r'.*code.*',
        r'.*id$',
        r'.*番号.*',
        r'.*no$'
    ]
    
    # 変換理由
    REASON_LEADING_ZERO = "先頭に0を含む値が存在"
    REASON_TRAILING_MINUS = "末尾にマイナス記号を含む値が存在"
    REASON_TYPE_MISMATCH = "テーブル間でデータ型が不一致"
    REASON_NUMERIC_CODE = "数値型で保存されたコードフィールド"
    
    # サンプル値の表示数
    MAX_SAMPLE_VALUES = 5