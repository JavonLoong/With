import os
import re

tex_file_path = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'

with open(tex_file_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Let's search for Mother 3 and Mother 4 chapters and print their lines.
# Mother 3 chapter start:
ch3_line = -1
ch4_line = -1
ch5_line = -1

for idx, line in enumerate(lines):
    if r'\chap{母题3' in line or r'\chap{母题三' in line:
        ch3_line = idx + 1
    elif r'\chap{母题4' in line or r'\chap{母题四' in line:
        ch4_line = idx + 1
    elif r'\chap{母题5' in line or r'\chap{母题五' in line:
        ch5_line = idx + 1

print(f"Mother 3 starts at line: {ch3_line}")
print(f"Mother 4 starts at line: {ch4_line}")
print(f"Mother 5 starts at line: {ch5_line}")

# Let's save lines 1000 to 1700 into a file so we can view them exactly and cleanly.
with open('mother_3_4_extract.txt', 'w', encoding='utf-8') as f_out:
    for idx in range(min(ch3_line - 50, 950), min(ch5_line + 50, len(lines))):
        f_out.write(f"{idx+1}: {lines[idx]}")

print("Saved extract to mother_3_4_extract.txt")
