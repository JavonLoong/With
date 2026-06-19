with open('search_results.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's extract sections containing '膨胀角' or 'PM' or '斜激波'
sections = text.split('--- Paragraph')
selected = []
for sec in sections:
    if '膨胀角' in sec or 'PM' in sec or '斜激波' in sec or '泵吸水管' in sec or '法兰' in sec or '螺栓' in sec:
        if len(sec.strip()) > 50:
            selected.append("--- Paragraph" + sec)

with open('selected_matches.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(selected))

print(f"Extracted {len(selected)} selected matches")
