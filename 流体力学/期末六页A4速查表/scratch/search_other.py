import os
filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '第4行用于弯管' in line or 'HGL/EGL' in line or '压力线/能量线' in line or '粗糙度反推' in line:
            print(f"Line {i+1}: {line.strip()}")
