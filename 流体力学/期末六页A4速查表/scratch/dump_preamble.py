import os
filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, encoding='utf-8') as f:
    for i in range(50):
        print(f"{i+1}: {f.readline().strip()}")
