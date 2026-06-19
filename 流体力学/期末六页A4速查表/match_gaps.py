import re

with open('all_qt_blocks.txt', 'r', encoding='utf-8') as f:
    blocks_text = f.read()

blocks = blocks_text.split("="*80 + "\n\n")

keywords_map = {
    "PM": ["PM", "膨胀角", "Prandtl"],
    "Oblique Shock": ["斜激波", "楔角", "波角"],
    "Pump": ["安装高度", "汽蚀", "吸水"],
    "Turbine": ["水轮机"],
    "Momentum": ["动量", "弯管", "法兰", "螺栓", "受力"],
    "Hydrostatic": ["闸门", "压力中心", "浮力", "静水"],
    "Hagen-Poiseuille": ["Poiseuille", "层流", "圆管层流"],
    "Wall Law": ["壁律", "摩擦速度", "底层", "对数"],
    "Dimensional Analysis": ["量纲", "相似", "毕", "Buckingham"],
    "Stress Tensor": ["应力张量", "法向应力", "切应力"]
}

with open('matched_gap_blocks.txt', 'w', encoding='utf-8') as f_out:
    for gap_name, kws in keywords_map.items():
        f_out.write(f"==================================================\n")
        f_out.write(f"=== GAP: {gap_name} ===\n")
        f_out.write(f"==================================================\n")
        found_blocks = []
        for b in blocks:
            # Check if any keyword matches
            match = False
            for kw in kws:
                if kw.lower() in b.lower():
                    match = True
                    break
            if match:
                found_blocks.append(b)
        
        # Sort by relevance (e.g., length or number of matches)
        found_blocks.sort(key=len)
        for fb in found_blocks[:3]: # top 3 shortest or most relevant blocks
            f_out.write(fb.strip() + "\n")
            f_out.write("-" * 50 + "\n")
        f_out.write("\n\n")

print("Matched blocks written to matched_gap_blocks.txt")
