---
title: Git導入ガイドライン
inclusion: always
---

# Git導入ガイドライン

## Git導入の目的

1. **バージョン管理**:
   - コードの変更履歴を追跡
   - 複数の開発者による並行開発をサポート
   - 問題発生時に以前の状態に戻せる

2. **コラボレーション**:
   - 変更の共有と統合が容易
   - コードレビューの実施
   - 作業の分担と進捗管理

3. **バックアップ**:
   - コードの安全な保存
   - 複数の場所での冗長性確保

## Git導入手順

### 1. Gitのインストール

```bash
# Windows
# https://git-scm.com/download/win からインストーラをダウンロード

# 確認
git --version
```

### 2. リポジトリの初期化

```bash
# 既存プロジェクトをGitリポジトリに変換
cd claude-test
git init

# 初期設定
git config --local user.name "Your Name"
git config --local user.email "your.email@example.com"
```

### 3. .gitignoreファイルの作成

```
# Python関連
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# データベース
*.db
*.db-journal
*.sqlite
*.sqlite3

# ログ
logs/
*.log

# 一時ファイル
.DS_Store
.idea/
.vscode/
*.swp
*.swo

# 環境設定
.env
.venv
venv/
ENV/

# データファイル（必要に応じて調整）
data/raw/*
data/sqlite/*
!data/raw/.gitkeep
!data/sqlite/.gitkeep
```

### 4. 初回コミット

```bash
# すべてのファイルをステージング
git add .

# 初回コミット
git commit -m "Initial commit"
```

### 5. リモートリポジトリの設定（オプション）

```bash
# GitHubなどのリモートリポジトリを追加
git remote add origin https://github.com/username/claude-test.git

# リモートにプッシュ
git push -u origin main
```

## ブランチ戦略

### 基本ブランチ

- **main**: 安定版のコード（本番環境用）
- **develop**: 開発中のコード（次回リリース用）

### 機能ブランチ

- **feature/xxx**: 新機能の開発
- **bugfix/xxx**: バグ修正
- **hotfix/xxx**: 緊急のバグ修正（本番環境用）

## コミットメッセージのガイドライン

```
[種類] 簡潔な要約（50文字以内）

詳細な説明（必要な場合）
```

### コミットの種類

- **feat**: 新機能
- **fix**: バグ修正
- **docs**: ドキュメントのみの変更
- **style**: コードの意味に影響しない変更（フォーマット等）
- **refactor**: バグ修正や機能追加ではないコード変更
- **perf**: パフォーマンス向上のための変更
- **test**: テストの追加・修正
- **chore**: ビルドプロセスやツールの変更

## Git操作の基本コマンド

```bash
# 状態確認
git status

# 変更の確認
git diff

# 変更をステージング
git add <file>

# コミット
git commit -m "メッセージ"

# ブランチ作成
git branch <branch-name>

# ブランチ切り替え
git checkout <branch-name>

# ブランチ作成と切り替えを同時に行う
git checkout -b <branch-name>

# 変更を取得
git pull

# 変更をプッシュ
git push
```

## Git使用時の注意点

1. **大きなファイルの管理**:
   - データファイルなど大きなファイルはGitで管理しない
   - 必要に応じてGit LFSの使用を検討

2. **機密情報**:
   - パスワードやAPIキーなどの機密情報はコミットしない
   - 環境変数や設定ファイルを使用

3. **コンフリクト解決**:
   - 同じファイルを複数人で編集する場合はコンフリクトに注意
   - こまめにpullして最新の状態を維持