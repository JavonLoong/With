import sys
import fitz
from rapidocr_onnxruntime import RapidOCR

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r"d:\虚拟C盘\学习\流体力学\流力瞎整\流体力学 张兆顺 第三版.pdf"
doc = fitz.open(pdf_path)
page = doc.load_page(50)  # Load page 50 (51st page)

print("Page loaded. Rendering...")
# Render at scale 1.35 as configured in RAG script
pix = page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
image_bytes = pix.tobytes("png")

print("Initializing RapidOCR...")
ocr = RapidOCR()

print("Running OCR...")
result, timings = ocr(image_bytes)

print("\n--- OCR Results ---")
if result:
    for line in result:
        text = line[1]
        confidence = line[2]
        print(f"[{confidence:.3f}] {text}")
else:
    print("No text detected.")
