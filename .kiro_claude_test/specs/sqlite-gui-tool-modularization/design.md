# SQLite GUI Tool モジュール化設計書

## 1. 概要

このドキュメントでは、SQLite GUI Toolのモジュール化設計について詳細に説明します。現在の単一ファイル構造から、機能ごとに分割された保守性の高いモジュール構造への移行計画を示します。

## 2. アーキテクチャ

### 2.1 全体アーキテクチャ

SQLite GUI Toolは以下の階層構造でモジュール化します：

```
sqlite_gui_tool/
├── main.py                    # エントリーポイント
├── app.py                     # メインアプリケーションクラス
├── config/                    # 設定関連
│   ├── __init__.py
│   ├── settings.py            # 設定管理
│   └── constants.py           # 定数定義
├── core/                      # コア機能
│   ├── __init__.py
│   ├── db_connection.py       # データベース接続管理
│   └── table_utils.py         # テーブル操作ユーティリティ
├── ui/                        # UI関連
│   ├── __init__.py
│   ├── components/            # 共通UIコンポーネント
│   │   ├── __init__.py
│   │   ├── data_table.py      # データテーブル表示
│   │   ├── file_dialog.py     # ファイル選択ダイアログ
│   │   └── message_box.py     # メッセージ表示
│   └── tabs/                  # タブごとの実装
│       ├── __init__.py
│       ├── base_tab.py        # 基底タブクラス
│       ├── query_tab.py       # クエリ実行タブ
│       ├── schema_tab.py      # スキーマ表示タブ
│       ├── import_tab.py      # インポートタブ
│       ├── export_tab.py      # エクスポートタブ
│       ├── analyze_tab.py     # データ分析タブ
│       └── converter_tab.py   # コードフィールド変換タブ
└── utils/                     # ユーティリティ
    ├── __init__.py
    ├── error_handler.py       # エラーハンドリング
    ├── logger.py              # ロギング
    └── string_utils.py        # 文字列操作ユーティリティ
```

### 2.2 モジュール間の依存関係

モジュール間の依存関係は以下のようになります：

```
main.py → app.py → ui/tabs/* → ui/components/* → core/* → utils/*
                 → config/*
```

循環依存を避けるため、上位モジュールから下位モジュールへの依存のみを許可します。

## 3. モジュール詳細

### 3.1 main.py

アプリケーションのエントリーポイントです。

**責任**:
- アプリケーションの起動
- 例外のグローバルハンドリング
- 終了処理

**主要クラス/関数**:
- `main()`: アプリケーションのエントリーポイント

### 3.2 app.py

メインアプリケーションクラスを定義します。

**責任**:
- メインウィンドウの作成
- タブの初期化と管理
- 共通UIコンポーネントの管理
- データベース接続の管理

**主要クラス/関数**:
- `SQLiteGUIApp`: メインアプリケーションクラス

### 3.3 config/

設定関連のモジュールを格納します。

#### 3.3.1 settings.py

アプリケーション設定の管理を担当します。

**責任**:
- 設定の読み込み/保存
- デフォルト設定の提供
- 設定変更の通知

**主要クラス/関数**:
- `Settings`: 設定管理クラス

#### 3.3.2 constants.py

アプリケーション全体で使用される定数を定義します。

**責任**:
- パス定数
- UI定数
- メッセージ定数

### 3.4 core/

コア機能を実装するモジュールを格納します。

#### 3.4.1 db_connection.py

データベース接続の管理を担当します。

**責任**:
- データベース接続の確立/切断
- クエリの実行
- トランザクション管理

**主要クラス/関数**:
- `DatabaseConnection`: データベース接続クラス

#### 3.4.2 table_utils.py

テーブル操作のユーティリティを提供します。

**責任**:
- テーブル名の変換
- テーブル構造の取得
- インデックス情報の取得

**主要クラス/関数**:
- `sanitize_table_name()`: テーブル名を適切に変換
- `get_table_structure()`: テーブル構造を取得
- `get_table_indexes()`: テーブルのインデックス情報を取得

### 3.5 ui/components/

共通UIコンポーネントを実装するモジュールを格納します。

#### 3.5.1 data_table.py

データテーブル表示コンポーネントを実装します。

**責任**:
- データの表形式表示
- ソート機能
- 列幅の自動調整

**主要クラス/関数**:
- `DataTable`: データテーブル表示クラス

#### 3.5.2 file_dialog.py

ファイル選択ダイアログを実装します。

**責任**:
- ファイル選択ダイアログの表示
- ディレクトリ選択ダイアログの表示
- ファイル保存ダイアログの表示

**主要クラス/関数**:
- `FileDialog`: ファイル選択ダイアログクラス

#### 3.5.3 message_box.py

メッセージボックスを実装します。

**責任**:
- 情報メッセージの表示
- 警告メッセージの表示
- エラーメッセージの表示
- 確認ダイアログの表示

