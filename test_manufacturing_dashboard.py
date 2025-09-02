"""
製造ダッシュボードのテストスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """インポートテスト"""
    try:
        print("=== 製造ダッシュボード インポートテスト ===")
        
        # 基本インポート
        from src.manufacturing_dashboard.main import ManufacturingDashboardApp
        print("✅ ManufacturingDashboardApp import successful")
        
        from src.manufacturing_dashboard.data_processor import DataProcessor
        print("✅ DataProcessor import successful")
        
        from src.manufacturing_dashboard.config.settings import get_config
        print("✅ Settings import successful")
        
        from src.manufacturing_dashboard.core.error_handler import error_handler
        print("✅ Error handler import successful")
        
        from src.manufacturing_dashboard.utils.helpers import format_datetime
        print("✅ Helpers import successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """基本機能テスト"""
    try:
        print("\n=== 基本機能テスト ===")
        
        # 設定テスト
        from src.manufacturing_dashboard.config.settings import get_config
        config = get_config()
        print(f"✅ 設定読み込み成功: {len(config)}セクション")
        
        # エラーハンドラーテスト
        from src.manufacturing_dashboard.core.error_handler import error_handler
        error_handler.log_info("テストメッセージ", "test")
        print("✅ エラーハンドラー動作確認")
        
        # ヘルパー関数テスト
        from src.manufacturing_dashboard.utils.helpers import format_datetime
        from datetime import datetime
        formatted = format_datetime(datetime.now())
        print(f"✅ ヘルパー関数動作確認: {formatted}")
        
        # データプロセッサーテスト（初期化のみ）
        from src.manufacturing_dashboard.data_processor import DataProcessor
        processor = DataProcessor()
        print("✅ DataProcessor初期化成功")
        
        print("\n🎉 基本機能テスト完了!")
        return True
        
    except Exception as e:
        print(f"❌ 基本機能テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_initialization():
    """アプリケーション初期化テスト"""
    try:
        print("\n=== アプリケーション初期化テスト ===")
        
        from src.manufacturing_dashboard.main import ManufacturingDashboardApp
        
        # アプリケーション初期化
        app = ManufacturingDashboardApp()
        print("✅ アプリケーション初期化成功")
        
        # ヘルスチェック
        health_ok = app.run_health_check()
        print(f"✅ ヘルスチェック: {'正常' if health_ok else '警告'}")
        
        # システム状態取得
        status = app.get_system_status()
        print(f"✅ システム状態取得: {status.get('status', 'unknown')}")
        
        print("\n🎉 アプリケーション初期化テスト完了!")
        return True
        
    except Exception as e:
        print(f"❌ アプリケーション初期化テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト関数"""
    print("製造ダッシュボード プロジェクト基盤テスト開始\n")
    
    results = []
    
    # インポートテスト
    results.append(test_imports())
    
    # 基本機能テスト
    results.append(test_basic_functionality())
    
    # アプリケーション初期化テスト
    results.append(test_app_initialization())
    
    # 結果サマリー
    print("\n" + "="*50)
    print("テスト結果サマリー")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"成功: {passed}/{total}")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました!")
        print("プロジェクト基盤構築が完了しました。")
        return True
    else:
        print("⚠️  一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)