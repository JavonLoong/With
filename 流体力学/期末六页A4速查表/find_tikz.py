with open(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex", 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_tikz = False
tikz_lines = []
for idx, line in enumerate(lines):
    if '\\begin{tikzpicture}' in line:
        in_tikz = True
        tikz_lines.append(f"--- TikZ at Line {idx+1} ---")
    if in_tikz:
        tikz_lines.append(line.strip())
    if '\\end{tikzpicture}' in line:
        in_tikz = False

with open("tikz_blocks.txt", "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(tikz_lines))

print("Done. Saved to tikz_blocks.txt")
