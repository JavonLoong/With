with open(r'd:\虚拟C盘\学习\流体力学\全目录题目归类_重整版一\母题子题精选结构_完整原题版一.md', 'r', encoding='utf-8') as f:
    text1 = f.read()

with open(r'd:\虚拟C盘\学习\流体力学\全目录题目归类_重整版一\母题子题精选结构_重整版一.md', 'r', encoding='utf-8') as f:
    text2 = f.read()

import re

out = []
out.append("=== FILE 1: 母题子题精选结构_完整原题版一.md ===")
for title in ["水轮机", "安装高度", "法兰螺栓", "螺栓"]:
    for m in re.finditer(re.escape(title), text1):
        start = max(0, text1.rfind('## ', 0, m.start()))
        end = min(len(text1), text1.find('## ', m.end()))
        out.append(f"--- MATCH {title} ---")
        out.append(text1[start:end].strip())
        out.append("="*40)

out.append("\n\n=== FILE 2: 母题子题精选结构_重整版一.md ===")
for title in ["水轮机", "安装高度", "法兰螺栓", "螺栓"]:
    for m in re.finditer(re.escape(title), text2):
        start = max(0, text2.rfind('## ', 0, m.start()))
        end = min(len(text2), text2.find('## ', m.end()))
        out.append(f"--- MATCH {title} ---")
        out.append(text2[start:end].strip())
        out.append("="*40)

with open('mother_child_problems.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(out))
print("Done")
