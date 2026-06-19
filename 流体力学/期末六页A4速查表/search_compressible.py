with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'\\qt\{([^{}]+)\}', text)
for m in matches:
    content = m.group(1)
    if any(x in content for x in ["膨胀", "PM", "Prandtl", "斜激波", "楔角"]):
        start = m.start()
        end = start + 300
        # find matching \ans or \chain
        print(f"L{text.count(chr(10), 0, start)+1}: {text[start:end]}")
        print("-" * 50)
