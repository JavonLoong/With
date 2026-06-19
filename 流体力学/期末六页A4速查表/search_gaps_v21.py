import re

file_path = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

keywords = [
    ("PM", ["PM", "Prandtl-Meyer", "膨胀角"]),
    ("Oblique Shock", ["斜激波", "楔角", "波角"]),
    ("Pump Cavitation", ["汽蚀", "安装高度", "泵"]),
    ("Turbine", ["水轮机", "功率"]),
    ("Momentum", ["动量", "弯管", "受力", "喷嘴"]),
    ("Hydrostatic Gate", ["闸门", "受力", "静水压"]),
    ("Hagen-Poiseuille", ["H-P", "Hagen", "层流", "圆管"]),
    ("Wall Law", ["壁面律", "摩擦速度", "底层厚度", "壁面剪"]),
    ("Dimensional Analysis", ["量纲", "相似", "Buckingham"]),
    ("Stress Tensor", ["应力张量", "指定平面", "法向", "切向"])
]

def search_text(kw_list):
    results = []
    for idx, line in enumerate(lines):
        for kw in kw_list:
            if kw in line:
                results.append((idx+1, line.strip()))
                break
    return results

for name, kws in keywords:
    res = search_text(kws)
    print(f"=== {name} (Matches: {len(res)}) ===")
    for line_num, content in res[:8]:
        print(f"Line {line_num}: {content[:100]}")
    print()