**主要クラス/関数**:
- `MessageBox`: メッセージボックスクラス

### 3.6 ui/tabs/

各タブの実装を格納します。

#### 3.6.1 base_tab.py

全てのタブの基底クラスを定義します。

**責任**:
- 共通タブ機能の提供
- タブのライフサイクル管理

**主要クラス/関数**:
- `BaseTab`: タブの基底クラス

#### 3.6.2 query_tab.py

クエリ実行タブを実装します。

**責任**:
- SQLクエリの入力と実行
- クエリ結果の表示
- クエリ例の提供

**主要クラス/関数**:
- `QueryTab`: クエリ実行タブクラス

#### 3.6.3 schema_tab.py

スキーマ表示タブを実装します。

**責任**:
- テーブル一覧の表示
- テーブル構造の表示
- インデックス情報の表示

**主要クラス/関数**:
- `SchemaTab`: スキーマ表示タブクラス

#### 3.6.4 import_tab.py

インポートタブを実装します。

**責任**:
- ファイル選択
- インポート設定
- データプレビュー
- インポート実行

**主要クラス/関数**:
- `ImportTab`: インポートタブクラス

#### 3.6.5 export_tab.py

エクスポートタブを実装します。

**責任**:
- エクスポート方法の選択
- エクスポート設定
- データプレビュー
- エクスポート実行

**主要クラス/関数**:
- `ExportTab`: エクスポートタブクラス

#### 3.6.6 analyze_tab.py

データ分析タブを実装します。

**責任**:
- 分析対象の選択
- 分析タイプの選択
- 分析実行
- 分析結果の表示

**主要クラス/関数**:
- `AnalyzeTab`: データ分析タブクラス

#### 3.6.7 converter_tab.py

コードフィールド変換タブを実装します。

**責任**:
- 変換対象フィールドの分析
- フィールド選択
- 変換実行

**主要クラス/関数**:
- `ConverterTab`: コードフィールド変換タブクラス

### 3.7 utils/

ユーティリティモジュールを格納します。

#### 3.7.1 error_handler.py

エラーハンドリングを実装します。

**責任**:
- 例外のキャッチと処理
- エラーメッセージの生成
- エラーログの記録

**主要クラス/関数**:
- `ErrorHandler`: エラーハンドリングクラス

#### 3.7.2 logger.py

ロギング機能を実装します。

**責任**:
- ログの記録
- ログレベルの管理
- ログファイルのローテーション

**主要クラス/関数**:
- `Logger`: ロギングクラス

#### 3.7.3 string_utils.py

文字列操作ユーティリティを提供します。

**責任**:
- テーブル名の変換
- エンコーディング検出
- 文字列フォーマット

**主要クラス/関数**:
- `detect_encoding()`: ファイルのエンコーディングを検出
- `format_sql()`: SQLクエリを整形

## 4. クラス設計

### 4.1 BaseTab クラス

```python
class BaseTab:
    """タブの基底クラス"""
    
    def __init__(self, parent, db_connection):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            db_connection: データベース接続オブジェクト
        """
        self.parent = parent
        self.db_connection = db_connection
        self.frame = None
        
    def initialize(self):
        """タブの初期化"""
        self.frame = ttk.Frame(self.parent)
        return self.frame
        
    def update_after_connection(self):
        """データベース接続後の更新"""
        pass
        
    def clear(self):
        """タブのクリア"""
        pass
```

### 4.2 DatabaseConnection クラス

```python
class DatabaseConnection:
    """データベース接続クラス"""
    
    def __init__(self):
        """初期化"""
        self.conn = None
        self.cursor = None
        self.db_path = None
        
    def connect(self, db_path):
        """
        データベースに接続
        
        Args:
            db_path: データベースファイルのパス
            
        Returns:
            bool: 接続成功の場合True、失敗の場合False
        """
        try:
            if self.conn:
                self.close()
                
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self.db_path = db_path
            return True
        except Exception as e:
            Logger.error(f"データベース接続エラー: {str(e)}")
            return False
            
    def close(self):
        """接続を閉じる"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            self.db_path = None
            
    def execute_query(self, query, params=None):
        """
        クエリを実行
        
        Args:
            query: 実行するSQLクエリ
            params: クエリパラメータ（オプション）
            
        Returns:
            tuple: (成功フラグ, 結果, エラーメッセージ)
        """
        if not self.conn:
            return False, None, "データベースに接続されていません"
            
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
                
            results = self.cursor.fetchall()
            return True, results, None
        except Exception as e:
            error_msg = str(e)
            Logger.error(f"クエリ実行エラー: {error_msg}")
            return False, None, error_msg
```

### 4.3 Settings クラス

