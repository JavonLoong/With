with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
for idx, line in enumerate(lines):
    if "量纲" in line or "相似" in line or "派" in line:
        if any(x in line for x in ["定理", "分析", "系数"]):
            print(f"L{idx+1}: {line}")
            for j in range(idx-1, idx+10):
                print(f"{j+1}: {lines[j]}")
            print("="*40)
