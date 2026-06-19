with open(r'期末六页A4速查表_重整版四_公式重排版.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

mother4_lines = []
in_mother4 = False
for idx, line in enumerate(lines):
    if '母题4' in line and '\\chap' in line:
        in_mother4 = True
    elif in_mother4 and '\\chap' in line:
        # reached next mother topic
        mother4_lines.append((idx+1, line))
        in_mother4 = False
    if in_mother4:
        mother4_lines.append((idx+1, line))

with open('mother4_lines.txt', 'w', encoding='utf-8') as f_out:
    for idx, l in mother4_lines:
        f_out.write(f"{idx}: {l}")

print(f"Mother 4 has {len(mother4_lines)} lines")