```python
class Settings:
    """設定管理クラス"""
    
    def __init__(self, config_file):
        """
        初期化
        
        Args:
            config_file: 設定ファイルのパス
        """
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self):
        """
        設定を読み込む
        
        Returns:
            dict: 設定データ
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            Logger.error(f"設定読み込みエラー: {str(e)}")
            
        return {}
        
    def save_config(self):
        """設定を保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            Logger.error(f"設定保存エラー: {str(e)}")
            
    def get(self, key, default=None):
        """
        設定値を取得
        
        Args:
            key: 設定キー
            default: デフォルト値（オプション）
            
        Returns:
            設定値
        """
        return self.config.get(key, default)
        
    def set(self, key, value):
        """
        設定値を設定
        
        Args:
            key: 設定キー
            value: 設定値
        """
        self.config[key] = value
        self.save_config()
```

### 4.4 DataTable クラス

```python
class DataTable:
    """データテーブル表示クラス"""
    
    def __init__(self, parent):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
        """
        self.parent = parent
        self.tree = None
        self.y_scrollbar = None
        self.x_scrollbar = None
        self._initialize()
        
    def _initialize(self):
        """初期化"""
        self.tree = ttk.Treeview(self.parent)
        
        # スクロールバー
        self.y_scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.x_scrollbar = ttk.Scrollbar(self.parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.y_scrollbar.set, xscrollcommand=self.x_scrollbar.set)
        
        # 配置
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def set_columns(self, columns):
        """
        列を設定
        
        Args:
            columns: 列名のリスト
        """
        self.tree["columns"] = columns
        self.tree["show"] = "headings"
        
        for col in columns:
            self.tree.heading(col, text=str(col))
            self.tree.column(col, width=100)
            
    def insert_data(self, data):
        """
        データを挿入
        
        Args:
            data: 挿入するデータのリスト
        """
        # 既存のデータをクリア
        self.clear()
        
        # データを挿入
        for row in data:
            # NULL値を「NULL」として表示
            formatted_row = [str(val) if val is not None else "NULL" for val in row]
            self.tree.insert("", "end", values=formatted_row)
            
        # 列幅を調整
        self.adjust_column_widths()
        
    def clear(self):
        """データをクリア"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
    def adjust_column_widths(self):
        """列幅を調整"""
        if not self.tree["columns"]:
            return
            
        for i, col in enumerate(self.tree["columns"]):
            # 列の値の最大長を計算
            max_len = len(str(col))
            
            for item_id in self.tree.get_children():
                values = self.tree.item(item_id, "values")
                if i < len(values):
                    val = values[i]
                    if val is not None:
                        val_len = len(str(val))
                        if val_len > max_len:
                            max_len = min(val_len, 50)  # 最大50文字
            
            # 列幅を設定（文字数 * 平均文字幅）
            char_width = 7  # 平均文字幅（ピクセル）
            self.tree.column(col, width=max_len * char_width)
```

## 5. 移行計画

### 5.1 移行ステップ

1. **プロジェクト構造の作成**
   - 新しいディレクトリ構造を作成
   - 必要なファイルを作成

2. **共通コンポーネントの実装**
   - BaseTabクラスの実装
   - DatabaseConnectionクラスの実装
   - Settingsクラスの実装
   - DataTableクラスの実装

3. **ユーティリティの実装**
   - エラーハンドリングの実装
   - ロギングの実装
   - 文字列ユーティリティの実装

4. **各タブの実装**
   - 既存コードからタブごとの機能を抽出
   - 新しいクラス構造に移行

5. **メインアプリケーションの実装**
   - app.pyの実装
   - main.pyの実装

6. **テストと検証**
   - 各モジュールの単体テスト
   - 統合テスト
   - 既存機能との互換性確認

### 5.2 リスクと対策

| リスク | 影響 | 対策 |
|-------|------|------|
| 循環依存の発生 | モジュール間の依存関係が複雑化 | 明確な階層構造の設計と依存関係の監視 |
| 機能の欠落 | 既存機能が動作しなくなる | 詳細な機能リストの作成と移行後のテスト |
| パフォーマンスの低下 | アプリケーションの応答性が低下 | パフォーマンス測定とボトルネックの特定 |
| 互換性の問題 | 既存のデータや設定が使用できなくなる | 後方互換性の確保と移行ツールの提供 |

## 6. 拡張性

### 6.1 新機能の追加方法

新しい機能を追加する場合は、以下の手順で実装します：

1. 適切なモジュールを特定
2. 必要に応じて新しいクラスを作成
3. 既存のインターフェースを活用
4. 単体テストを作成
5. メインアプリケーションに統合

### 6.2 プラグイン機構

将来的には、以下のようなプラグイン機構を実装することも検討します：

- プラグインインターフェースの定義
- プラグインの動的読み込み
- プラグイン設定の管理
- プラグイン間の連携

## 7. まとめ

SQLite GUI Toolのモジュール化により、以下のメリットが期待できます：

- コードの保守性向上
- 機能拡張の容易化
- テスト容易性の向上
- チーム開発の効率化

モジュール化は段階的に進め、各ステップでの検証を徹底することで、リスクを最小限に抑えながら実施します。