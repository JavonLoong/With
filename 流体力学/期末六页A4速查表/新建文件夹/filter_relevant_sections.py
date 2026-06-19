import re

with open('extracted_sections.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's split by the separator line "================================================================================"
sections = content.split("================================================================================\n")

keywords_to_keep = ['安装高度', '水轮机', '弯管', '法兰', '吸水管']

filtered = []
for sec in sections:
    if not sec.strip():
        continue
    # Let's see if it has the keyword or title that is relevant
    first_lines = sec.split('\n')
    header_line = first_lines[0] if len(first_lines) > 0 else ""
    
    # We want to find sections that contain a subq with latex math and description
    # of a specific problem
    if any(kw in sec for kw in keywords_to_keep):
        # We only want sections that have actual numerical problem text like "原题" or numbers
        if '原题' in sec or '作业' in sec or 'N' in sec or 'm' in sec or 'kg' in sec or 'MPa' in sec:
            filtered.append(sec)

print(f"Found {len(filtered)} filtered sections.")

with open('filtered_sections.txt', 'w', encoding='utf-8') as out:
    for sec in filtered:
        out.write("="*80 + "\n")
        out.write(sec + "\n")
