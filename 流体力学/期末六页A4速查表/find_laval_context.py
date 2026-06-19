import os

tex_file_path = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'

with open(tex_file_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

targets = [
    "Laval管外膨胀模板",
    "Laval管内正激波模板",
    "Laval内激波分段链",
    "Laval管内正激波型",
    "Laval管内正激波：",
    "Laval内激波：",
    "Laval管外膨胀/内激波/多波型"
]

with open('laval_sections_in_m4.txt', 'w', encoding='utf-8') as f_out:
    for idx, line in enumerate(lines):
        for t in targets:
            if t in line:
                f_out.write(f"Line {idx+1}: {line}")
                # Print 5 lines before and 15 lines after
                f_out.write("--- Context ---\n")
                start = max(0, idx - 3)
                end = min(len(lines), idx + 15)
                for c_idx in range(start, end):
                    prefix = ">>> " if c_idx == idx else "    "
                    f_out.write(f"{c_idx+1}{prefix}{lines[c_idx]}")
                f_out.write("=" * 60 + "\n\n")

print("Saved Laval context to laval_sections_in_m4.txt")
