with open(r'C:\Users\sem3171\OneDrive - 株式会社三社電機製作所\デスクトップ\PC外注転送\テキスト\ZS65.TXT', 'r', encoding='cp932') as file:
    for _ in range(5):  # 最初の5行を表示
        print(file.readline())
