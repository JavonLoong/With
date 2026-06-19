with open(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex", 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'\\draw[^;]+;', text)
for m in matches:
    if 'triangle' in m or 'polygon' in m or '--' in m:
        # check if it forms a triangle
        pass

print("Number of draw commands:", len(matches))
