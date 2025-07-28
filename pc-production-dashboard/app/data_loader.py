"""
PC製造専用ダッシュボード - データローダー

過去データ（月次ZM29）と当日データ（MES）の統合処理
"""

import pandas as pd
import sqlite3
from pathlib import Path
import datetime
import logging
import chardet
import shutil
import os

class PCProductionDataLoader:
    def __init__(self, db_path=None):
        # 実行ファイルの場所を基準にパスを設定
        if db_path is None:
            base_dir = Path(__file__).parent.parent
            self.db_path = base_dir / "data" / "sqlite" / "pc_production.db"
        else:
            self.db_path = Path(db_path)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # サーバーパス設定（テキスト一覧.csvから取得）
        self.server_paths = {
            'KANSEI_JISSEKI': r'\\fssha01\common\HOST\MES\KANSEI_JISSEKI.txt',
            'KOUSU_JISSEKI': r'\\fssha01\common\HOST\MES\KOUSU_JISSEKI.txt',
            'KOUTEI_JISSEKI': r'\\fssha01\common\HOST\MES\KOUTEI_JISSEKI.txt',
            'SASIZU_JISSEKI': r'\\fssha01\common\HOST\MES\SASIZU_JISSEKI.txt',
            'ZP51N': r'\\fssha01\common\HOST\ZP51N\ZP51N.TXT',
            'PC_SEISAN_KANRI': r'\\fsshi01\電源機器製造本部共有\39　部材管理課⇒他部署共有\01     PC工程進捗管理\2020.5月～PC生産_生産管理_20250724.xlsx'
        }
    
    def detect_encoding(self, file_path):
        """ファイルのエンコーディングを検出"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 最初の10KBを読み取り
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
        # 実行ファイルの場所を基準にパスを設定
        base_dir = Path(__file__).parent.parent
        historical_path = base_dir / "data" / "zm29_Monthly_performance"
        
        # claude-testからのパスも試す
        if not historical_path.exists():
            claude_test_path = Path("../data/zm29_Monthly_performance")
            if claude_test_path.exists():
                historical_path = claude_test_path
        
        if not historical_path.exists():
            self.logger.error(f"過去データフォルダが見つかりません: {historical_path}")
            return pd.DataFrame()
        
        all_data = []
        
        # 月次ファイルを順番に読み込み
        for file_path in sorted(historical_path.glob("ZM29_*.txt")):
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
        base_dir = Path(__file__).parent.parent
        current_data_path = base_dir / "data" / "current"
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
    
    def load_current_zm29_data(self):
        """当日のZM29データを読み込み（KANSEI_JISSEKIから生成）"""
        base_dir = Path(__file__).parent.parent
        current_file = base_dir / "data" / "current" / "KANSEI_JISSEKI.txt"
        
        if not current_file.exists():
            self.logger.warning("当日データファイルが見つかりません")
            return pd.DataFrame()
        
        try:
            # エンコーディング検出
            encoding = self.detect_encoding(current_file)
            
            # データ読み込み
            df = pd.read_csv(
                current_file,
                delimiter='\t',
                encoding=encoding,
                dtype=str,
                on_bad_lines='skip'
            )
            
            # KANSEI_JISSEKIのカラムをZM29形式にマッピング
            column_mapping = {
                '転記日付': '転記日付',
                'ネットワーク・指図番号': 'ネットワーク・指図番号',
                '品目コード': '品目コード',
                '品目テキスト': '品目テキスト',
                '完成数': '完成数',
                '単価': '単価',
                'MRP管理者': 'MRP管理者'
            }
            
            # 必要なカラムのみ抽出してリネーム
            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            if not available_columns:
                self.logger.warning("KANSEI_JISSEKIに必要なカラムが見つかりません")
                self.logger.info(f"利用可能なカラム: {list(df.columns)}")
                # 最低限のカラムを作成
                df = df.copy()
                if '転記日付' not in df.columns and len(df.columns) > 0:
                    df['転記日付'] = datetime.datetime.now().strftime('%Y%m%d')
                if 'ネットワーク・指図番号' not in df.columns and len(df.columns) > 0:
                    df['ネットワーク・指図番号'] = df.iloc[:, 0] if len(df.columns) > 0 else 'UNKNOWN'
                if '品目コード' not in df.columns and len(df.columns) > 1:
                    df['品目コード'] = df.iloc[:, 1] if len(df.columns) > 1 else 'UNKNOWN'
                if '完成数' not in df.columns:
                    df['完成数'] = 1
                if '単価' not in df.columns:
                    df['単価'] = 0
                if 'MRP管理者' not in df.columns:
                    df['MRP管理者'] = 'PC1'  # デフォルト値
            else:
                df = df[available_columns].copy()
            
            # 当日データの情報を追加
            today = datetime.datetime.now().strftime('%Y%m%d')
            df['データ年月'] = today[:6]  # YYYYMM
            df['データソース'] = '当日データ'
            df['更新時刻'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"当日データ読み込み完了: {len(df)}行")
            return df
            
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
            processed_df = processed_df[processed_df['MRP管理者'].str.contains('PC', na=False)]
        
        return processed_df
    
    def save_to_database(self, df, table_name):
        """データをSQLiteデータベースに保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # テーブルを置き換えて保存
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            conn.close()
            self.logger.info(f"データベース保存完了: {table_name} ({len(df)}行)")
            
        except Exception as e:
            self.logger.error(f"データベース保存エラー: {table_name} - {e}")
    
    def integrate_all_data(self):
        """全データの統合処理"""
        self.logger.info("PC製造データ統合処理開始")
        
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
        
        try:
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
                # カラムの統一
                common_columns = None
                for data in all_zm29_data:
                    if common_columns is None:
                        common_columns = set(data.columns)
                    else:
                        common_columns = common_columns.intersection(set(data.columns))
                
                if common_columns:
                    # 共通カラムのみで統合
                    common_columns = list(common_columns)
                    unified_data = []
                    for data in all_zm29_data:
                        unified_data.append(data[common_columns])
                    
                    integrated_data = pd.concat(unified_data, ignore_index=True)
                    
                    # 重複除去（同じ日付・品目・指図番号の場合は当日データを優先）
                    if 'データソース' in integrated_data.columns:
                        integrated_data = integrated_data.sort_values('データソース', ascending=False)  # 当日データが先
                        
                        # 重複除去のキーを動的に決定
                        dedup_keys = []
                        for key in ['転記日付', '品目コード', 'ネットワーク・指図番号']:
                            if key in integrated_data.columns:
                                dedup_keys.append(key)
                        
                        if dedup_keys:
                            integrated_data = integrated_data.drop_duplicates(
                                subset=dedup_keys,
                                keep='first'
                            )
                    
                    # 5. データベースに保存
                    self.logger.info("Step 5: データベース保存")
                    self.save_to_database(integrated_data, 'pc_production_zm29')
                    
                    self.logger.info(f"PC製造データ統合完了: 総行数 {len(integrated_data)}")
                    return integrated_data
                else:
                    self.logger.error("統合可能な共通カラムがありません")
                    return pd.DataFrame()
            else:
                self.logger.warning("統合するデータがありません")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"データ統合エラー: {e}")
            # デバッグ情報を出力
            if not historical_data.empty:
                self.logger.info(f"過去データカラム: {list(historical_data.columns)}")
            if not current_data.empty:
                self.logger.info(f"当日データカラム: {list(current_data.columns)}")
            return pd.DataFrame()

def main():
    """メイン実行関数"""
    loader = PCProductionDataLoader()
    result = loader.integrate_all_data()
    
    if not result.empty:
        print(f"✅ データ統合完了: {len(result)}行")
        print(f"📊 データ期間: {result['転記日付'].min()} ～ {result['転記日付'].max()}")
        print(f"🏭 MRP管理者: {result['MRP管理者'].unique()}")
    else:
        print("❌ データ統合に失敗しました")

if __name__ == "__main__":
    main()