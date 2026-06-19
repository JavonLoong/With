import sys
import time
import fitz
from rapidocr_onnxruntime import RapidOCR

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r"d:\虚拟C盘\学习\流体力学\流力瞎整\流体力学 张兆顺 第三版.pdf"
doc = fitz.open(pdf_path)

print("Initializing RapidOCR...")
t0 = time.perf_counter()
ocr = RapidOCR(
    **{
        "Det.intra_op_num_threads": 1,
        "Det.inter_op_num_threads": 1,
        "Cls.intra_op_num_threads": 1,
        "Cls.inter_op_num_threads": 1,
        "Rec.intra_op_num_threads": 1,
        "Rec.inter_op_num_threads": 1,
    }
)
t1 = time.perf_counter()
print(f"Initialization took {t1 - t0:.2f}s")

# Test pages 50, 51, 52 sequentially
for page_num in [50, 51, 52]:
    print(f"\nProcessing page {page_num}...")
    p_start = time.perf_counter()
    
    page = doc.load_page(page_num - 1)
    
    r_start = time.perf_counter()
    pix = page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
    image_bytes = pix.tobytes("png")
    r_time = time.perf_counter() - r_start
    
    ocr_start = time.perf_counter()
    result, timings = ocr(image_bytes)
    ocr_time = time.perf_counter() - ocr_start
    
    p_total = time.perf_counter() - p_start
    print(f"Page {page_num} completed in {p_total:.2f}s (Render: {r_time:.2f}s, OCR: {ocr_time:.2f}s)")
    if timings:
        print(f"Timings: {timings}")
