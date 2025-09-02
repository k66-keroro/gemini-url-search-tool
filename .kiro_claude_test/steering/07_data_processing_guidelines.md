# データ加工処理ガイドライン

## 基本方針

データ加工処理は、以下の2つのカテゴリに分類します：

1. **標準処理**: `main.py` で一括処理される標準的なデータ取り込み
2. **特殊処理**: 複雑な加工ロジックを持つ個別処理スクリプト

## 特殊処理の判断基準

以下の条件に1つでも当てはまる場合は、個別の特殊処理スクリプトとして実装します：

- 複雑なビジネスロジック（例：ZP138の引当計算）が必要
- メモリ使用量が大きい処理
- 処理時間が長い（目安：60秒以上）
- 特殊なデータ形式や変換が必要
- 特定の外部システムとの連携が必要

## ファイル構成

```
project/
├── src/
│   ├── main.py                # メインバッチ処理
│   ├── core/                  # コア機能
│   │   └── sqlite_manager.py  # SQLite管理クラス
│   └── processors/            # 特殊処理スクリプト
│       ├── zp138_processor.py # ZP138処理
│       └── other_processor.py # その他の特殊処理
├── data/
│   ├── raw/                   # 元データ
│   │   └── ZP138.txt          # ZP138元データ
│   └── sqlite/                # SQLiteデータベース
│       └── main.db            # メインデータベース
└── config/
    └── processors/            # 特殊処理の設定ファイル
        └── zp138_config.json  # ZP138処理の設定
```

## 命名規則

1. **ファイル名**: `{テーブル名}_processor.py`
   - 例: `zp138_processor.py`, `zm37_processor.py`

2. **クラス名**: `{テーブル名}Processor`
   - 例: `ZP138Processor`, `ZM37Processor`

3. **メソッド名**:
   - `process()`: メイン処理
   - `read_data()`: データ読み込み
   - `transform_data()`: データ変換
   - `save_to_db()`: データベース保存

## 実装ガイドライン

### 1. 基本構造

```python
class DataProcessor:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
    def process(self):
        """メイン処理フロー"""
        try:
            data = self.read_data()
            processed_data = self.transform_data(data)
            self.save_to_db(processed_data)
            return True
        except Exception as e:
            self.logger.error(f"処理エラー: {e}")
            return False
            
    def read_data(self):
        """データ読み込み"""
        pass
        
    def transform_data(self, data):
        """データ変換"""
        pass
        
    def save_to_db(self, data):
        """データベース保存"""
        pass
```

### 2. ZP138処理の例

```python
class ZP138Processor(DataProcessor):
    def read_data(self):
        """ZP138.txtを読み込む"""
        file_path = "data/raw/ZP138.txt"
        return pd.read_csv(file_path, delimiter='\t', encoding='cp932')
        
    def transform_data(self, data):
        """引当計算などの変換処理"""
        # 引当計算ロジック
        return processed_data
        
    def save_to_db(self, data):
        """SQLiteに保存"""
        conn = sqlite3.connect("data/sqlite/main.db")
        data.to_sql("t_zp138引当", conn, if_exists="replace", index=False)
        conn.close()
```

## ZP138処理の特殊性

ZP138処理は以下の理由から個別処理として実装します：

1. **複雑な引当計算ロジック**:
   - 在庫数に基づく引当計算
   - 品目ごとの連続行番号に基づく処理

2. **処理時間の長さ**:
   - 現状の処理時間: 約195秒
   - 一括処理に含めると全体の処理時間に影響

3. **特殊なデータ形式**:
   - SAPの後ろマイナス表記
   - 特殊な日付形式

## 既存ZP138処理の改善方針

1. **ファイル配置の変更**:
   - `src/processors/zp138_processor.py` に移動

2. **パス設定の変更**:
   - 入力ファイル: `data/raw/ZP138.txt`
   - SQLiteデータベース: `data/sqlite/main.db`

3. **Access依存の削減**:
   - 段階的にAccessエクスポート機能を削除
   - 当面は互換性のためにオプション機能として維持

4. **パフォーマンス最適化**:
   - バッチ処理によるメモリ使用量の削減
   - インデックスを活用したSQLite処理の高速化

## 実行方法

### 1. 単体実行

```bash
python src/processors/zp138_processor.py
```

### 2. メインバッチからの呼び出し（オプション）

```python
# main.py
from src.processors.zp138_processor import ZP138Processor

def main():
    # 標準処理
    # ...
    
    # 特殊処理（オプション）
    if config.get("process_zp138", False):
        processor = ZP138Processor()
        processor.process()
```

## 今後の展開

1. **処理の共通化**:
   - 共通ロジックを基底クラスに移動
   - 特殊処理間での再利用性向上

2. **設定の外部化**:
   - 処理パラメータをJSON設定ファイルに移動
   - 実行時の柔軟な設定変更をサポート

3. **並列処理の検討**:
   - 独立した処理の並列実行
   - 全体の処理時間短縮