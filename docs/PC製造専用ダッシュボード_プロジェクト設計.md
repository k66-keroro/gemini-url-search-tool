# PC製造専用ダッシュボード - プロジェクト設計

## プロジェクト分離の理由

### 現在のclaude-test（汎用データ処理ツール）
- 多様なデータソース対応
- 汎用的なSQLite管理機能
- 開発・検証用途

### 新規PC製造専用プロジェクト（配布用）
- PC製造業務に特化
- Embeddable-Python対応
- エンドユーザー配布用

## 新規プロジェクト構成案

```
pc-production-dashboard/
├── app/                           # アプリケーション本体
│   ├── main.py                    # エントリーポイント
│   ├── dashboard.py               # Streamlitダッシュボード
│   ├── data_loader.py             # データ読み込み専用
│   └── config.py                  # 設定管理
├── data/                          # データフォルダ
│   ├── current/                   # 当日データ（1時間毎更新）
│   │   ├── KANSEI_JISSEKI.txt
│   │   ├── KOUSU_JISSEKI.txt
│   │   ├── KOUTEI_JISSEKI.txt
│   │   └── SASIZU_JISSEKI.txt
│   ├── historical/                # 過去データ（月次）
│   │   ├── 2024/
│   │   │   ├── ZM29_202404.txt
│   │   │   └── ...
│   │   └── 2025/
│   │       ├── ZM29_202501.txt
│   │       └── ...
│   └── sqlite/
│       └── pc_production.db       # PC製造専用DB
├── python-embedded/               # Embeddable Python
│   ├── python.exe
│   ├── python311.zip
│   └── Lib/
├── requirements.txt               # 依存関係
├── setup.py                       # セットアップスクリプト
├── config.json                    # 設定ファイル
└── README.md                      # 使用方法
```

## 機能仕様

### 1. データ統合機能
- **過去データ**: 2024/04-2025/06の月次ZM29データ
- **当日データ**: MESからの1時間毎更新データ
- **自動統合**: 過去データ + 当日データの統合表示

### 2. 週区分計算（月別週単位）
```python
def calculate_monthly_week(date):
    """月別の週区分を計算（1-5週）"""
    # 月の最初の月曜日を基準とした週区分
    first_day = date.replace(day=1)
    first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
    
    if date < first_monday:
        return 1
    else:
        days_from_first_monday = (date - first_monday).days
        return min(days_from_first_monday // 7 + 2, 5)
```

### 3. リアルタイム更新機能
- **自動リフレッシュ**: 1時間毎のデータ更新検知
- **差分処理**: 新規データのみ処理
- **ステータス表示**: 最終更新時刻の表示

### 4. 4つの実績データ統合
- **KANSEI_JISSEKI.txt**: 完成実績（ZM29ベース）
- **KOUSU_JISSEKI.txt**: 工数実績（標準時間比較）
- **KOUTEI_JISSEKI.txt**: 工程実績（進捗管理）
- **SASIZU_JISSEKI.txt**: 製造指図サマリ

## Embeddable-Python配布設計

### 1. ポータブル構成
```
PC製造ダッシュボード_v1.0/
├── start_dashboard.bat            # 起動バッチファイル
├── python-embedded/               # Python実行環境
├── app/                          # アプリケーション
├── data/                         # データフォルダ
└── config/                       # 設定ファイル
```

### 2. 起動バッチファイル
```batch
@echo off
cd /d %~dp0
python-embedded\python.exe app\main.py
pause
```

### 3. 自動セットアップ機能
- 初回起動時の環境構築
- 必要なライブラリの自動インストール
- データフォルダの自動作成

## 開発フェーズ

### Phase 1: 基盤構築（1-2週間）
1. 新規プロジェクト作成
2. 過去データ統合機能
3. 月別週区分計算
4. 基本ダッシュボード

### Phase 2: リアルタイム対応（1週間）
1. 当日データ読み込み
2. 自動更新機能
3. 差分処理機能

### Phase 3: 多実績統合（1-2週間）
1. 工数実績統合
2. 工程実績統合
3. 製造指図統合
4. 統合ダッシュボード

### Phase 4: 配布パッケージ（1週間）
1. Embeddable-Python統合
2. インストーラー作成
3. ユーザーマニュアル作成

## 技術選定

### コア技術
- **Python**: 3.11 (Embeddable版)
- **Streamlit**: ダッシュボードフレームワーク
- **SQLite**: ローカルデータベース
- **Pandas**: データ処理
- **Plotly**: 可視化

### 配布技術
- **Python Embeddable**: ポータブル実行環境
- **PyInstaller**: 実行ファイル化（オプション）
- **NSIS**: インストーラー作成（オプション）

## 現在のclaude-testとの関係

### 開発段階での連携
1. **プロトタイプ開発**: claude-testで機能検証
2. **データ処理ロジック**: 共通部分の移植
3. **テスト**: claude-testでデータ品質確認

### 本番での独立性
- PC製造専用プロジェクトは完全独立
- claude-testへの依存なし
- 単体での配布・運用

## 次のアクション

1. **新規プロジェクト作成**: `pc-production-dashboard` フォルダ作成
2. **過去データ統合**: 月次ZM29データの統合処理
3. **週区分計算**: 月別週単位計算の実装
4. **プロトタイプ**: 基本ダッシュボードの作成

この設計でよろしいでしょうか？まずは新規プロジェクトの作成から始めましょうか？