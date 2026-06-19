import re

file_path = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find all \qt{...} and matching blocks.
# We can search using regex.
matches = re.finditer(r'\\qt\{([^{}]+)\}', text)
blocks = []
for m in matches:
    start_pos = m.start()
    # Find the matching \ans or \chain or \res or \form
    # We can take the substring from start_pos to the next \qt{ or \mt{ or \chap{
    end_match = re.search(r'\\(qt|mt|chap|sect)\{', text[start_pos+1:])
    if end_match:
        end_pos = start_pos + 1 + end_match.start()
    else:
        end_pos = len(text)
    block_text = text[start_pos:end_pos].strip()
    blocks.append(block_text)

print("Found blocks:", len(blocks))

# Let's search inside these blocks for the key terms
targets = [
    ("PM", ["PM", "Prandtl-Meyer", "膨胀"]),
    ("Oblique Shock", ["斜激波"]),
    ("Pump Cavitation", ["汽蚀", "吸水"]),
    ("Turbine", ["水轮机"]),
    ("Momentum", ["动量", "弯管", "喷嘴"]),
    ("Hydrostatic Gate", ["闸门", "静水"]),
    ("Hagen-Poiseuille", ["H-P", "Hagen", "Poiseuille", "层流"]),
    ("Wall Law", ["壁面律", "摩擦速度", "底层厚度"]),
    ("Dimensional Analysis", ["量纲", "Buckingham"]),
    ("Stress Tensor", ["应力张量", "指定平面", "法向"])
]

import os
os.makedirs("extracted_gaps", exist_ok=True)

for name, kws in targets:
    matched_blocks = []
    for b in blocks:
        for kw in kws:
            if kw in b:
                matched_blocks.append(b)
                break
    out_path = f"extracted_gaps/{name.replace(' ', '_').lower()}.txt"
    with open(out_path, "w", encoding="utf-8") as f_out:
        f_out.write("\n\n========================================\n\n".join(matched_blocks))
    print(f"Saved {len(matched_blocks)} blocks for {name} to {out_path}")
