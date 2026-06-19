with open(r'd:\虚拟C盘\学习\流体力学\速查表v8_全量测试评判报告\05_全量逐题解决路径.md', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Let's search for "水轮机"
matches_turbine = [m.start() for m in re.finditer(r'水轮机', text)]
print("--- TURBINE MATCHES ---")
for m in matches_turbine[:5]:
    start = max(0, text.rfind('\n', 0, m) - 100)
    end = min(len(text), text.find('\n', m) + 500)
    print(text[start:end])
    print("*"*40)

# Let's search for "螺栓" or "法兰"
matches_bolt = [m.start() for m in re.finditer(r'螺栓|法兰', text)]
print("--- BOLT MATCHES ---")
for m in matches_bolt[:5]:
    start = max(0, text.rfind('\n', 0, m) - 100)
    end = min(len(text), text.find('\n', m) + 500)
    print(text[start:end])
    print("*"*40)
