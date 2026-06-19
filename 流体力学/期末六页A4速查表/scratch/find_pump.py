import os
filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '吸水' in line or 'z_B' in line or 'psafe' in line:
            print(f"Line {i+1}: {line.strip()}")
