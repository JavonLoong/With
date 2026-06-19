with open(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
for idx, line in enumerate(lines):
    if "法兰" in line or "弯管" in line or "喷嘴" in line:
        print(f"L{idx+1}: {line}")
