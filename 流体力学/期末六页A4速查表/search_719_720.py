with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'(7\.19|7\.20)', text)
for m in matches:
    start = max(0, m.start() - 100)
    end = min(len(text), m.end() + 300)
    print(f"Match: {text[start:end]}")
    print("=" * 50)
