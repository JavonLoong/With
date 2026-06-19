import os

paths = [
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex',
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex'
]

for p in paths:
    print(f"=== File: {p} ===")
    if not os.path.exists(p):
        print("File does not exist!")
        continue
    with open(p, encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if '吸水' in line or 'z_B' in line or 'psafe' in line or '0+0+z_0' in line:
            print(f"Line {i+1}: {line.strip()}")
