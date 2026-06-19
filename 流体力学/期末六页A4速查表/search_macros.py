import re

fp = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"

with open(fp, 'r', encoding='utf-8') as f:
    text = f.read()

macros = ["schemeshock", "schemeviscous", "schemebl"]

for m in macros:
    print(f"=== MACRO: {m} ===")
    pattern = r'\\newcommand\{\\' + m + r'\}(.*?)(?=\\newcommand|\\mt|\\begin\{document\}|$)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        print(match.group(0))
    else:
        # Just search for the definition in a simpler way
        pattern_simple = r'\\' + m + r'\b'
        match_idx = text.find("\\newcommand{\\" + m + "}")
        if match_idx != -1:
            print(text[match_idx:match_idx+1500])
        else:
            print("Not found")
    print("-" * 50)
