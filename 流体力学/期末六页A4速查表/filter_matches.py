import re

with open(r'selected_matches.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's search for "离心泵" or "泵" or "吸水管" or "水轮机" or "动量" or "PM" or "膨胀" or "斜激波" in selected_matches.txt
keywords = ["泵", "吸水", "水轮机", "动量", "弯管", "法兰", "PM", "膨胀", "斜激波", "静水", "闸门", "壁律", "量纲"]

matches = []
paragraphs = text.split("\n\n")
for para in paragraphs:
    for kw in keywords:
        if kw in para:
            matches.append(para)
            break

with open('filtered_matches.txt', 'w', encoding='utf-8') as f_out:
    for i, match in enumerate(matches):
        f_out.write(f"Match {i+1}:\n{match}\n")
        f_out.write("="*40 + "\n")

print(f"Found {len(matches)} matching paragraphs")
