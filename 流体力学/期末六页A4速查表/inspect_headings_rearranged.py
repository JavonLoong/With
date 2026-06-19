with open('期末六页A4速查表_重整版四_公式重排版.tex', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split("\n")
headings = []
for idx, line in enumerate(lines):
    if any(cmd in line for cmd in [r'\mt{', r'\sect{', r'\section{', r'\subsection{', r'\qt{', r'\subt{', r'\subq{', r'\chap{']):
        headings.append(f"{idx+1}: {line.strip()}")

with open('headings_rearranged.txt', 'w', encoding='utf-8') as f_out:
    for h in headings:
        f_out.write(h + "\n")

print(f"Found {len(headings)} headings in rearranged")
