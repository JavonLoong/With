import os
filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.log'
with open(filepath, encoding='utf-8', errors='ignore') as f:
    log_content = f.read()

import re
# Find lines with "Overfull \hbox" or "line 369"
for line in log_content.split('\n'):
    if '369' in line or 'Overfull \\hbox' in line:
        print(line)
