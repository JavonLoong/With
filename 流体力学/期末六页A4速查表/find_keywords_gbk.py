import re
import os

files = [
    r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版一.tex',
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
]

for fp in files:
    if not os.path.exists(fp):
        print(f"Not found: {fp}")
        continue
    print(f"=== File: {fp} ===")
    with open(fp, 'r', encoding='gbk', errors='ignore') as f:
        content = f.read()
    # Search for any matches of "离心泵" or "吸水管"
    matches = list(re.finditer(r'(离心泵|吸水管|水轮机|弯管|法兰|螺栓|膨胀角|斜激波|HP|Poiseuille|量纲|张量)', content))
    print(f"Total matches found: {len(matches)}")
    found_count = 0
    for m in matches:
        start = max(0, m.start() - 100)
        end = min(len(content), m.end() + 100)
        print(f"Pos {m.start()}: {content[start:end]}")
        print("-" * 50)
        found_count += 1
        if found_count >= 15:
            print("Truncated after 15 matches...")
            break
