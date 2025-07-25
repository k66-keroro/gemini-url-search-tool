# マスターテーブルの管理ガイド

## マスターテーブルとは

マスターテーブルとは、システム内で基準となる静的なデータを格納するテーブルです。例えば、商品コード、部門コード、取引先コードなどの基準情報が該当します。これらのデータは頻繁に変更されず、他のテーブルから参照されることが多いという特徴があります。

## マスターテーブルと更新データの管理方法

SQLiteではデータベースのパーティション機能は直接サポートされていませんが、以下の方法でマスターテーブルと日々更新されるデータを効果的に管理することができます。

### 1. 命名規則による区別

マスターテーブルと更新データテーブルを命名規則で区別します。

```
# マスターテーブルの命名例
m_product  # 商品マスター
m_customer  # 顧客マスター
m_department  # 部門マスター

# 更新データテーブルの命名例
t_transaction  # 取引データ
t_inventory  # 在庫データ
t_sales  # 売上データ
```

### 2. スキーマ（ATTACH DATABASE）の活用

SQLiteの`ATTACH DATABASE`機能を使用して、論理的に別のデータベースとして管理することができます。

```sql
-- マスターデータ用のデータベースをアタッチ
ATTACH DATABASE 'master.db' AS master;

-- 更新データ用のデータベースをアタッチ
ATTACH DATABASE 'transaction.db' AS transaction;

-- マスターテーブルの作成
CREATE TABLE master.m_product (
    product_code TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    price INTEGER
);

-- 更新データテーブルの作成
CREATE TABLE transaction.t_sales (
    id INTEGER PRIMARY KEY,
    product_code TEXT,
    quantity INTEGER,
    sale_date TEXT,
    FOREIGN KEY (product_code) REFERENCES master.m_product(product_code)
);
```

### 3. 別々のデータベースファイルの使用

マスターデータと更新データを完全に別々のデータベースファイルで管理する方法です。

```
master.db  # マスターデータ用
transaction.db  # 更新データ用
```

アプリケーション側で両方のデータベースに接続し、必要に応じてデータを結合します。

## 推奨アプローチ

プロジェクトの規模や要件に応じて、以下のアプローチを推奨します：

### 小〜中規模のプロジェクト

**単一データベース + 命名規則**

- マスターテーブルと更新データテーブルを同じデータベースファイル（main.db）に格納
- 命名規則で区別（m_xxx, t_xxx）
- バックアップ時にはデータベース全体をバックアップ

### 中〜大規模のプロジェクト

**ATTACH DATABASEによる論理的分離**

- マスターデータと更新データを論理的に分離
- 必要に応じて結合クエリを実行
- バックアップはデータベースごとに個別に実行可能

### 大規模プロジェクト

**完全に別々のデータベースファイル**

- マスターデータと更新データを別々のデータベースファイルで管理
- アプリケーション側で両方のデータベースに接続
- バックアップや管理を個別に実行

## マスターテーブルの更新管理

マスターテーブルは頻繁に更新されないものの、時には更新が必要になります。以下の方法で更新を管理します：

### 1. バージョン管理

マスターテーブルにバージョン情報を持たせ、更新履歴を管理します。

```sql
CREATE TABLE m_product_version (
    version_id INTEGER PRIMARY KEY,
    update_date TEXT NOT NULL,
    description TEXT
);
```

### 2. 履歴テーブルの作成

マスターテーブルの変更履歴を記録するテーブルを作成します。

```sql
CREATE TABLE m_product_history (
    history_id INTEGER PRIMARY KEY,
    product_code TEXT NOT NULL,
    product_name TEXT NOT NULL,
    price INTEGER,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    FOREIGN KEY (product_code) REFERENCES m_product(product_code)
);
```

### 3. トリガーの活用

マスターテーブルが更新された際に、自動的に履歴テーブルに記録するトリガーを設定します。

```sql
CREATE TRIGGER trg_product_update
AFTER UPDATE ON m_product
FOR EACH ROW
BEGIN
    -- 古いレコードの有効期限を設定
    UPDATE m_product_history
    SET valid_to = datetime('now')
    WHERE product_code = OLD.product_code
    AND valid_to IS NULL;
    
    -- 新しいレコードを履歴テーブルに挿入
    INSERT INTO m_product_history (
        product_code, product_name, price, valid_from, valid_to
    ) VALUES (
        NEW.product_code, NEW.product_name, NEW.price, datetime('now'), NULL
    );
END;
```

## バックアップ戦略

マスターテーブルと更新データでは、バックアップの頻度や方法が異なる場合があります。

### マスターデータのバックアップ

- 変更が少ないため、変更時にのみバックアップを取得
- 完全バックアップを定期的に実施（週1回など）

### 更新データのバックアップ

- 頻繁に変更されるため、定期的なバックアップが必要（日次など）
- 増分バックアップやWALファイルのバックアップを検討

## まとめ

SQLiteではパーティション機能は直接サポートされていませんが、命名規則、ATTACH DATABASE、別々のデータベースファイルなどの方法を使用して、マスターテーブルと更新データを効果的に管理することができます。プロジェクトの規模や要件に応じて、適切な方法を選択してください。