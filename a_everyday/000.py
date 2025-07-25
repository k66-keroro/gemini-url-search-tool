def test_file_write():
    """ファイル書き込みテスト"""
    test_file = SCRIPT_DIR / "a_everyday" / "test_write.csv"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 簡単なDataFrameでテスト
        import pandas as pd
        df_test = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        df_test.to_csv(test_file, index=False, encoding='utf-8-sig')
        
        if test_file.exists():
            print(f"テスト成功: {test_file}")
            test_file.unlink()  # 削除
            return True
        else:
            print("テスト失敗: ファイルが作成されない")
            return False
    except Exception as e:
        print(f"テスト失敗: {e}")
        return False