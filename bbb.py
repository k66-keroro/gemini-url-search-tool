import pytesseract
from PIL import Image, ImageOps

# Tesseractのパス指定
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 画像読み込みと前処理
img = Image.open("page_0.png")
img = ImageOps.grayscale(img)  # グレースケール化
img = ImageOps.invert(img)     # 白黒反転（必要なら）

# OCR実行（縦書き日本語も試す）
text = pytesseract.image_to_string(img, lang="jpn_vert")
print(text)
