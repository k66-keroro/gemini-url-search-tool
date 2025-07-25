# PC 生産実績ダッシュボード

既存の Access ロジックを Streamlit で再現したインタラクティブなダッシュボードです。

## 機能

### 📈 週別集計

- MRP 管理者別の週別生産実績
- 週別集計テーブル
- 週別棒グラフ

### 📅 日別集計

- 日別生産実績の詳細表示
- 日別トレンドグラフ
- MRP 管理者別日別推移

### 📋 明細データ

- 生産実績の詳細明細
- 品目コード・品目テキスト検索
- CSV ダウンロード機能

### 📊 分析

- MRP 管理者別構成比（円グラフ）
- 生産金額上位 10 品目（棒グラフ）
- 週別・MRP 管理者別ヒートマップ

## データソース

- **データベース**: `data/sqlite/main.db`
- **テーブル**: `ZM29`
- **条件**: `MRP管理者 LIKE 'PC%'` かつ `完成数 > 0`

## 使用方法

### 1. 簡単実行（推奨）

```bash
python run_dashboard.py
```

### 2. 手動実行

```bash
# 依存パッケージのインストール
pip install -r streamlit_apps/requirements.txt

# ダッシュボード起動
streamlit run streamlit_apps/pc_production_dashboard.py
```

### 3. ブラウザアクセス

- 自動で開かない場合: http://localhost:8501

## フィルター機能

### サイドバー

- **日付範囲選択**: 期間を指定してデータをフィルタ
- **MRP 管理者選択**: 特定の MRP 管理者のみ表示

### 明細タブ

- **品目コード検索**: 部分一致検索
- **品目テキスト検索**: 部分一致検索

## 週区分について

既存の Access ロジックを再現：

- 週区分 = `週番号 % 4 + 1` (1-4 の値)
- 月曜日始まりの週計算
- 平日・休日の識別

## データ集計ロジック

### 日別集計

```sql
-- 元のAccessクエリを再現
SELECT
    転記日付,
    週区分,
    SUM(CASE WHEN MRP管理者='PC1' THEN 金額 ELSE 0 END) AS PC1,
    SUM(CASE WHEN MRP管理者='PC2' THEN 金額 ELSE 0 END) AS PC2,
    -- ... 他のMRP管理者
    SUM(金額) AS 日別金額
FROM ZM29
WHERE MRP管理者 LIKE 'PC%'
GROUP BY 転記日付, 週区分
```

### 週別集計

```sql
-- 週別の集計
SELECT
    週区分,
    SUM(CASE WHEN MRP管理者='PC1' THEN 金額 ELSE 0 END) AS PC1,
    SUM(CASE WHEN MRP管理者='PC2' THEN 金額 ELSE 0 END) AS PC2,
    -- ... 他のMRP管理者
    SUM(金額) AS 合計
FROM ZM29
WHERE MRP管理者 LIKE 'PC%'
GROUP BY 週区分
```

## カスタマイズ

### 新しい MRP 管理者の追加

`pc_production_dashboard.py`の以下の部分を修正：

```python
# MRP管理者のフィルタ条件
WHERE MRP管理者 LIKE 'PC%'
```

### 週区分の計算方法変更

```python
# 週区分の計算
df['週区分'] = df['転記日付'].dt.isocalendar().week % 4 + 1
```

### グラフの色やスタイル変更

Plotly の設定を変更してカスタマイズ可能

## トラブルシューティング

### データが表示されない

1. `data/sqlite/main.db`が存在するか確認
2. ZM29 テーブルに PC 関連データがあるか確認
3. 日付範囲フィルターを確認

### パフォーマンスが遅い

1. 日付範囲を狭める
2. 特定の MRP 管理者のみ選択
3. データベースにインデックスを追加

### エラーが発生する

1. 依存パッケージが正しくインストールされているか確認
2. Python のバージョンが 3.8 以上か確認
3. データベースファイルの権限を確認

## 既存 Access との対応

| Access 機能          | Streamlit 対応     |
| -------------------- | ------------------ |
| pc*生産実績*明細     | 明細データタブ     |
| pc*生産実績*日別集計 | 日別集計タブ       |
| pc*生産実績*週別集計 | 週別集計タブ       |
| m_calendar           | 自動計算（週区分） |
| 集計\_mrp/日別生産   | ピボットテーブル   |

## 今後の拡張予定

- [ ] 月別集計機能
- [ ] 予実対比機能
- [ ] アラート機能
- [ ] 自動更新機能
- [ ] エクスポート機能の拡充
