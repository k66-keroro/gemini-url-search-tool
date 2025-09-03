# Gemini URL Search Tool - セットアップガイド

## 📋 概要
このツールは、Web検索→AI絞り込み→サイト内容要約を行うスマート検索ツールです。

## 🚀 クイックスタート

### 1. 必要な環境
- Python 3.8以上
- Gemini API キー（Google AI Studio）

### 2. インストール手順

#### Step 1: リポジトリをクローン
```bash
git clone https://github.com/k66-keroro/gemini-url-search-tool.git
cd gemini-url-search-tool
```

#### Step 2: 仮想環境作成（推奨）
```bash
# 仮想環境作成
python -m venv venv

# 仮想環境有効化
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

#### Step 3: 依存関係インストール
```bash
pip install streamlit requests beautifulsoup4 google-generativeai python-dotenv
```

#### Step 4: 環境設定
```bash
# .envファイルを作成
cp .env.example .env
```

`.env`ファイルを編集してGemini API キーを設定：
```
GEMINI_API_KEY=your_api_key_here
```

### 3. Gemini API キー取得方法

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. "Create API Key" をクリック
4. 生成されたキーを`.env`ファイルに設定

### 4. アプリケーション起動

#### 推奨: スマート概要・詳細ツール
```bash
streamlit run smart_overview_detail.py --server.port 8510
```

#### その他のツール
```bash
# AI絞り込み検索
streamlit run smart_search_filter.py --server.port 8504

# 直接URL分析
streamlit run direct_url_analyzer.py --server.port 8503

# 完全検索ワークフロー
streamlit run working_content_search.py --server.port 8502
```

### 5. ブラウザでアクセス
- http://localhost:8510 （推奨ツール）

## 🎯 各ツールの特徴

### smart_overview_detail.py（推奨）
- **概要一覧→詳細分析の理想的なUI**
- 関連度による色分け表示
- カード形式の見やすい一覧
- ワンクリックで詳細分析

### smart_search_filter.py
- AI絞り込み機能付き検索
- 複数サイトの統合分析
- 段階的な分析プロセス

### direct_url_analyzer.py
- 直接URLを入力して分析
- 単一サイトの詳細分析
- テスト用URL付き

### working_content_search.py
- 完全な検索→要約ワークフロー
- 複数サイトの比較分析
- 統合レポート生成

## 🔧 トラブルシューティング

### よくある問題

#### 1. API キーエラー
```
❌ Gemini API key not found
```
**解決方法**: `.env`ファイルにAPI キーが正しく設定されているか確認

#### 2. モジュールが見つからない
```
ModuleNotFoundError: No module named 'streamlit'
```
**解決方法**: 
```bash
pip install streamlit requests beautifulsoup4 google-generativeai python-dotenv
```

#### 3. ポートが使用中
```
Port 8510 is already in use
```
**解決方法**: 別のポートを使用
```bash
streamlit run smart_overview_detail.py --server.port 8511
```

#### 4. 検索結果が取得できない
- インターネット接続を確認
- ファイアウォール設定を確認
- 別の検索キーワードを試す

#### 5. 仮想環境の問題
```bash
# 仮想環境を削除して再作成
rm -rf venv  # Mac/Linux
rmdir /s venv  # Windows

python -m venv venv
venv\Scripts\activate  # Windows
pip install streamlit requests beautifulsoup4 google-generativeai python-dotenv
```

## 📚 使用方法

### 基本的な使い方
1. **検索キーワード入力** - 調べたいトピックを入力
2. **概要確認** - AI生成の概要一覧を確認
3. **詳細分析** - 気になるサイトの詳細分析を実行
4. **結果活用** - 要約結果を参考に情報収集

### 効果的な検索キーワード例
- `Python 機械学習`
- `React フロントエンド開発`
- `Docker コンテナ技術`
- `AWS クラウドサービス`

## 🛠️ 開発者向け情報

### プロジェクト構造
```
gemini-url-search-tool/
├── smart_overview_detail.py    # 推奨メインツール
├── smart_search_filter.py      # AI絞り込み検索
├── direct_url_analyzer.py      # 直接URL分析
├── working_content_search.py   # 完全ワークフロー
├── .env.example               # 環境変数テンプレート
├── SETUP_GUIDE.md            # このファイル
└── src/                      # コアライブラリ（開発中）
```

### カスタマイズ
- 検索ソースの追加: `search_with_multiple_sources()` 関数を編集
- UI改善: Streamlitコンポーネントをカスタマイズ
- AI分析の調整: プロンプトを編集

## 📞 サポート

問題が発生した場合：
1. このガイドのトラブルシューティングを確認
2. [GitHub Issues](https://github.com/k66-keroro/gemini-url-search-tool/issues) で報告
3. 環境情報（OS、Pythonバージョン等）を含めて報告

## 🎉 楽しい検索ライフを！

このツールで効率的な情報収集をお楽しみください！