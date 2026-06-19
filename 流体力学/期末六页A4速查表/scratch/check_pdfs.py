import os
import fitz

pdf_paths = [
    r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.pdf",
    r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.pdf",
    r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版2.pdf"
]

for p in pdf_paths:
    if not os.path.exists(p):
        print(f"{p}: Does not exist")
        continue
    doc = fitz.open(p)
    has_11 = any("选择判断秒杀库-11" in page.get_text() for page in doc)
    print(f"{p}: Pages={doc.page_count}, Has Section 11={has_11}")
