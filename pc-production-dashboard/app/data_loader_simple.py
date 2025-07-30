"""
PC製造専用ダッシュボード - シンプル版データローダー

単価取得を簡素化して確実に動作させる版
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

class PCProductionDataLoaderSimple:
    def __init__(self):
        # 実行ファイルの場所を基準にパスを設定
        self.base_dir = Path(__file__).parent.parent
        self.db_path = self.base_dir / "data" / "sqlite" / "pc_production.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
        
        # サーバーパス設定
        self.server_paths = {
            'KANSEI_JISSEKI': r'\\fssha01\common\HOST\MES\KANSEI_JISSEKI.txt',
            'KOUSU_JISSEKI': r'\\fssha01\common\HOST\MES\KOUSU_JISSEKI.txt',
            'KOUTEI_JISSEKI': r'\\fssha01\common\HOST\MES\KOUTEI_JISSEKI.txt',
            'SASIZU_JISSEKI': r'\\fssha01\common\HOST\MES\SASIZU_JISSEKI.txt',
            'ZP51N': r'\\fssha01\common\HOST\ZP51N\ZP51N.TXT'
            # 問題のあるパスは削除
            # 'PC_SEISAN_KANRI': r'\\fsshi01\電源機器製造本部共有\39　部材管理課⇒他部署共有\01     PC工程進捗管理\2020.5月～PC生産_生産管理_20250724.xlsx'
        }
    
    def safe_print(self, message):
        """安全な文字列出力"""
        try:
            # Windowsコンソールでの文字化け対策
            if hasattr(message, 'encode'):
                # 日本語文字を含む場合の処理
                try:
                    print(message.encode('cp932', errors='replace').decode('cp932'))
                except:
                    print(message.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
            else:
                print(message)
        except UnicodeEncodeError:
            ascii_message = message.encode('ascii', 'replace').decode('ascii')
            print(ascii_message)
    
    def detect_encoding(self, file_path):
        """ファイルのエンコーディングを検出"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                
                if encoding and 'cp932' in encoding.lower():
                    encoding = 'shift_jis'
                
                return encoding if result['confidence'] > 0.7 else 'utf-8'
        except Exception as e:
            self.logger.warning(f"エンコーディング検出失敗: {file_path}")
            return 'utf-8'
    
    def load_historical_zm29_data(self):
        """過去のZM29月次データを読み込み"""
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
            return pd.DataFrame()
        
        self.logger.info(f"過去データフォルダ: {historical_path}")
        
        all_data = []
        files = sorted(historical_path.glob("ZM29_*.txt"))
        
        for file_path in files:
            try:
                self.logger.info(f"過去データ読み込み中: {file_path.name}")
                
                encoding = self.detect_encoding(file_path)
                self.logger.info(f"エンコーディング検出: {file_path.name} -> {encoding} (信頼度: {chardet.detect(open(file_path, 'rb').read(10000))['confidence']:.2f})")
                
                # エンコーディングエラー対策
                df = None
                encodings_to_try = [encoding, 'shift_jis', 'cp932', 'utf-8', 'latin-1', 'iso-2022-jp']
                
                for try_encoding in encodings_to_try:
                    try:
                        df = pd.read_csv(
                            file_path,
                            delimiter='\t',
                            encoding=try_encoding,
                            dtype=str,
                            on_bad_lines='skip',
                            errors='replace'  # 文字化けを?に置換
                        )
                        self.logger.info(f"成功したエンコーディング: {try_encoding}")
                        break
                    except (UnicodeDecodeError, UnicodeError) as e:
                        self.logger.warning(f"エンコーディング {try_encoding} 失敗: {e}")
                        continue
                
                if df is None:
                    # 最後の手段: バイナリ読み込みで強制変換
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        
                        # バイナリデータを強制的にUTF-8に変換
                        text_content = content.decode('utf-8', errors='replace')
                        
                        # 一時ファイルに書き込み
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as temp_file:
                            temp_file.write(text_content)
                            temp_path = temp_file.name
                        
                        df = pd.read_csv(
                            temp_path,
                            delimiter='\t',
                            encoding='utf-8',
                            dtype=str,
                            on_bad_lines='skip'
                        )
                        
                        # 一時ファイルを削除
                        os.unlink(temp_path)
                        self.logger.info("バイナリ強制変換で読み込み成功")
                        
                    except Exception as final_e:
                        self.logger.error(f"全てのエンコーディング試行が失敗: {final_e}")
                        continue
                
                if df is None:
                    self.logger.error(f"すべてのエンコーディングで読み込み失敗: {file_path.name}")
                    continue
                
                year_month = file_path.stem.split('_')[1]
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
        """KANSEI_JISSEKIをZM29形式に変換（シンプル版）"""
        if kansei_df.empty:
            return pd.DataFrame()
        
        self.logger.info(f"KANSEI_JISSEKI変換開始: {len(kansei_df)}行")
        
        zm29_df = pd.DataFrame()
        
        # 正しいカラムマッピング（計画終了日を転記日付として使用）
        column_mapping = {
            '転記日付': '計画終了日',  # SAP製造指図の基準日付の終了日
            'ネットワーク・指図番号': '指図番号',
            '品目コード': '品目コード',
            '品目テキスト': '品目テキスト',
            '完成数': '実績数量',
            '計画数': '指図数量',
            'MRP管理者': 'MRP管理者',
        }
        
        # マッピング実行
        for zm29_col, kansei_col in column_mapping.items():
            if kansei_col in kansei_df.columns:
                zm29_df[zm29_col] = kansei_df[kansei_col].copy()
                self.logger.info(f"カラムマッピング: {kansei_col} -> {zm29_col}")
        
        # 日付フィールドの変換
        if '転記日付' in zm29_df.columns:
            try:
                zm29_df['転記日付'] = pd.to_datetime(zm29_df['転記日付'], format='%Y%m%d', errors='coerce')
                self.logger.info("日付変換完了")
            except Exception as e:
                self.logger.warning(f"日付変換エラー: {e}")
        
        # 数値フィールドの変換
        numeric_columns = ['完成数', '計画数']
        for col in numeric_columns:
            if col in zm29_df.columns:
                zm29_df[col] = pd.to_numeric(zm29_df[col], errors='coerce').fillna(0)
                self.logger.info(f"数値変換完了: {col}")
        
        # シンプルな単価設定（品目コードパターンベース）
        zm29_df['単価'] = zm29_df['品目コード'].apply(self.get_simple_unit_price)
        self.logger.info("シンプル単価設定完了")
        
        # 金額計算
        if '完成数' in zm29_df.columns and '単価' in zm29_df.columns:
            zm29_df['金額'] = zm29_df['完成数'] * zm29_df['単価']
            self.logger.info("金額計算完了")
        
        # 当日データの情報を追加
        today = datetime.datetime.now().strftime('%Y%m%d')
        zm29_df['データ年月'] = today[:6]
        zm29_df['データソース'] = '当日データ'
        zm29_df['更新時刻'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.logger.info(f"ZM29形式変換完了: {len(zm29_df)}行")
        return zm29_df
    
    def get_simple_unit_price(self, item_code):
        """シンプルな単価取得（パターンベース）"""
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
            'CK-': 7000,    # 制御系
        }
        
        # パターンマッチング
        for pattern, price in price_patterns.items():
            if item_code.startswith(pattern):
                # 品目コードの特徴で価格を調整
                if len(item_code) > 10:
                    price = int(price * 1.2)  # 複雑な品目は20%増
                elif 'SUB' in item_code:
                    price = int(price * 0.8)  # SUB品目は20%減
                
                return price
        
        # デフォルト単価
        return 1000
    
    def load_current_zm29_data(self):
        """当日のZM29データを読み込み"""
        current_file = self.base_dir / "data" / "current" / "KANSEI_JISSEKI.txt"
        
        if not current_file.exists():
            self.logger.warning("当日データファイルが見つかりません")
            return pd.DataFrame()
        
        try:
            encoding = self.detect_encoding(current_file)
            kansei_df = pd.read_csv(
                current_file,
                delimiter='\t',
                encoding=encoding,
                dtype=str,
                on_bad_lines='skip'
            )
            
            self.logger.info(f"KANSEI_JISSEKI読み込み完了: {len(kansei_df)}行")
            zm29_df = self.convert_kansei_to_zm29_format(kansei_df)
            
            return zm29_df
            
        except Exception as e:
            self.logger.error(f"当日データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def calculate_monthly_week(self, date_str):
        """月別週区分を計算"""
        try:
            if pd.isna(date_str) or date_str == '':
                return None
                
            if len(str(date_str)) == 8:
                date = pd.to_datetime(str(date_str), format='%Y%m%d')
            else:
                date = pd.to_datetime(date_str)
            
            first_day = date.replace(day=1)
            days_to_monday = (7 - first_day.weekday()) % 7
            first_monday = first_day + pd.Timedelta(days=days_to_monday)
            
            if date < first_monday:
                return 1
            
            days_from_first_monday = (date - first_monday).days
            week_number = min(days_from_first_monday // 7 + 2, 5)
            
            return week_number
            
        except Exception as e:
            self.logger.warning(f"週区分計算エラー: {date_str}")
            return None
    
    def process_zm29_data(self, df):
        """ZM29データの前処理"""
        if df.empty:
            return df
        
        processed_df = df.copy()
        
        # 日付列の処理
        if '転記日付' in processed_df.columns:
            processed_df['転記日付'] = pd.to_datetime(processed_df['転記日付'], errors='coerce')
            processed_df['月別週区分'] = processed_df['転記日付'].apply(
                lambda x: self.calculate_monthly_week(x) if pd.notna(x) else None
            )
        
        # 数値列の処理
        numeric_columns = ['完成数', '計画数', '単価', '金額']
        for col in numeric_columns:
            if col in processed_df.columns:
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce').fillna(0)
        
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
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
            self.logger.info(f"データベース保存完了: {table_name} ({len(df)}行)")
            self.safe_print(f"データベース保存: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"データベース保存エラー: {table_name} - {e}")
    
    def integrate_all_data(self):
        """全データの統合処理（シンプル版）"""
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
            
            # 4. データの統合（重複除去対応）
            self.logger.info("Step 4: データ統合（重複除去処理）")
            all_zm29_data = []
            
            if not historical_data.empty:
                processed_historical = self.process_zm29_data(historical_data)
                processed_historical['データソース'] = '過去データ(ZM29)'
                if not processed_historical.empty:
                    all_zm29_data.append(processed_historical)
                    self.logger.info(f"過去データ処理完了: {len(processed_historical)}行")
            
            if not current_data.empty:
                processed_current = self.process_zm29_data(current_data)
                processed_current['データソース'] = '当日データ(KANSEI_JISSEKI)'
                if not processed_current.empty:
                    all_zm29_data.append(processed_current)
                    self.logger.info(f"当日データ処理完了: {len(processed_current)}行")
            
            if all_zm29_data:
                # データ統合
                integrated_data = pd.concat(all_zm29_data, ignore_index=True)
                
                # 重複除去（KANSEI_JISSEKIを優先）
                if 'データソース' in integrated_data.columns:
                    # KANSEI_JISSEKIを優先するためにソート（当日データが先頭に来る）
                    integrated_data = integrated_data.sort_values(
                        ['データソース', '転記日付'], 
                        ascending=[False, True]  # 当日データを優先、日付は昇順
                    )
                    
                    # 段階的重複除去
                    before_count = len(integrated_data)
                    
                    # 1. 完全一致の重複除去（転記日付+品目コード+指図番号）
                    dedup_keys_full = []
                    for key in ['転記日付', '品目コード', 'ネットワーク・指図番号']:
                        if key in integrated_data.columns:
                            dedup_keys_full.append(key)
                    
                    if dedup_keys_full:
                        integrated_data = integrated_data.drop_duplicates(subset=dedup_keys_full, keep='first')
                        after_full = len(integrated_data)
                        self.logger.info(f"完全一致重複除去: {before_count}行 -> {after_full}行")
                    
                    # 2. 指図番号のみでの重複除去（より積極的）
                    if 'ネットワーク・指図番号' in integrated_data.columns:
                        # 同じ指図番号で複数のデータソースがある場合、KANSEI_JISSEKIを優先
                        order_duplicates = integrated_data.groupby('ネットワーク・指図番号').size()
                        multi_source_orders = order_duplicates[order_duplicates > 1].index
                        
                        if len(multi_source_orders) > 0:
                            self.logger.info(f"複数データソースを持つ指図番号: {len(multi_source_orders)}件")
                            
                            # 各指図番号について、KANSEI_JISSEKIがあればそれを優先
                            final_data = []
                            processed_orders = set()
                            
                            for _, row in integrated_data.iterrows():
                                order_no = row['ネットワーク・指図番号']
                                
                                if order_no in processed_orders:
                                    continue
                                
                                if order_no in multi_source_orders:
                                    # この指図番号のすべてのレコードを取得
                                    order_records = integrated_data[
                                        integrated_data['ネットワーク・指図番号'] == order_no
                                    ].copy()
                                    
                                    # KANSEI_JISSEKIがあるかチェック
                                    kansei_records = order_records[
                                        order_records['データソース'].str.contains('KANSEI_JISSEKI', na=False)
                                    ]
                                    
                                    if not kansei_records.empty:
                                        # KANSEI_JISSEKIを優先（最新の転記日付）
                                        selected = kansei_records.sort_values('転記日付', ascending=False).iloc[0]
                                        final_data.append(selected)
                                        self.logger.debug(f"指図番号 {order_no}: KANSEI_JISSEKIを選択")
                                    else:
                                        # KANSEI_JISSEKIがない場合は最新のZM29データ
                                        selected = order_records.sort_values('転記日付', ascending=False).iloc[0]
                                        final_data.append(selected)
                                        self.logger.debug(f"指図番号 {order_no}: ZM29データを選択")
                                    
                                    processed_orders.add(order_no)
                                else:
                                    # 重複のない指図番号はそのまま追加
                                    final_data.append(row)
                                    processed_orders.add(order_no)
                            
                            integrated_data = pd.DataFrame(final_data)
                            after_order = len(integrated_data)
                            
                            self.logger.info(f"指図番号重複除去: {after_full}行 -> {after_order}行")
                    
                    # 最終結果
                    final_count = len(integrated_data)
                    removed_count = before_count - final_count
                    
                    self.logger.info(f"重複除去完了: {before_count}行 -> {final_count}行 (除去: {removed_count}行)")
                    
                    # データソース別の残存データ数
                    source_counts = integrated_data['データソース'].value_counts()
                    for source, count in source_counts.items():
                        self.logger.info(f"  {source}: {count}行")
                    
                    self.safe_print(f"重複除去: KANSEI_JISSEKIを優先して{removed_count}行の重複を除去")
                
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
    loader = PCProductionDataLoaderSimple()
    result = loader.integrate_all_data()
    
    if not result.empty:
        loader.safe_print(f"データ統合成功: {len(result)}行")
        loader.safe_print(f"データベース: {loader.db_path}")
        
        if '完成数' in result.columns:
            total_qty = result['完成数'].sum()
            loader.safe_print(f"総完成数: {total_qty}")
        
        if '金額' in result.columns:
            total_amount = result['金額'].sum()
            loader.safe_print(f"総金額: ¥{total_amount:,.0f}")
        
        if '単価' in result.columns:
            avg_price = result['単価'].mean()
            loader.safe_print(f"平均単価: ¥{avg_price:.0f}")
    else:
        loader.safe_print("データ統合に失敗しました")

if __name__ == "__main__":
    main()