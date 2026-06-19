with open(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex", 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if '\\chap{母题' in line:
        print(f"Line {idx+1}: {line.strip()}")
