with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
for idx, line in enumerate(lines):
    if "水轮机" in line and "D=20" in line:
        print(f"Match found at line {idx+1}:")
        for j in range(idx-2, idx+15):
            print(f"{j+1}: {lines[j]}")
        print("="*50)
