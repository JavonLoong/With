import os
import fitz

extracted_dir = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip\几页纸（带考场）"
artifact_dir = r"C:\Users\15410\.gemini\antigravity\brain\d7a3129b-a055-473f-8391-d61281f1f488"
os.makedirs(artifact_dir, exist_ok=True)

pdf_files = [
    ("期中一页纸_wbz.pdf", "mid_wbz_p1.png"),
    ("期末一页纸_wbz.pdf", "final_wbz_p1.png"),
    ("流力期中一张纸_cl.pdf", "mid_cl_p1.png"),
    ("流力期中参考纸.pdf", "mid_ref_p1.png"),
    ("流力期末两张纸_cl.pdf", "final_cl_p1.png"),
    ("流力期末参考纸.pdf", "final_ref_p1.png")
]

for pdf_name, out_name in pdf_files:
    pdf_path = os.path.join(extracted_dir, pdf_name)
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        continue
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=100) # Lower DPI to save space
        out_path = os.path.join(artifact_dir, out_name)
        pix.save(out_path)
        print(f"Rendered {pdf_name} page 1 to {out_name}")
    except Exception as e:
        print(f"Error rendering {pdf_name}: {e}")
