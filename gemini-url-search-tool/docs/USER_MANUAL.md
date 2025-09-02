# Gemini URL Search Tool - ユーザーマニュアル

🔍 **Gemini URL Search Tool** の完全ユーザーガイド

## 目次

1. [はじめに](#はじめに)
2. [インストールと初期設定](#インストールと初期設定)
3. [基本的な使い方](#基本的な使い方)
4. [機能詳細ガイド](#機能詳細ガイド)
5. [設定とカスタマイズ](#設定とカスタマイズ)
6. [よくある質問](#よくある質問)
7. [トラブルシューティング](#トラブルシューティング)

---

## はじめに

### このツールについて

Gemini URL Search Tool は、Google Gemini AI を活用した高度なWeb情報収集ツールです。キーワード検索から関連URLの発見、コンテンツの自動要約まで、研究や開発作業を効率化します。

### 主な特徴

- 🔍 **インテリジェント検索**: AIによる関連性の高いURL検索
- 📄 **自動要約**: Webページの内容を構造化して要約
- 🔧 **部品仕様検索**: メーカー名と品番による専門検索
- 💾 **履歴管理**: 検索結果と分析の保存・管理
- 📊 **分析ダッシュボード**: 検索パフォーマンスの可視化
- ⚙️ **カスタマイズ**: 豊富な設定オプション

---

## インストールと初期設定

### システム要件

- **Python**: 3.8以上
- **OS**: Windows, macOS, Linux
- **メモリ**: 最小512MB、推奨1GB以上
- **ストレージ**: 最小100MB
- **ネットワーク**: インターネット接続必須

### ステップ1: プロジェクトの準備

```bash
# プロジェクトディレクトリに移動
cd gemini-url-search-tool

# Python仮想環境の作成（推奨）
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### ステップ2: 依存関係のインストール

```bash
# 必要なパッケージをインストール
pip install -r requirements.txt
```

### ステップ3: 環境設定

```bash
# 環境変数ファイルの作成
cp .env.example .env
```

`.env` ファイルを編集して、Gemini API キーを設定：

```env
GEMINI_API_KEY=your_actual_api_key_here
```

### ステップ4: Gemini API キーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたAPIキーを `.env` ファイルに貼り付け

### ステップ5: アプリケーションの起動

```bash
# アプリケーションを起動
streamlit run main.py
```

ブラウザが自動的に開き、`http://localhost:8501` でアプリケーションにアクセスできます。

---

## 基本的な使い方

### 初回起動時の確認

アプリケーションが正常に起動すると、以下の画面が表示されます：

- 🔍 **検索タブ**: メイン機能
- 📊 **ダッシュボードタブ**: 統計情報
- 📈 **詳細分析タブ**: 詳細な分析結果
- ⚙️ **設定タブ**: 各種設定

### 基本的な検索フロー

#### 1. 検索タイプの選択

**一般検索（フリーワード）**
- キーワードやフレーズで幅広く検索
- 例：「Python 機械学習 入門」

**部品仕様検索**
- メーカー名と品番で技術文書を検索
- 例：メーカー「Arduino」、品番「UNO R3」

#### 2. 検索の実行

1. 検索タイプを選択
2. キーワードまたはメーカー名・品番を入力
3. 「検索実行」ボタンをクリック
4. 検索結果の表示を待つ

#### 3. 結果の確認と活用

- **結果一覧**: 関連度順に表示
- **プレビュー**: 各結果の概要を確認
- **詳細分析**: 興味のあるURLを選択して詳細分析
- **保存**: 有用な結果を保存
- **評価**: 結果の有用性を5段階で評価

---

## 機能詳細ガイド

### 🔍 検索機能

#### 一般検索（フリーワード）

**使用場面**
- 技術情報の調査
- 学習リソースの発見
- 業界動向の把握

**検索のコツ**
```
✅ 良い例：
- "React hooks 使い方 2024"
- "機械学習 初心者 チュートリアル"
- "AWS Lambda Python 設定"

❌ 避けるべき例：
- "プログラミング"（曖昧すぎる）
- "エラー"（具体性に欠ける）
```

#### 部品仕様検索

**使用場面**
- 電子部品の仕様確認
- データシートの検索
- 互換部品の調査

**入力例**
```
メーカー名: "Texas Instruments"
品番: "LM358"
→ TIのLM358オペアンプの公式データシートを優先的に検索
```

### 📄 コンテンツ分析機能

#### 自動要約

検索結果から選択したURLのコンテンツを自動的に分析し、以下の情報を抽出：

- **概要**: ページの主要内容
- **キーポイント**: 重要な情報の箇条書き
- **技術仕様**: 技術的な詳細（該当する場合）
- **関連リンク**: 参考になる関連URL

#### 分析結果の活用

- **保存**: 分析結果をローカルデータベースに保存
- **エクスポート**: 結果をテキストファイルとして出力
- **評価**: 分析の有用性を評価してシステムを改善

### 💾 データ管理機能

#### 検索履歴

- **自動保存**: 全ての検索が自動的に記録
- **検索**: 過去の検索を条件で絞り込み
- **再実行**: 過去の検索を簡単に再実行

#### 保存済みコンテンツ

- **分類**: カテゴリ別に整理
- **タグ付け**: カスタムタグで管理
- **全文検索**: 保存したコンテンツ内を検索

### 📊 分析・評価機能

#### パフォーマンスダッシュボード

**表示される指標**
- 検索成功率
- 平均検索時間
- 最も検索されるキーワード
- 保存率の高いコンテンツタイプ

**活用方法**
- 検索パターンの把握
- 効果的なキーワードの発見
- システムパフォーマンスの監視

---

## 設定とカスタマイズ

### ⚙️ 設定画面の使い方

設定画面では以下の項目をカスタマイズできます：

#### API設定

```json
{
  "gemini": {
    "models": ["gemini-2.0-flash-exp", "gemini-1.5-flash"],
    "max_retries": 3,
    "timeout": 30
  }
}
```

- **使用モデル**: 利用するGeminiモデルの選択
- **リトライ回数**: API失敗時の再試行回数
- **タイムアウト**: API応答の待機時間

#### 検索設定

```json
{
  "search": {
    "max_results": 10,
    "enable_caching": true,
    "cache_duration_hours": 24
  }
}
```

- **最大結果数**: 1回の検索で取得する結果数
- **キャッシュ**: 検索結果のキャッシュ機能
- **キャッシュ期間**: キャッシュの有効期間

#### コンテンツ処理設定

```json
{
  "content": {
    "max_content_size": 1048576,
    "summary_max_length": 1000,
    "extraction_timeout": 60
  }
}
```

- **最大コンテンツサイズ**: 処理するコンテンツの上限
- **要約最大長**: 生成する要約の最大文字数
- **抽出タイムアウト**: コンテンツ取得の制限時間

### 高度な設定

#### プロキシ設定

企業環境でプロキシが必要な場合：

```env
# .envファイルに追加
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=https://proxy.company.com:8080
```

#### ログ設定

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/app.log",
    "max_size_mb": 10
  }
}
```

- **DEBUG**: 詳細なデバッグ情報
- **INFO**: 一般的な動作情報
- **WARNING**: 警告レベルの情報
- **ERROR**: エラー情報のみ

---

## よくある質問

### Q1: 検索結果が表示されない

**A:** 以下を確認してください：
1. インターネット接続
2. Gemini API キーの設定
3. API利用制限の確認

### Q2: 要約の品質を向上させたい

**A:** 以下の方法を試してください：
1. より具体的なキーワードで検索
2. 要約最大長の調整
3. 異なるGeminiモデルの使用

### Q3: 大量のデータを処理したい

**A:** 設定を調整してください：
```json
{
  "content": {
    "max_content_size": 2097152,
    "chunk_size": 8192
  }
}
```

### Q4: 検索が遅い

**A:** パフォーマンス改善方法：
1. キャッシュ機能を有効化
2. 最大結果数を減らす
3. タイムアウト時間を調整

### Q5: データベースが大きくなりすぎた

**A:** データベースのメンテナンス：
```python
# 古いデータの削除（30日以上前）
python -c "
from src.models.database import DatabaseManager
db = DatabaseManager('data/search_results.db')
db.cleanup_old_records(days=30)
"
```

---

## トラブルシューティング

### 一般的な問題と解決方法

#### 🚨 API認証エラー

**症状**: `Authentication failed` エラー

**解決方法**:
1. `.env`ファイルのAPIキーを確認
2. APIキーの有効性を確認
3. API利用制限を確認

```bash
# APIキーの確認
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('GEMINI_API_KEY')[:10] + '...')
"
```

#### 🚨 メモリ不足エラー

**症状**: アプリケーションが突然終了

**解決方法**:
1. コンテンツサイズ制限を下げる
2. 不要なキャッシュを削除
3. データベースをクリーンアップ

```bash
# キャッシュのクリア
rm -rf data/cache/*

# データベースの最適化
python -c "
from src.models.database import DatabaseManager
db = DatabaseManager('data/search_results.db')
db.vacuum()
"
```

#### 🚨 ネットワークエラー

**症状**: `Connection timeout` エラー

**解決方法**:
1. インターネット接続を確認
2. プロキシ設定を確認
3. タイムアウト時間を延長

### ログの確認方法

```bash
# 最新のログを確認
tail -f logs/app.log

# エラーログのみを確認
grep "ERROR" logs/app.log

# 特定の時間のログを確認
grep "2024-01-15 10:" logs/app.log
```

### パフォーマンス監視

```python
# メモリ使用量の確認
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
print(f"CPU: {process.cpu_percent():.1f}%")
```

---

## サポート情報

### 技術サポート

問題が解決しない場合は、以下の情報を含めてお問い合わせください：

1. **エラーメッセージ**: 完全なエラーメッセージ
2. **環境情報**: OS、Pythonバージョン
3. **設定ファイル**: `config.json`（APIキーは除く）
4. **ログファイル**: `logs/app.log`の関連部分
5. **再現手順**: エラーが発生する具体的な手順

### 更新とメンテナンス

#### 定期メンテナンス

```bash
# 月次メンテナンススクリプト
python -c "
from src.models.database import DatabaseManager
from pathlib import Path
import shutil

# データベースの最適化
db = DatabaseManager('data/search_results.db')
db.cleanup_old_records(days=30)
db.vacuum()

# ログファイルのローテーション
log_file = Path('logs/app.log')
if log_file.exists() and log_file.stat().st_size > 10 * 1024 * 1024:
    shutil.move(log_file, log_file.with_suffix('.log.old'))

print('メンテナンス完了')
"
```

#### アップデート確認

```bash
# 依存関係の更新確認
pip list --outdated

# 特定パッケージの更新
pip install --upgrade streamlit google-generativeai
```

---

## 付録

### キーボードショートカット

| ショートカット | 機能 |
|---------------|------|
| `Ctrl + R` | ページリロード |
| `Ctrl + Shift + R` | キャッシュクリア後リロード |
| `F5` | ページ更新 |

### 設定ファイルリファレンス

完全な設定例：

```json
{
  "app": {
    "name": "Gemini URL Search Tool",
    "version": "1.0.0",
    "debug": false
  },
  "gemini": {
    "models": ["gemini-2.0-flash-exp", "gemini-1.5-flash"],
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
    "page_title": "Gemini URL Search Tool",
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

---

**最終更新**: 2024年1月
**バージョン**: 1.0.0

このマニュアルについてご質問やご提案がございましたら、お気軽にお問い合わせください。