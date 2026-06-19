with open('filtered_sections.txt', 'r', encoding='utf-8') as f:
    content = f.read()

sections = content.split("================================================================================\n")
for idx, sec in enumerate(sections):
    if not sec.strip():
        continue
    lines = sec.strip().split('\n')
    header = lines[0]
    # Find the first few lines of body to print
    body_lines = [l for l in lines[1:4] if l.strip()]
    print(f"[{idx+1}] {header}")
    for bl in body_lines:
        print("  ", bl)
