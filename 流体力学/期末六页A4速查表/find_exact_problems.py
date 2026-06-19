import re

with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()

# Search helper
def search_kw(kw_list, exclude=None):
    results = []
    for idx, line in enumerate(lines):
        if any(kw in line for kw in kw_list):
            if exclude and any(ex in line for ex in exclude):
                continue
            # find surrounding \qt and \ans
            start = max(0, idx - 10)
            end = min(len(lines), idx + 25)
            # Find the actual block
            block = []
            for j in range(start, end):
                block.append(f"{j+1}: {lines[j]}")
            results.append((idx+1, "\n".join(block)))
    return results

print("=== SEARCHING PUMP / CAVITATION ===")
for line_num, block in search_kw(["汽蚀", "NPSH", "吸水"])[:3]:
    print(f"Line {line_num}:\n{block}\n" + "="*40)

print("=== SEARCHING TURBINE ===")
for line_num, block in search_kw(["水轮机"])[:3]:
    print(f"Line {line_num}:\n{block}\n" + "="*40)

print("=== SEARCHING MOMENTUM ===")
for line_num, block in search_kw(["弯管", "射流冲板", "法兰"])[:3]:
    print(f"Line {line_num}:\n{block}\n" + "="*40)

print("=== SEARCHING GATE / PRESSURE CENTER ===")
for line_num, block in search_kw(["闸门", "形心", "曲面闸门"])[:3]:
    print(f"Line {line_num}:\n{block}\n" + "="*40)

print("=== SEARCHING HAGEN-POISEUILLE ===")
for line_num, block in search_kw(["Hagen", "Poiseuille", "层流", "圆管层流"])[:3]:
    print(f"Line {line_num}:\n{block}\n" + "="*40)

print("=== SEARCHING WALL LAW ===")
for line_num, block in search_kw(["壁律", "底层", "摩擦速度", "sublayer"])[:3]:
    print(f"Line {line_num}:\n{block}\n" + "="*40)

print("=== SEARCHING DIMENSIONAL ANALYSIS ===")
for line_num, block in search_kw(["量纲", "Buckingham", "无量纲"])[:3]:
    print(f"Line {line_num}:\n{block}\n" + "="*40)

print("=== SEARCHING STRESS TENSOR ===")
for line_num, block in search_kw(["应力张量", "应力矢量"])[:3]:
    print(f"Line {line_num}:\n{block}\n" + "="*40)
