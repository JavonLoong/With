import re

fp = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex"

with open(fp, 'r', encoding='utf-8') as f:
    text = f.read()

macros = ["schemeshock", "schemeviscous", "schemebl", "varq", "formq", "symq"]

for m in macros:
    print(f"=== MACRO: {m} ===")
    match_idx = text.find("\\newcommand{\\" + m + "}")
    if match_idx == -1:
         match_idx = text.find("\\def\\" + m)
    if match_idx != -1:
        print(text[match_idx:match_idx+1000])
    else:
        print("Not found")
    print("-" * 50)
