import re

file_path = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# search for tikzpicture
tikz_blocks = []
in_tikz = False
current_block = []
for idx, line in enumerate(text.splitlines()):
    if '\\begin{tikzpicture}' in line:
        in_tikz = True
        current_block = [f"Line {idx+1}"]
    if in_tikz:
        current_block.append(line)
    if '\\end{tikzpicture}' in line:
        in_tikz = False
        tikz_blocks.append("\n".join(current_block))

print("Total tikz blocks in v21:", len(tikz_blocks))
for block in tikz_blocks:
    if 'Hg' in block or 'h' in block or 'U' in block:
        print(block)
        print("="*40)
