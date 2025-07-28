"""
PC製造専用ダッシュボード - データローダー（修正版）

検証で見つかった問題を修正:
1. パス問題の修正
2. KANSEI_JISSEKI → ZM29形式の変換
3. エンコーディング問題の対応
4. エラーハンドリングの強化
"""

import pandas as pd
import sqlite3
from pathlib import Path
import datetime
import logging
import chardet
import shutil
import os
import sys

class PCProductionDataLoaderFixed:
    def __init__(self):
        # 実行ファイルの場所を基準にパスを設定
        self.base_dir = Path(__file__).parent.parent
        self.db_path = self.base_dir / "data" / "sqlite" / "pc_production.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ログ設定（エンコーディング対応）
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # サーバーパス設定
        self.server_paths = {
            'KANSEI_JISSEKI': r'\\fssha01\common\HOST\MES\KANSEI_JISSEKI.txt',
            'KOUSU_JISSEKI': r'\\fssha01\common\HOST\MES\KOUSU_JISSEKI.txt',
            'KOUTEI_JISSEKI': r'\\fssha01\common\HOST\MES\KOUTEI_JISSEKI.txt',
            'SASIZU_JISSEKI': r'\\fssha01\common\HOST\MES\SASIZU_JISSEKI.txt',
            'ZP51N': r'\\fssha01\common\HOST\ZP51N\ZP51N.TXT'
        }
    
    def safe_print(self, message):
        """安全な文字列出力"""
        try:
            print(message)
        except UnicodeEncodeError:
            # 文字化けする場合はASCII文字のみで出力
            ascii_message = message.encode('ascii', 'replace').decode('ascii')
            print(ascii_message)
    
    def detect_encoding(self, file_path):
        """ファイルのエンコーディングを検出"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                
                self.logger.info(f"エンコーディング検出: {file_path.name} -> {encoding} (信頼度: {confidence:.2f})")
                
                # CP932の場合はshift_jisとして扱う
                if encoding and 'cp932' in encoding.lower():
                    encoding = 'shift_jis'
                
                return encoding if confidence > 0.7 else 'utf-8'
        except Exception as e:
            self.logger.warning(f"エンコーディング検出失敗: {file_path} -> デフォルトutf-8使用")
            return 'utf-8'
    
    def load_historical_zm29_data(self):
        """過去のZM29月次データを読み込み"""
        # 複数のパスを試す
        possible_paths = [
            self.base_dir / "data" / "zm29_Monthly_performance",
            Path("../data/zm29_Monthly_performance"),
            Path("data/zm29_Monthly_performance")
        ]
        
        historical_path = None
        for path in possible_paths:
            if path.exists() and list(path.glob("ZM29_*.txt")):
                historical_path = path
                break
        
        if not historical_path:
            self.logger.error("過去データフォルダが見つかりません")
            self.safe_print("過去データフォルダが見つかりません。以下のパスを確認してください:")
            for path in possible_paths:
                self.safe_print(f"  - {path.absolute()}")
            return pd.DataFrame()
        
        self.logger.info(f"過去データフォルダ: {historical_path}")
        
        all_data = []
        files = sorted(historical_path.glob("ZM29_*.txt"))
        
        for file_path in files:
            try:
                self.logger.info(f"過去データ読み込み中: {file_path.name}")
                
                # エンコーディング検出
                encoding = self.detect_encoding(file_path)
                
                # データ読み込み
                df = pd.read_csv(
                    file_path,
                    delimiter='\t',
                    encoding=encoding,
                    dtype=str,
                    on_bad_lines='skip'
                )
                
                # 年月情報を追加
                year_month = file_path.stem.split('_')[1]  # ZM29_202404 -> 202404
                df['データ年月'] = year_month
                df['データソース'] = '過去データ'
                
                all_data.append(df)
                self.logger.info(f"読み込み完了: {file_path.name} ({len(df)}行)")
                
            except Exception as e:
                self.logger.error(f"過去データ読み込みエラー: {file_path.name} - {e}")
                continue
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            self.logger.info(f"過去データ統合完了: 総行数 {len(combined_df)}")
            return combined_df
        else:
            return pd.DataFrame()
    
    def copy_current_data_from_server(self):
        """サーバーから当日データをコピー"""
        current_data_path = self.base_dir / "data" / "current"
        current_data_path.mkdir(parents=True, exist_ok=True)
        
        copied_files = []
        
        for data_name, server_path in self.server_paths.items():
            try:
                server_file = Path(server_path)
                local_file = current_data_path / server_file.name
                
                if server_file.exists():
                    shutil.copy2(server_file, local_file)
                    copied_files.append(local_file)
                    self.logger.info(f"サーバーファイルコピー完了: {server_file.name}")
                else:
                    self.logger.warning(f"サーバーファイルが見つかりません: {server_path}")
                    
            except Exception as e:
                self.logger.error(f"サーバーファイルコピーエラー: {data_name} - {e}")
                continue
        
        return copied_files
    
    def convert_kansei_to_zm29_format(self, kansei_df):
        """KANSEI_JISSEKIをZM29形式に変換（正しいマッピング版）"""
        if kansei_df.empty:
            return pd.DataFrame()
        
        self.logger.info(f"KANSEI_JISSEKI変換開始: {len(kansei_df)}行")
        self.logger.info(f"KANSEI_JISSEKIカラム: {list(kansei_df.columns)}")
        
        # ZM29形式のDataFrameを作成
        zm29_df = pd.DataFrame()
        
        # 正しいカラムマッピング（分析結果に基づく）
        column_mapping = {
            '転記日付': '計画終了日',        # 20250612 -> 2025-06-12
            'ネットワーク・指図番号': '指図番号',  # 50119749
            '品目コード': '品目コード',       # P0A326100
            '品目テキスト': '品目テキスト',   # PK-3261B  PK-3260 ﾎｶ  SUB
            '完成数': '実績数量',            # 12, 9, 10...
            '計画数': '指図数量',            # 12, 10, 10...
            'MRP管理者': 'MRP管理者',        # PC1, PC2...
        }
        
        # マッピング実行
        for zm29_col, kansei_col in column_mapping.items():
            if kansei_col in kansei_df.columns:
                zm29_df[zm29_col] = kansei_df[kansei_col].copy()
                self.logger.info(f"カラムマッピング: {kansei_col} -> {zm29_col}")
            else:
                self.logger.warning(f"カラムが見つかりません: {kansei_col}")
        
        # 日付フィールドの変換（YYYYMMDD -> YYYY-MM-DD）
        if '転記日付' in zm29_df.columns:
            try:
                # 8桁数値を日付形式に変換
                zm29_df['転記日付'] = pd.to_datetime(zm29_df['転記日付'], format='%Y%m%d', errors='coerce')
                self.logger.info("日付変換完了: YYYYMMDD -> datetime")
            except Exception as e:
                self.logger.warning(f"日付変換エラー: {e}")
        
        # 数値フィールドの変換
        numeric_columns = ['完成数', '計画数']
        for col in numeric_columns:
            if col in zm29_df.columns:
                zm29_df[col] = pd.to_numeric(zm29_df[col], errors='coerce').fillna(0)
                self.logger.info(f"数値変換完了: {col}")
        
        # 単価の設定（配布版対応）
        zm29_df['単価'] = self.get_unit_prices_for_distribution(zm29_df)
        
        # 金額計算（完成数 × 単価）
        if '完成数' in zm29_df.columns and '単価' in zm29_df.columns:
            zm29_df['金額'] = zm29_df['完成数'] * zm29_df['単価']
            self.logger.info("金額計算完了: 完成数 × 単価")
        
        # 不足カラムの補完
        required_columns = {
            'プラント': 'P100',
            '保管場所': '1120',
            'WBS要素': '',
            '受注伝票番号': '0000000000',
            '受注明細番号': '000000'
        }
        
        for col, default_val in required_columns.items():
            if col not in zm29_df.columns and col in kansei_df.columns:
                zm29_df[col] = kansei_df[col]
            elif col not in zm29_df.columns:
                zm29_df[col] = default_val
        
        self.logger.info(f"ZM29形式変換完了: {len(zm29_df)}行, カラム: {list(zm29_df.columns)}")
        
        # 変換結果のサンプル表示
        if not zm29_df.empty:
            self.logger.info("変換結果サンプル:")
            sample = zm29_df.head(2)
            for i, row in sample.iterrows():
                self.logger.info(f"  行{i+1}: 品目={row.get('品目コード', 'N/A')}, 完成数={row.get('完成数', 'N/A')}, 金額={row.get('金額', 'N/A')}")
        
        return zm29_df
    
    def get_unit_prices_for_distribution(self, zm29_df):
        """配布版用の単価取得（複数のソースから取得）"""
        if zm29_df.empty or '品目コード' not in zm29_df.columns:
            return [1000] * len(zm29_df)  # デフォルト単価
        
        unit_prices = []
        
        for item_code in zm29_df['品目コード']:
            price = self.get_single_unit_price(item_code)
            unit_prices.append(price)
        
        self.logger.info(f"単価取得完了: 平均単価 {sum(unit_prices)/len(unit_prices):.0f}円")
        return unit_prices
    
    def get_single_unit_price(self, item_code):
        """単一品目の単価を取得（複数ソース対応）"""
        try:
            # 方法1: ZP51Nファイルから取得
            price = self.get_price_from_zp51n(item_code)
            if price > 0:
                return price
            
            # 方法2: サーバーのマスタファイルから取得
            price = self.get_price_from_server_master(item_code)
            if price > 0:
                return price
            
            # 方法3: 品目コードパターンに基づく推定単価
            price = self.estimate_price_by_pattern(item_code)
            return price
            
        except Exception as e:
            self.logger.warning(f"単価取得エラー {item_code}: {e}")
            return 1000  # デフォルト単価
    
    def get_price_from_zp51n(self, item_code):
        """ZP51Nファイルから単価を取得"""
        try:
            zp51n_file = self.base_dir / "data" / "current" / "ZP51N.TXT"
            
            if not zp51n_file.exists():
                return 0
            
            # ZP51Nファイルを読み込み（簡易版）
            with open(zp51n_file, 'r', encoding='shift_jis') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) > 2 and parts[0] == item_code:
                        # 単価カラムを探す（位置は要調整）
                        try:
                            price = float(parts[5])  # 仮の位置
                            if price > 0:
                                return price
                        except:
                            continue
            
            return 0
            
        except Exception as e:
            self.logger.debug(f"ZP51N単価取得エラー {item_code}: {e}")
            return 0
    
    def get_price_from_server_master(self, item_code):
        """サーバーのマスタファイルから単価を取得"""
        try:
            # MARA_DLやZP128などのマスタファイルから取得
            master_files = [
                r'\\fssha01\common\HOST\JOHODBDL\TEIKEI\MASTER\HINMOKU\MARA_DL.csv',
                r'\\fssha01\common\HOST\ZP128\ZP128_P100.txt'
            ]
            
            for master_file in master_files:
                if Path(master_file).exists():
                    try:
                        # CSVまたはTXTファイルから単価を検索
                        df = pd.read_csv(master_file, delimiter='\t' if master_file.endswith('.txt') else ',', 
                                       encoding='shift_jis', dtype=str, on_bad_lines='skip')
                        
                        # 品目コードでフィルタ
                        if '品目コード' in df.columns:
                            match = df[df['品目コード'] == item_code]
                            if not match.empty:
                                # 単価カラムを探す
                                price_columns = ['単価', '標準価格', '価格', 'PRICE', 'UNIT_PRICE']
                                for col in price_columns:
                                    if col in match.columns:
                                        try:
                                            price = float(match[col].iloc[0])
                                            if price > 0:
                                                return price
                                        except:
                                            continue
                    except Exception as e:
                        self.logger.debug(f"マスタファイル読み込みエラー {master_file}: {e}")
                        continue
            
            return 0
            
        except Exception as e:
            self.logger.debug(f"サーバーマスタ単価取得エラー {item_code}: {e}")
            return 0
    
    def estimate_price_by_pattern(self, item_code):
        """品目コードパターンに基づく推定単価"""
        try:
            if not item_code or len(item_code) < 3:
                return 1000
            
            # PC製造品目の推定単価パターン
            price_patterns = {
                'P0A': 5000,    # PCB基板系
                'P00': 3000,    # 部品系
                'PZZ': 2000,    # 小物部品
                'IK-': 8000,    # 制御基板
                'PK-': 6000,    # 電源基板
                'MK-': 4000,    # その他基板
            }
            
            # パターンマッチング
            for pattern, price in price_patterns.items():
                if item_code.startswith(pattern):
                    # 品目コードの長さや特徴で価格を調整
                    if len(item_code) > 10:
                        price = int(price * 1.2)  # 複雑な品目は20%増
                    elif 'SUB' in item_code:
                        price = int(price * 0.8)  # SUB品目は20%減
                    
                    return price
            
            # デフォルト推定単価
            base_price = 1000
            
            # 品目コードの特徴による調整
            if 'PCB' in item_code.upper():
                base_price = 4000
            elif any(x in item_code.upper() for x in ['CTRL', 'CONTROL', '制御']):
                base_price = 6000
            elif any(x in item_code.upper() for x in ['PWR', 'POWER', '電源']):
                base_price = 5000
            
            return base_price
            
        except Exception as e:
            self.logger.debug(f"単価推定エラー {item_code}: {e}")
            return 1000
    
    def load_current_zm29_data(self):
        """当日のZM29データを読み込み（KANSEI_JISSEKIから変換）"""
        current_file = self.base_dir / "data" / "current" / "KANSEI_JISSEKI.txt"
        
        if not current_file.exists():
            self.logger.warning("当日データファイルが見つかりません")
            return pd.DataFrame()
        
        try:
            # エンコーディング検出
            encoding = self.detect_encoding(current_file)
            
            # データ読み込み
            kansei_df = pd.read_csv(
                current_file,
                delimiter='\t',
                encoding=encoding,
                dtype=str,
                on_bad_lines='skip'
            )
            
            self.logger.info(f"KANSEI_JISSEKI読み込み完了: {len(kansei_df)}行")
            
            # ZM29形式に変換
            zm29_df = self.convert_kansei_to_zm29_format(kansei_df)
            
            if not zm29_df.empty:
                # 当日データの情報を追加
                today = datetime.datetime.now().strftime('%Y%m%d')
                zm29_df['データ年月'] = today[:6]  # YYYYMM
                zm29_df['データソース'] = '当日データ'
                zm29_df['更新時刻'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                self.logger.info(f"当日データ変換完了: {len(zm29_df)}行")
            
            return zm29_df
            
        except Exception as e:
            self.logger.error(f"当日データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def calculate_monthly_week(self, date_str):
        """月別週区分を計算（1-5週）"""
        try:
            if pd.isna(date_str) or date_str == '':
                return None
                
            # 日付文字列をdatetimeに変換
            if len(str(date_str)) == 8:  # YYYYMMDD
                date = pd.to_datetime(str(date_str), format='%Y%m%d')
            else:
                date = pd.to_datetime(date_str)
            
            # 月の最初の日
            first_day = date.replace(day=1)
            
            # 月の最初の月曜日を見つける
            days_to_monday = (7 - first_day.weekday()) % 7
            first_monday = first_day + pd.Timedelta(days=days_to_monday)
            
            # 対象日が最初の月曜日より前の場合は第1週
            if date < first_monday:
                return 1
            
            # 最初の月曜日からの経過日数で週を計算
            days_from_first_monday = (date - first_monday).days
            week_number = min(days_from_first_monday // 7 + 2, 5)
            
            return week_number
            
        except Exception as e:
            self.logger.warning(f"週区分計算エラー: {date_str} - {e}")
            return None
    
    def process_zm29_data(self, df):
        """ZM29データの前処理"""
        if df.empty:
            return df
        
        processed_df = df.copy()
        
        # 日付列の処理
        if '転記日付' in processed_df.columns:
            processed_df['転記日付'] = pd.to_datetime(processed_df['転記日付'], errors='coerce')
            
            # 月別週区分を計算
            processed_df['月別週区分'] = processed_df['転記日付'].apply(
                lambda x: self.calculate_monthly_week(x) if pd.notna(x) else None
            )
        
        # 数値列の処理
        numeric_columns = ['完成数', '計画数', '単価']
        for col in numeric_columns:
            if col in processed_df.columns:
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce').fillna(0)
        
        # 金額計算
        if '完成数' in processed_df.columns and '単価' in processed_df.columns:
            processed_df['金額'] = processed_df['完成数'] * processed_df['単価']
        
        # PC製造データのフィルタリング
        if 'MRP管理者' in processed_df.columns:
            pc_mask = processed_df['MRP管理者'].str.contains('PC', na=False)
            processed_df = processed_df[pc_mask]
            self.logger.info(f"PC製造データフィルタリング: {pc_mask.sum()}行")
        
        return processed_df
    
    def save_to_database(self, df, table_name):
        """データをSQLiteデータベースに保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # テーブルを置き換えて保存
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            conn.close()
            self.logger.info(f"データベース保存完了: {table_name} ({len(df)}行)")
            self.safe_print(f"データベース保存: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"データベース保存エラー: {table_name} - {e}")
    
    def integrate_all_data(self):
        """全データの統合処理"""
        self.logger.info("PC製造データ統合処理開始")
        self.safe_print("PC製造データ統合処理開始")
        
        try:
            # 1. サーバーから当日データをコピー
            self.logger.info("Step 1: サーバーデータコピー")
            self.copy_current_data_from_server()
            
            # 2. 過去データの読み込み
            self.logger.info("Step 2: 過去データ読み込み")
            historical_data = self.load_historical_zm29_data()
            
            # 3. 当日データの読み込み
            self.logger.info("Step 3: 当日データ読み込み")
            current_data = self.load_current_zm29_data()
            
            # 4. データの統合
            self.logger.info("Step 4: データ統合")
            all_zm29_data = []
            
            if not historical_data.empty:
                processed_historical = self.process_zm29_data(historical_data)
                if not processed_historical.empty:
                    all_zm29_data.append(processed_historical)
                    self.logger.info(f"過去データ処理完了: {len(processed_historical)}行")
            
            if not current_data.empty:
                processed_current = self.process_zm29_data(current_data)
                if not processed_current.empty:
                    all_zm29_data.append(processed_current)
                    self.logger.info(f"当日データ処理完了: {len(processed_current)}行")
            
            if all_zm29_data:
                # データ統合
                integrated_data = pd.concat(all_zm29_data, ignore_index=True)
                
                # 重複除去
                if 'データソース' in integrated_data.columns:
                    integrated_data = integrated_data.sort_values('データソース', ascending=False)
                    
                    # 重複除去のキーを動的に決定
                    dedup_keys = []
                    for key in ['転記日付', '品目コード', 'ネットワーク・指図番号']:
                        if key in integrated_data.columns:
                            dedup_keys.append(key)
                    
                    if dedup_keys:
                        before_count = len(integrated_data)
                        integrated_data = integrated_data.drop_duplicates(subset=dedup_keys, keep='first')
                        after_count = len(integrated_data)
                        self.logger.info(f"重複除去: {before_count}行 -> {after_count}行")
                
                # 5. データベースに保存
                self.logger.info("Step 5: データベース保存")
                self.save_to_database(integrated_data, 'pc_production_zm29')
                
                self.logger.info(f"PC製造データ統合完了: 総行数 {len(integrated_data)}")
                self.safe_print(f"PC製造データ統合完了: 総行数 {len(integrated_data)}")
                
                return integrated_data
            else:
                self.logger.warning("統合するデータがありません")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"データ統合エラー: {e}")
            self.safe_print(f"データ統合エラー: {e}")
            return pd.DataFrame()

def main():
    """メイン実行関数"""
    loader = PCProductionDataLoaderFixed()
    result = loader.integrate_all_data()
    
    if not result.empty:
        loader.safe_print(f"データ統合成功: {len(result)}行")
        loader.safe_print(f"データベース: {loader.db_path}")
        
        if '転記日付' in result.columns:
            date_range = result['転記日付'].dropna()
            if not date_range.empty:
                loader.safe_print(f"データ期間: {date_range.min()} - {date_range.max()}")
        
        if 'MRP管理者' in result.columns:
            mrp_managers = result['MRP管理者'].unique()
            loader.safe_print(f"MRP管理者: {list(mrp_managers)}")
    else:
        loader.safe_print("データ統合に失敗しました")

if __name__ == "__main__":
    main()