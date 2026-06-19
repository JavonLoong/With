import os

path = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

import re
matches = re.findall(r'\\end\{tabular\}.*', content)
for m in matches:
    print(repr(m))
