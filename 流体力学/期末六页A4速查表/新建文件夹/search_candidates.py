with open('numerical_candidates.txt', 'r', encoding='utf-8') as f:
    text = f.read()

parts = text.split("=== FILE: ")
targets = ['吸水', '汽蚀', '安装高度', '水轮机', '弯管', '法兰', '螺栓', '喷嘴']

matched = []
for p in parts:
    if not p.strip():
        continue
    # Check if the text matches
    found_kws = [t for t in targets if t in p]
    if found_kws:
        # Check if it has actual problem statement
        matched.append((found_kws, p))

with open('numerical_matched.txt', 'w', encoding='utf-8') as out:
    for kws, p in matched:
        out.write("="*80 + "\n")
        out.write(f"KEYWORDS: {kws}\n")
        out.write("="*80 + "\n")
        out.write(p + "\n\n")

print(f"Matched {len(matched)} problems.")
