# DB Browser for SQLite 参考情報

## 主キー設定の手順

### GUIツールでの主キー設定

1. **テーブル選択**: GUIツールでテーブルを選択
2. **主キー追加ボタン**: 「選択テーブルに主キー追加」をクリック
3. **自動処理**: 以下の処理が自動で実行されます
   - 既存テーブルを一時テーブルにリネーム
   - 新しいテーブルを作成（`_rowid_`主キー付き）
   - データを移行
   - 一時テーブルを削除

### DB Browser for SQLiteでの手動設定

#### 方法1: GUI操作（推奨）
1. **テーブル選択**: 対象テーブルを選択
2. **テーブルの変更**: 右クリック→「テーブルの変更」
3. **主キー設定**: 
   - 新しいカラムを追加（INTEGER型）
   - 「PK」にチェック
   - 「OK」で適用
4. **自動増分設定**: 
   - 再度「テーブルの変更」を開く
   - 「AI」にチェック
   - 「OK」で適用

#### 方法2: SQL手動実行
```sql
-- 1. 外部キー制約を無効化
PRAGMA foreign_keys=off;
BEGIN TRANSACTION;

-- 2. 既存テーブルをリネーム
ALTER TABLE zm29 RENAME TO temp_zm29;

-- 3. 新しいテーブルを作成（主キー付き）
CREATE TABLE zm29 (
    "_rowid_" INTEGER PRIMARY KEY AUTOINCREMENT,
    "MRP管理者" TEXT,
    "転記日付" INTEGER,
    -- 他のカラム...
);

-- 4. データを移行
INSERT INTO zm29 ("MRP管理者", "転記日付", ...)
SELECT "MRP管理者", "転記日付", ... FROM temp_zm29;

-- 5. 一時テーブルを削除
DROP TABLE temp_zm29;

-- 6. トランザクションをコミット
COMMIT;
PRAGMA foreign_keys=on;
```

## 重要なポイント

### 1. INTEGER PRIMARY KEY vs AUTOINCREMENT
- **INTEGER PRIMARY KEY**: 連番が自動で付与される
- **AUTOINCREMENT**: IDの重複を絶対に避ける（大規模システム向け）

### 2. 主キー設定のタイミング
- **PKのみ**: 基本的な連番機能
- **PK + AI**: 厳密なID管理

### 3. エラー対処法
- **データ型エラー**: カラムがINTEGER型であることを確認
- **データ存在エラー**: カラムが完全に空（NULL）であることを確認
- **重複エラー**: 主キーに設定するカラムに重複値がないことを確認

## 本システムでの実装

### SQLiteManager.finalize_table_structure()
```python
# DB Browser for SQLiteの手順を参考に実装
success, error = manager.finalize_table_structure(conn, table_name, [])
```

### 処理の流れ
1. **テーブル存在確認**: テーブルが存在するかチェック
2. **主キー重複チェック**: 既に主キーが設定されているかチェック
3. **テーブルリネーム**: 既存テーブルを一時テーブルにリネーム
4. **新テーブル作成**: `_rowid_`主キー付きの新しいテーブルを作成
5. **データ移行**: データを新しいテーブルにコピー
6. **一時テーブル削除**: 一時テーブルを削除
7. **インデックス作成**: 指定されたカラムにインデックスを作成

### エラーハンドリング
- **ロールバック**: エラー時に元のテーブルに復元
- **詳細ログ**: 処理の各段階でログを出力
- **安全な処理**: トランザクションを使用してデータの整合性を保証

## 参考情報

- **SQLite公式ドキュメント**: https://www.sqlite.org/lang_altertable.html
- **DB Browser for SQLite**: https://sqlitebrowser.org/
- **主キーとインデックスの違い**: 主キーは一意性制約、インデックスは検索速度向上 