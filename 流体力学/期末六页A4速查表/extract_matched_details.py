with open(r'selected_matches.txt', 'r', encoding='utf-8') as f:
    text = f.read()

keywords = ["泵", "吸水", "水轮机", "动量", "弯管", "法兰", "螺栓", "PM", "膨胀", "斜激波", "张量", "壁律", "量纲"]

matches = []
paragraphs = text.split("\n\n")
for para in paragraphs:
    matched_kws = [kw for kw in keywords if kw in para]
    if matched_kws:
        matches.append((para, matched_kws))

with open('all_matched_details.txt', 'w', encoding='utf-8') as f_out:
    for i, (para, kws) in enumerate(matches):
        f_out.write(f"Index: {i+1} | Keywords: {kws}\n")
        f_out.write(para + "\n")
        f_out.write("="*80 + "\n")

print(f"Extracted {len(matches)} matching paragraphs")
