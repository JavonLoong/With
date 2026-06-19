import re

fp = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex"

with open(fp, 'r', encoding='utf-8-sig') as f:
    text = f.read()

# Let's search for all command definitions or section titles containing "母题" or similar.
lines = text.split('\n')
for idx, line in enumerate(lines):
    if '母题' in line:
        print(f"Line {idx+1}: {line}")
