import re

file_path = r"D:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_v108_母题层级强化版.tex"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

lines = content.split('\n')
print("--- Lines 953 to 1035 ---")
for i in range(952, min(1035, len(lines))):
    print(f"Line {i+1}: {lines[i]}")
