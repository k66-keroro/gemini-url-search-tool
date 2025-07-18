import logging
import pandas as pd
import sqlite3
from pathlib import Path
import json
import os

class DataProcessor:
    """基本データ処理クラス
    
    すべての特殊処理プロセッサの基底クラス。
    共通の処理フローとユーティリティメソッドを提供します。
    """
    
    def __init__(self, config=None):
        """初期化
        
        Args:
            config (dict, optional): 設定パラメータ。Defaults to None.
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # デフォルト設定
        self.db_path = self.config.get('db_path', 'data/sqlite/main.db')
        self.raw_data_dir = self.config.get('raw_data_dir', 'data/raw')
        
        # データベースディレクトリの確認と作成
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
    def process(self):
        """メイン処理フロー
        
        データの読み込み、変換、保存を行います。
        
        Returns:
            bool: 処理成功の場合True、失敗の場合False
        """
        start_time = pd.Timestamp.now()
        self.logger.info(f"処理開始: {self.__class__.__name__}")
        
        try:
            # データ読み込み
            self.logger.info("データ読み込み開始")
            data = self.read_data()
            self.logger.info(f"データ読み込み完了: {len(data)}行")
            
            # データ変換
            self.logger.info("データ変換開始")
            processed_data = self.transform_data(data)
            self.logger.info(f"データ変換完了: {len(processed_data)}行")
            
            # データベース保存
            self.logger.info("データベース保存開始")
            self.save_to_db(processed_data)
            self.logger.info("データベース保存完了")
            
            end_time = pd.Timestamp.now()
            processing_time = (end_time - start_time).total_seconds()
            self.logger.info(f"処理完了: {processing_time:.2f}秒")
            print(f"処理完了: {processing_time:.2f}秒")
            return True
            
        except Exception as e:
            self.logger.error(f"処理エラー: {e}", exc_info=True)
            print(f"処理エラー: {e}")
            return False
            
    def read_data(self):
        """データ読み込み
        
        サブクラスでオーバーライドする必要があります。
        
        Raises:
            NotImplementedError: サブクラスで実装されていない場合
            
        Returns:
            pd.DataFrame: 読み込んだデータ
        """
        raise NotImplementedError("サブクラスで実装する必要があります")
        
    def transform_data(self, data):
        """データ変換
        
        サブクラスでオーバーライドする必要があります。
        
        Args:
            data (pd.DataFrame): 変換するデータ
            
        Raises:
            NotImplementedError: サブクラスで実装されていない場合
            
        Returns:
            pd.DataFrame: 変換後のデータ
        """
        raise NotImplementedError("サブクラスで実装する必要があります")
        
    def save_to_db(self, data):
        """データベース保存
        
        サブクラスでオーバーライドする必要があります。
        
        Args:
            data (pd.DataFrame): 保存するデータ
            
        Raises:
            NotImplementedError: サブクラスで実装されていない場合
        """
        raise NotImplementedError("サブクラスで実装する必要があります")
        
    def get_connection(self):
        """SQLite接続を取得
        
        Returns:
            sqlite3.Connection: データベース接続
        """
        # データベースディレクトリの確認
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        return sqlite3.connect(self.db_path)
        
    def execute_query(self, query, params=None):
        """SQLクエリを実行
        
        Args:
            query (str): 実行するSQLクエリ
            params (tuple, optional): クエリパラメータ。Defaults to None.
            
        Returns:
            list: クエリ結果
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.fetchall()
        finally:
            conn.close()
            
    def load_config(self, config_file):
        """設定ファイルを読み込む
        
        Args:
            config_file (str): 設定ファイルのパス
            
        Returns:
            dict: 設定データ
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗しました: {e}")
            return {}