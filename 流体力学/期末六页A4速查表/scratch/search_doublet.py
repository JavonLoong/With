import os

filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        for word in ['三维', '3d', '偶极', 'doublet']:
            if word in line.lower():
                print(f"Line {i+1} ({word}): {line.strip()}")
                break
