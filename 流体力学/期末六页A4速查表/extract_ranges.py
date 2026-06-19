# Let's search for regions of text in v21 around specific matching lines.
with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

# Let's write a python script to find all matching blocks with their line ranges and save them.
# The tags are \qt{...} and \ans{...} or similar.
# Let's find some key lines:
# 1. Pump Cavitation / Installation Height: around line 131-150.
# 2. Turbine: around line 135.
# 3. Hagen-Poiseuille: around line 196, 2194.
# 4. Wall Law: around line 642, 2210.
# 5. Stress Tensor: around line 285, 411.
# 6. PM: around the compressible flow section.
# Let's write a script that extracts blocks of lines.

lines = text.splitlines()

def save_range(name, start, end):
    with open(f"extract_{name}.txt", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(lines[start-1:end]))
    print(f"Saved {name} (lines {start} to {end})")

save_range("pump_turbine", 120, 160)
save_range("hp_wall", 2170, 2225)
save_range("stress", 280, 310)
save_range("stress_macro", 405, 430)
