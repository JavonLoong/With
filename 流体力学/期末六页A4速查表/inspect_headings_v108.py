import re

with open(r'期末六页A4速查表_v108_母题层级强化版.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find all \mt, \sect, \subsection, \section, \qt, \subt, \stepq etc.
lines = text.split("\n")
headings = []
for idx, line in enumerate(lines):
    if any(cmd in line for cmd in [r'\mt{', r'\sect{', r'\section{', r'\subsection{', r'\qt{', r'\subt{', r'\subq{']):
        headings.append(f"{idx+1}: {line.strip()}")

with open('headings_v108.txt', 'w', encoding='utf-8') as f_out:
    for h in headings:
        f_out.write(h + "\n")

print(f"Found {len(headings)} headings in v108")
