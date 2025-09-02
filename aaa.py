from pdf2image import convert_from_path

# Popplerのインストール先を指定（例）
poppler_path = r"C:\poppler-25.07.0\Library\bin"

# PDFを画像に変換
images = convert_from_path("FIN0297711c_hupxp02pj5.pdf", poppler_path=poppler_path)

# PNGとして保存
for i, image in enumerate(images):
    image.save(f"page_{i}.png", "PNG")
