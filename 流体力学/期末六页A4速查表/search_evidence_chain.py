import os
import re

files_to_search = [
    r'd:\虚拟C盘\学习\流体力学\全目录试题_证据链\全目录试题评判报告_证据链.md',
    r'd:\虚拟C盘\学习\流体力学\全目录试题_证据链\母题精选结构_原证据链.md',
    r'd:\虚拟C盘\学习\流体力学\期末习题_证据链\03_流动动力学_量纲_应用\题目.md',
    r'd:\虚拟C盘\学习\流体力学\速查表v10_全景对比\03_期末.md'
]

keywords = ["D1=200mm", "水轮机", "泵吸水管最大安装高度", "最大安装高度"]

results = []

for filepath in files_to_search:
    if not os.path.exists(filepath):
        results.append(f"File not found: {filepath}")
        continue
    results.append(f"\n========================================\nFILE: {filepath}\n========================================")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for kw in keywords:
        for m in re.finditer(re.escape(kw), content):
            start = max(0, content.rfind('\n\n', 0, m.start()))
            end = min(len(content), content.find('\n\n', m.end()))
            results.append(f"--- KEYWORD '{kw}' Match ---")
            results.append(content[start:end].strip())
            results.append("-" * 30)

with open('target_questions_search_results.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(results))
print("Done")
