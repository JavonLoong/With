with open('期末六页A4速查表_v108_母题层级强化版.tex', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'泵安装高度|泵吸水安装高度', text)]
for m in matches:
    # Print 10 lines around match
    start = max(0, text.rfind('\n', 0, m) - 100)
    end = min(len(text), text.find('\n', m) + 200)
    print(f"--- MATCH AT {m} ---")
    print(text[start:end])
    print("*"*40)
