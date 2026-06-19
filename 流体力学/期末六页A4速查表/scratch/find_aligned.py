import os
filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'

with open(filepath, encoding='utf-8') as f:
    content = f.read()

import re
matches = re.finditer(r'\\begin\{aligned\}(.*?)\\end\{aligned\}', content, re.DOTALL)
for m in matches:
    print(f"Match found at position {m.start()}:")
    print(m.group(0))
    print("-" * 50)
