with open(r'd:\虚拟C盘\学习\流体力学\速查表v8_全量测试评判报告\05_全量逐题解决路径.md', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'3\.\s*水轮机输出功率', text)]

out = []
for idx, m in enumerate(matches):
    start = max(0, text.rfind('\n#', 0, m))
    end = min(len(text), text.find('\n#', m + 50))
    if end == -1 or end <= m:
        end = m + 4000
    out.append(f"--- MATCH {idx} ---")
    out.append(text[start:end])
    out.append("="*80)

with open('turbine_full_extracted.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(out))
