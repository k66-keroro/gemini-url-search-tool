# 🔍 Gemini URL Search Tool

AI搭載のスマート検索・コンテンツ分析ツール

## ✨ 特徴

- **🎯 スマート検索**: 複数ソースから関連性の高いサイトを自動選別
- **🤖 AI分析**: Gemini AIによる高品質なコンテンツ要約
- **📋 理想的なUI**: 概要一覧→詳細分析の直感的なワークフロー
- **🌐 多様なソース**: Wikipedia、技術文書、公式サイトなど
- **🎨 視覚的表示**: 関連度による色分け、カード形式の見やすい表示

## 🚀 クイックスタート

### Windows
```bash
# 1. リポジトリをクローン
git clone https://github.com/k66-keroro/gemini-url-search-tool.git
cd gemini-url-search-tool

# 2. 簡単起動（自動セットアップ）
start.bat
```

### Mac/Linux
```bash
# 1. リポジトリをクローン
git clone https://github.com/k66-keroro/gemini-url-search-tool.git
cd gemini-url-search-tool

# 2. 実行権限付与
chmod +x start.sh

# 3. 簡単起動（自動セットアップ）
./start.sh
```

### 手動セットアップ
```bash
# 1. 仮想環境作成
python -m venv venv

# 2. 仮想環境有効化
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# 3. 依存関係インストール
pip install -r requirements.txt

# 4. 環境設定
cp .env.example .env
# .envファイルにGemini API キーを設定

# 5. アプリ起動
streamlit run smart_overview_detail.py --server.port 8510
```

## 🔑 API キー設定

1. [Google AI Studio](https://makersuite.google.com/app/apikey) でAPI キーを取得
2. `.env`ファイルに設定:
```
GEMINI_API_KEY=your_api_key_here
```

## 🎯 使用方法

1. **検索キーワード入力** - 調べたいトピックを入力
2. **概要確認** - AI生成の概要一覧を確認（関連度で色分け）
3. **詳細分析** - 気になるサイトをクリックして詳細分析
4. **結果活用** - 高品質な要約を情報収集に活用

## 📱 利用可能なツール

| ツール | 説明 | ポート |
|--------|------|--------|
| `smart_overview_detail.py` | **推奨**: 概要一覧→詳細分析 | 8510 |
| `smart_search_filter.py` | AI絞り込み検索 | 8504 |
| `direct_url_analyzer.py` | 直接URL分析 | 8503 |
| `working_content_search.py` | 完全ワークフロー | 8502 |

## 📚 詳細ドキュメント

- [📋 セットアップガイド](SETUP_GUIDE.md) - 詳細なインストール手順
- [📖 完全版README](README.md) - 詳細な技術仕様とAPI
- [📖 ユーザーマニュアル](docs/USER_MANUAL.md) - 使用方法の詳細

## 🎉 楽しい検索ライフを！

効率的な情報収集をお楽しみください！