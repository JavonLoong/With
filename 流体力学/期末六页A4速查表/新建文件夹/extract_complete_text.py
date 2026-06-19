import re

with open('deduped_problems.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's split by "=== FILE: "
parts = text.split("=== FILE: ")

targets = ['汽蚀', '吸水管', '水轮机', '弯管', '法兰', '喷嘴', '安装高度', '动量']

matched_blocks = []
seen_blocks = set()

for part in parts:
    if not part.strip():
        continue
    # Let's find subtopics inside this file
    # Subtopics are typically separated by \subq{...}
    subsections = re.split(r'(\\subq\{)', part)
    
    # Reassemble subsections
    reassembled = []
    if len(subsections) > 1:
        for i in range(1, len(subsections), 2):
            header_type = subsections[i]
            body = subsections[i+1] if (i+1) < len(subsections) else ""
            reassembled.append(header_type + body)
    else:
        reassembled.append(part)
        
    for sec in reassembled:
        if any(t in sec for t in targets):
            # Normalize to avoid duplicates
            norm = re.sub(r'\s+', '', sec)
            if norm not in seen_blocks:
                seen_blocks.add(norm)
                matched_blocks.append(sec)

with open('matched_utf8.txt', 'w', encoding='utf-8') as out:
    for idx, block in enumerate(matched_blocks):
        out.write("="*80 + "\n")
        out.write(f"BLOCK {idx+1}\n")
        out.write("="*80 + "\n")
        out.write(block + "\n\n")

print(f"Extracted {len(matched_blocks)} blocks.")
