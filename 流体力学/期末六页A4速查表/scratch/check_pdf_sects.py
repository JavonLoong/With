import fitz
import sys
sys.stdout.reconfigure(encoding="utf-8")
doc = fitz.open(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.pdf")
print("Total pages:", len(doc))
for i, page in enumerate(doc):
    text = page.get_text()
    if "选择判断秒杀库-11" in text or "专练" in text:
        print(f"Page {i+1} contains Section 11 text!")
