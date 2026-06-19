with open(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()

# print all lines starting with commands or having \chap, \mt, \qt, \subq, \realq, \varq etc in lines 170-890
for idx in range(170, 890):
    line = lines[idx]
    stripped = line.strip()
    if stripped.startswith(("\\chap", "\\infoh", "\\subq", "\\realq", "\\varq", "\\stepq", "\\lookq", "\\errq", "\\idq", "\\conceptq", "\\fmlb")):
        print(f"L{idx+1}: {line}")
