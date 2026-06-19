import os
filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'begin{tabular}' in line:
        print(f"=== Table at line {i+1} ===")
        # Print up to 10 lines
        for j in range(max(0, i-1), min(len(lines), i+15)):
            print(f"{j+1}: {lines[j].strip()}")
