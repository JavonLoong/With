import fitz

pdf_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.pdf"
doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")
for i, page in enumerate(doc):
    text = page.get_text()
    sections = []
    for line in text.split('\n'):
        if "选择判断秒杀库" in line:
            sections.append(line.strip())
    print(f"Page {i+1}: {sections}")
