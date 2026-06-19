with open(r'期末六页A4速查表_重整版四_公式重排版.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for idx, line in enumerate(lines):
    if '\\section' in line or '\\subsection' in line or '\\chap' in line or '母题' in line:
        if len(line.strip()) < 150:
            out.append(f"Line {idx+1}: {line.strip()}")

with open('inspected_headings_utf8.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(out))
print("Done")
