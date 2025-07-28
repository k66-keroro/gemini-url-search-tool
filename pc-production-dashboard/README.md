# PC製造専用ダッシュボード v1.0

PC製造部門向けの生産実績ダッシュボード（Embeddable-Python配布用）

## 🚀 クイックスタート

### 1. データ統合
```cmd
python app/data_loader_simple.py
```

### 2. ダッシュボード起動
```cmd
python app/main.py
```

### 3. バッチファイル起動
```cmd
start_dashboard.bat
```

## 📊 主な機能

- **過去データ統合**: 2024/04-2025/06の月次ZM29データ
- **当日データ統合**: MESからのリアルタイムデータ
- **月別週区分集計**: 月の最初の月曜日基準の週別集計
- **インタラクティブダッシュボード**: Streamlit + Plotly
- **CSV出力**: 明細データのダウンロード

## 🔧 技術仕様

- **Python**: 3.11 (Embeddable版対応)
- **フレームワーク**: Streamlit, Plotly
- **データベース**: SQLite
- **データソース**: ZM29月次データ + KANSEI_JISSEKI当日データ

## 📁 ファイル構成

```
pc-production-dashboard/
├── app/
│   ├── main.py                    # エントリーポイント
│   ├── dashboard.py               # Streamlitダッシュボード
│   └── data_loader_simple.py      # データローダー
├── data/
│   ├── current/                   # 当日データ
│   ├── zm29_Monthly_performance/  # 過去データ
│   └── sqlite/                    # SQLiteDB
├── config.json                    # 設定ファイル
└── start_dashboard.bat            # 起動バッチ
```

## 💰 単価推定システム

品目コードパターンベースの推定単価:
- `P0A`: 5,000円（PCB基板系）
- `P00`: 3,000円（部品系）
- `IK-`: 8,000円（制御基板）
- `PK-`: 6,000円（電源基板）
- `CK-`: 7,000円（制御系）
- `MK-`: 4,000円（その他基板）

## 🎯 配布準備完了

Embeddable-Python環境での配布に対応済み

---

**バージョン**: v1.0  
**作成日**: 2025年1月28日