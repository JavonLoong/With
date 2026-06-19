import fitz
import sys
sys.stdout.reconfigure(encoding="utf-8")
doc = fitz.open(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.pdf")
print(doc[5].get_text())
