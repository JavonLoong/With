import re

fp = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex"
with open(fp, 'r', encoding='utf-8-sig') as f:
    text = f.read()

lines = text.split('\n')

with open('mother3_mother4_lines.txt', 'w', encoding='utf-8') as f_out:
    f_out.write("=== MOTHER 3 (Lines 1027 to 1370) ===\n")
    for i in range(1026, min(1370, len(lines))):
        f_out.write(f"Line {i+1}: {lines[i]}\n")
        
    f_out.write("\n\n=== MOTHER 4 (Lines 1371 to 1618) ===\n")
    for i in range(1370, min(1618, len(lines))):
        f_out.write(f"Line {i+1}: {lines[i]}\n")

print("Written mother3 and mother4 lines to mother3_mother4_lines.txt")
