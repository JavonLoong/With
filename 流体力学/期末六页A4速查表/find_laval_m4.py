fp = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex"

with open(fp, 'r', encoding='utf-8-sig') as f:
    text = f.read()

lines = text.split('\n')
for idx, line in enumerate(lines):
    line_num = idx + 1
    if 1371 <= line_num <= 1618:
        if 'Laval' in line or 'laval' in line or '正激波' in line or '膨胀波' in line:
            print(f"Line {line_num}: {line}")
