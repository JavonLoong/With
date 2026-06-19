import sys

with open(r'd:\虚拟C盘\学习\流体力学\速查表v8_全量测试评判报告\05_全量逐题解决路径.md', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'Q0338', text)]

out = []
out.append(f"Found {len(matches)} matches")
for idx, m in enumerate(matches):
    start = max(0, m - 500)
    end = min(len(text), m + 1500)
    out.append(f"Match {idx} at position {m}:")
    out.append(text[start:end])
    out.append("="*80)

matches_bolt = [m.start() for m in re.finditer(r'法兰螺栓|每个螺栓|喷嘴法兰', text)]
out.append(f"Found {len(matches_bolt)} bolt matches")
for idx, m in enumerate(matches_bolt):
    start = max(0, m - 500)
    end = min(len(text), m + 1500)
    out.append(f"Bolt Match {idx} at position {m}:")
    out.append(text[start:end])
    out.append("="*80)

with open('q0338_and_bolt.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(out))
