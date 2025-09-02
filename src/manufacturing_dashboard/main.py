"""
製造ダッシュボードメインアプリケーション
"""

import sys
from pathlib import Path
from typing import Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.manufacturing_dashboard.data_processor import DataProcessor
from src.manufacturing_dashboard.config.settings import get_config, ensure_directories
from src.manufacturing_dashboard.core.error_handler import error_handler


class ManufacturingDashboardApp:
    """製造ダッシュボードアプリケーション"""
    
    def __init__(self, db_path: Optional[str] = None):
        """初期化"""
        # 必要なディレクトリを作成
        ensure_directories()
        
        # 設定を読み込み
        self.config = get_config()
        
        # データベースパスを設定
        if db_path is None:
            db_path = self.config["database"]["default_db_path"]
        
        # データプロセッサーを初期化
        self.data_processor = DataProcessor(db_path)
        
        error_handler.log_info("製造ダッシュボードアプリケーションを初期化しました", "ManufacturingDashboardApp")
    
    def initialize_database(self) -> bool:
        """データベースを初期化"""
        try:
            error_handler.log_info("データベース初期化を開始", "initialize_database")
            
            # データベース情報を取得
            db_info = self.data_processor.get_database_info()
            
            if db_info:
                error_handler.log_info(
                    f"データベース初期化完了: {db_info['table_count']}テーブル", 
                    "initialize_database"
                )
                return True
            else:
                error_handler.log_warning("データベース情報の取得に失敗", "initialize_database")
                return False
                
        except Exception as e:
            error_handler.handle_error(e, "データベース初期化エラー", "error")
            return False
    
    def process_file(self, file_path: str, file_type: str = "night_batch") -> dict:
        """ファイルを処理"""
        try:
            error_handler.log_info(f"ファイル処理開始: {file_path} ({file_type})", "process_file")
            
            if file_type == "night_batch":
                result = self.data_processor.process_night_batch_files(file_path)
            elif file_type == "hourly":
                result = self.data_processor.process_hourly_data(file_path)
            else:
                raise ValueError(f"未知のファイルタイプ: {file_type}")
            
            if result["status"] == "success":
                error_handler.log_info(
                    f"ファイル処理完了: {result.get('rows_processed', 0)}行処理", 
                    "process_file"
                )
            else:
                error_handler.log_warning(
                    f"ファイル処理失敗: {result.get('error_message', 'Unknown error')}", 
                    "process_file"
                )
            
            return result
            
        except Exception as e:
            error_handler.handle_error(e, f"ファイル処理エラー: {file_path}", "error")
            return {
                "status": "error",
                "file_path": file_path,
                "error_message": str(e)
            }
    
    def generate_report(self, report_type: str, format: str = "excel") -> Optional[str]:
        """レポートを生成"""
        try:
            error_handler.log_info(f"レポート生成開始: {report_type} ({format})", "generate_report")
            
            output_path = self.data_processor.export_report(report_type, format)
            
            error_handler.log_info(f"レポート生成完了: {output_path}", "generate_report")
            return output_path
            
        except Exception as e:
            error_handler.handle_error(e, f"レポート生成エラー: {report_type}", "error")
            return None
    
    def get_system_status(self) -> dict:
        """システム状態を取得"""
        try:
            # データベース情報を取得
            db_info = self.data_processor.get_database_info()
            
            # データ整合性をチェック
            integrity_issues = self.data_processor.validate_data_integrity()
            
            # エラーサマリーを取得
            error_summary = error_handler.get_error_summary()
            
            return {
                "database": db_info,
                "integrity_issues": len(integrity_issues),
                "error_summary": error_summary,
                "status": "healthy" if len(integrity_issues) == 0 and error_summary["total_errors"] == 0 else "warning"
            }
            
        except Exception as e:
            error_handler.handle_error(e, "システム状態取得エラー", "error")
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def run_health_check(self) -> bool:
        """ヘルスチェックを実行"""
        try:
            error_handler.log_info("ヘルスチェック開始", "health_check")
            
            # データベース接続チェック
            db_info = self.data_processor.get_database_info()
            if not db_info:
                error_handler.log_warning("データベース接続に問題があります", "health_check")
                return False
            
            # 設定チェック
            config = get_config()
            if not config:
                error_handler.log_warning("設定の読み込みに問題があります", "health_check")
                return False
            
            error_handler.log_info("ヘルスチェック完了: 正常", "health_check")
            return True
            
        except Exception as e:
            error_handler.handle_error(e, "ヘルスチェックエラー", "error")
            return False


def main():
    """メイン関数"""
    try:
        # アプリケーションを初期化
        app = ManufacturingDashboardApp()
        
        # ヘルスチェックを実行
        if app.run_health_check():
            print("製造ダッシュボードアプリケーションが正常に起動しました")
            
            # システム状態を表示
            status = app.get_system_status()
            print(f"システム状態: {status['status']}")
            
            if status.get('database'):
                print(f"データベース: {status['database']['table_count']}テーブル")
            
            return True
        else:
            print("製造ダッシュボードアプリケーションの起動に失敗しました")
            return False
            
    except Exception as e:
        print(f"アプリケーション起動エラー: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)