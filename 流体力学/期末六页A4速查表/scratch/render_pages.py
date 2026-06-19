import os
import fitz

pdf_root = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.pdf'
pdf_sub = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.pdf'

artifact_dir = r'C:\Users\15410\.gemini\antigravity\brain\d7a3129b-a055-473f-8391-d61281f1f488'
os.makedirs(artifact_dir, exist_ok=True)

def render_page1(pdf_path, output_name):
    if not os.path.exists(pdf_path):
        print(f"{pdf_path} does not exist!")
        return
    doc = fitz.open(pdf_path)
    page = doc.load_page(0) # page 1
    pix = page.get_pixmap(dpi=150)
    out_path = os.path.join(artifact_dir, output_name)
    pix.save(out_path)
    print(f"Saved {pdf_path} page 1 to {out_path}")

render_page1(pdf_root, 'page_1_root.png')
render_page1(pdf_sub, 'page_1_sub.png')
