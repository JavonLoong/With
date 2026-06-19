import os
import fitz

pdf_path = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.pdf'
artifact_dir = r'C:\Users\15410\.gemini\antigravity\brain\a15aa55d-8660-4074-9a2b-db9cbc30ce1a'
os.makedirs(artifact_dir, exist_ok=True)

def render_page(pdf_path, page_num, output_name):
    if not os.path.exists(pdf_path):
        print(f"{pdf_path} does not exist!")
        return
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    pix = page.get_pixmap(dpi=150)
    out_path = os.path.join(artifact_dir, output_name)
    pix.save(out_path)
    print(f"Saved {pdf_path} page {page_num+1} to {out_path}")

render_page(pdf_path, 5, 'page_6.png')
