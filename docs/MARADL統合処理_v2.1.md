# MARADL統合処理 v2.1

## 概要

既存のsqlite_gui_tool_v2_fixed_modular.pyにMARADLパイプライン処理を統合しました。これにより、3段階のマスタ処理が一元管理できるようになりました。

## 統合された処理

### 1. MARA_DL → 全120フィールドのマスタテーブル
- **ソース**: `data/raw/MARA_DL.csv`
- **テーブル**: `MARA_DL`
- **処理**: 全件データ更新で自動処理
- **内容**: SAP MARAマスタの全フィールド（約120項目）

### 2. view_pc_master → 使用頻度の高いフィールドを抽出してPC基板に絞り込み
- **ソース**: `MARA_DL`テーブル
- **テーブル**: `view_pc_master`
- **処理**: MARADLパイプライン処理で作成
- **フィルタ条件**:
  ```sql
  WHERE 
      (プラント = 'P100' AND 評価クラス = '2120') OR
      (プラント = 'P100' AND 評価クラス = '2130' AND 品目 LIKE '9710%' AND 品目 != '971030100')
  ```
- **抽出フィールド**: 34項目（使用頻度の高いもの）

### 3. parsed_pc_master → 差分検出と正規表現による要素抽出
- **ソース**: `view_pc_master`テーブル
- **テーブル**: `parsed_pc_master`
- **処理**: MARADLパイプライン処理で差分検出・登録
- **抽出要素**:
  - `cm_code`: CM分類コード
  - `board_number`: 基板番号
  - `derivative_code`: 派生コード
  - `board_type`: 基板タイプ（標準/派生基板）

## 実装箇所

### DB管理タブ（admin_tab.py）
新しいボタンとメソッドを追加：

1. **MARADLパイプライン処理ボタン**
   - `process_maradl_pipeline()`: メイン処理
   - `_create_view_pc_master()`: view_pc_master作成
   - `_create_parsed_pc_master()`: parsed_pc_master作成
   - `_process_pc_master_diff()`: 差分検出・登録

2. **ZP138個別処理ボタン**（既存を強化）
   - `process_zp138_individual()`: ZP138プロセッサー連携

3. **データベース診断ボタン**（新規）
   - `diagnose_database()`: 詳細な診断情報

4. **データ型分析ボタン**（新規）
   - `analyze_data_type_consistency()`: データ型整合性分析

5. **データ型統一ボタン**（新規）
   - `standardize_data_types()`: Access連携対応の型統一

### スクリプト実行タブ（launcher_tab.py）
外部スクリプトの実行管理機能を追加：

- **設定可能なスクリプト管理**
- **カテゴリ別表示**
- **実行ログ表示**
- **JSON設定ファイル連携**

## 正規表現パターン

### 派生コード抽出
```python
DERIVATIVE_PATTERN = re.compile(r"([STU][0-9]{1,2}|[STU][A-Z][0-9])")
BLACKLIST = {"SENS", "CV", "CV-055"}
```

### CM分類コード抽出
```python
Y_CODE_MAP = {
    "YAMK": "m", "YAUWM": "w", "YAWM": "w", "YBPM": "p", 
    "YCK": "c", "YCUWM": "w", "YGK": "g", "YMK": "m", 
    "YPK": "p", "YPM": "p", "YUK": "w", "YWK": "w", "YWM": "w"
}

HEAD_CM_MAP = {
    "AK": "a", "CK": "c", "DK": "d", "EK": "e", "GK": "g", 
    "HK": "h", "IK": "i", "LK": "l", "MK": "m", "PK": "p", 
    "PM": "p", "SK": "s", "UK": "w", "UWM": "w", "WK": "w", 
    "WM": "w", "WS": "w", "BWM": "w"
}
```

### 基板番号抽出
- DIMCOM形式: `DIMCOM No.12345`
- P00A形式: `P00A12345` → `1234`
- P0A形式: `P0A1234` → `1234`
- ハイフン区切り: `NAME-1234`
- 数値パターン: `\d{3,4}`

## 使用方法

