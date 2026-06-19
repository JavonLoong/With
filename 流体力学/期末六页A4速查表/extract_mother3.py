with open(r'期末六页A4速查表_重整版四_公式重排版.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

mother3_lines = []
in_mother3 = False
for idx, line in enumerate(lines):
    if '母题3' in line and '\\chap' in line:
        in_mother3 = True
    elif in_mother3 and '母题4' in line and '\\chap' in line:
        # reached next mother topic
        mother3_lines.append((idx+1, line))
        in_mother3 = False
    if in_mother3:
        mother3_lines.append((idx+1, line))

with open('mother3_lines.txt', 'w', encoding='utf-8') as f_out:
    for idx, l in mother3_lines:
        f_out.write(f"{idx}: {l}")

print(f"Mother 3 has {len(mother3_lines)} lines")
