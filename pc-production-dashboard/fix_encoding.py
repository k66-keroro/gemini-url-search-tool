"""
PC製造専用ダッシュボード - エンコーディング修正

Embeddable-Python環境での文字化け対策
"""

import sys
import os
import locale

def fix_console_encoding():
    """コンソールエンコーディングの修正"""
    try:
        # Windows環境でのエンコーディング設定
        if sys.platform == 'win32':
            # コンソールのコードページをUTF-8に設定
            os.system('chcp 65001 > nul')
            
            # 標準出力のエンコーディングを設定
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
        
        # ロケール設定
        try:
            locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'Japanese_Japan.932')
            except:
                pass
        
        print("✅ エンコーディング設定完了")
        return True
        
    except Exception as e:
        print(f"⚠️ エンコーディング設定エラー: {e}")
        return False

def safe_print(text):
    """安全な文字列出力"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 文字化けする場合はASCII文字のみで出力
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)

def main():
    """エンコーディング修正テスト"""
    print("=" * 50)
    safe_print("🏭 PC製造専用ダッシュボード - エンコーディング修正")
    print("=" * 50)
    
    # エンコーディング修正
    fix_console_encoding()
    
    # テスト出力
    test_messages = [
        "✅ 成功メッセージ",
        "❌ エラーメッセージ", 
        "🔄 処理中メッセージ",
        "📊 データ統合完了",
        "🎉 すべて完了しました！"
    ]
    
    print("\n📝 テスト出力:")
    for msg in test_messages:
        safe_print(f"  {msg}")
    
    # システム情報
    print(f"\nシステム情報:")
    print(f"  Python: {sys.version}")
    print(f"  Platform: {sys.platform}")
    print(f"  Encoding: {sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else 'unknown'}")
    print(f"  Locale: {locale.getlocale()}")

if __name__ == "__main__":
    main()