### 1. 基本的なワークフロー
1. **データベース接続**: SQLiteファイルを選択
2. **全件データ更新**: MARA_DL.csvを含む全ファイルを処理
3. **MARADLパイプライン処理**: 3段階のマスタ処理を実行
4. **結果確認**: スキーマタブで各テーブルを確認

### 2. MARADLパイプライン処理の実行
```
DB管理タブ → MARADLパイプライン処理ボタン → 確認ダイアログ → 実行
```

### 3. 処理結果の確認
- **view_pc_master**: PC基板に絞り込まれたマスタ
- **parsed_pc_master**: 解析済みPC基板マスタ
- **差分ログ**: `logs/pc_master_diff_YYYYMMDD_HHMMSS.csv`

## データフロー

```
MARA_DL.csv (120フィールド)
    ↓ (全件データ更新)
MARA_DL テーブル
    ↓ (フィルタ・抽出)
view_pc_master テーブル (34フィールド)
    ↓ (差分検出・正規表現解析)
parsed_pc_master テーブル (7フィールド)
    ↓ (ログ出力)
差分ログCSV
```

## テーブル構造

### MARA_DL
- 全120フィールド（SAP MARAマスタの完全コピー）
- 主要フィールド: 品目、品目テキスト、プラント、評価クラス、標準原価など

### view_pc_master
- 34フィールド（使用頻度の高いもの）
- PC基板関連のみ（P100プラント、評価クラス2120/2130）

### parsed_pc_master
- 7フィールド: 品目、品目テキスト、cm_code、board_number、derivative_code、board_type、登録日
- 正規表現による解析結果

## エラーハンドリング

### 1. ファイル不存在
- MARA_DL.csvが存在しない場合は全件データ更新を促す
- ZP138.txtが存在しない場合は適切なエラーメッセージ

### 2. テーブル不存在
- MARA_DLテーブルが存在しない場合は処理を中断
- 適切なエラーメッセージとガイダンス

### 3. データ処理エラー
- 個別レコードのエラーは記録して処理継続
- 詳細なエラーログを出力

## パフォーマンス

### 処理時間の目安
- **MARA_DL読み込み**: 約10-30秒（ファイルサイズ依存）
- **view_pc_master作成**: 約1-5秒
- **parsed_pc_master処理**: 約5-15秒（差分データ量依存）

### メモリ使用量
- 大きなMARA_DLファイルの場合は一時的にメモリ使用量が増加
- 処理完了後は自動的に解放

## データ型整合性対応

### SQLiteとAccessの違い
- **SQLite**: 動的型付け、柔軟なデータ型
- **Access**: 静的型付け、厳密な型制約

### 問題例
```sql
-- 問題のあるケース
zm29.品目: INTEGER = 1234567    -- 数値型
zp02.品目: TEXT = "0001234567"  -- 文字列型
```

### 解決方法
1. **データ型分析**: 全テーブルの型不整合を検出
2. **データ型統一**: 品目コード系を文字列型に統一
3. **ゼロパディング**: 適切な桁数（10桁）で統一

### 推奨ワークフロー
```
全件データ更新 → データ型分析 → データ型統一 → Access連携
```

## 今後の拡張

### 1. 自動化機能
- 定期実行スケジュール
- ファイル監視による自動処理
- データ型統一の自動実行

### 2. 分析機能の強化
- CM分類別の統計情報
- 基板タイプ別の分析
- データ品質レポート

### 3. 外部連携
- Accessデータベースとの同期
- サーバーDBへの自動アップロード
- 型安全なデータ転送

## 関連ファイル

- `src/core/sqlite_gui_tool/admin_tab.py`: メイン処理
- `src/core/sqlite_gui_tool/launcher_tab.py`: スクリプト実行管理
- `src/core/sqlite_gui_tool/app.py`: タブ統合
- `a_everyday/z_maradl.py`: 元の処理（参考）
- `a_everyday/z_view_pcmaster.py`: 元の処理（参考）
- `a_everyday/z_Parsed Pc Master Diff Logger.py`: 元の処理（参考）