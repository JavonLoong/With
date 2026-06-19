with open(r'd:\虚拟C盘\学习\流体力学\速查表v8_全量测试评判报告\05_全量逐题解决路径.md', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'hf 1 = 0\.0216', text)]

out = []
for idx, m in enumerate(matches):
    start = m
    end = min(len(text), m + 1500)
    out.append(f"--- MATCH {idx} ---")
    out.append(text[start:end])
    out.append("="*80)

with open('turbine_more.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(out))
