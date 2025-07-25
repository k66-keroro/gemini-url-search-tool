def convert_to_utf8(file_path):
    try:
        # ファイルの内容を読み込む
        with open(file_path, 'r', encoding='shift_jis', errors='ignore') as file:
            content = file.read()
        
        # UTF-8エンコードで新しいファイルに内容を書き込む
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f"The file {file_path} has been converted to UTF-8 encoding.")
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError: {e}")

# 変換したい.batファイルのパスを指定
file_path = r'C:\Embeddable-Python\run.bat'

# .batファイルをUTF-8エンコードに変換
convert_to_utf8(file_path)