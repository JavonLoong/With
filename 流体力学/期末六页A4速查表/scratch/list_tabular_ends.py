import os

path = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if r'\end{tabular}' in line:
            print(f"Line {i+1}: {repr(line)}")
