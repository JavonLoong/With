with open(r'期末六页A4速查表_重整版四_公式重排版.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for idx, line in enumerate(lines):
    if '\\subq{' in line or '\\stepq{' in line or '\\chap{' in line or '\\realq{' in line or '\\infoh{' in line:
        out.append(f"Line {idx+1}: {line.strip()}")

with open('subq_stepq_list.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(out))
print("Done")
