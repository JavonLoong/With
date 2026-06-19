with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
for idx, line in enumerate(lines):
    if "70" in line or "30" in line:
        if any(x in line for x in ["水轮", "功率", "管"]):
            print(f"L{idx+1}: {line}")
            print("="*40)
