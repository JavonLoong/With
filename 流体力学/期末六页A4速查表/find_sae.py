with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
for idx, line in enumerate(lines):
    if "SAE 10W30" in line or "2006" in line:
        print(f"L{idx+1}: {line}")
        for j in range(idx-1, idx+10):
            print(f"{j+1}: {lines[j]}")
        print("="*40)
