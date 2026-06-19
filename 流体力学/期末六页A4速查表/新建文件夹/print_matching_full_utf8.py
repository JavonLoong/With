import os
import re

folder = r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一'
tex_files = [f for f in os.listdir(folder) if f.endswith('.tex')]

keywords = ['汽蚀', '安装高度', '吸水管', '水轮机', '弯管', '法兰', '喷嘴', '动量']

results = []

for f in tex_files:
    path = os.path.join(folder, f)
    with open(path, 'rb') as file_obj:
        content = file_obj.read().decode('utf-8', errors='ignore')
    
    sections = re.split(r'(\\subq\{|\\conceptq\{|\\stepq\{|\\infoh\{|\\errq\{)', content)
    reassembled = []
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            header_type = sections[i]
            body = sections[i+1] if (i+1) < len(sections) else ""
            reassembled.append(header_type + body)
            
    for sec in reassembled:
        if any(kw in sec for kw in keywords):
            if '原题' in sec or '作业' in sec or 'N' in sec:
                results.append((f, sec))

# Let's deduplicate based on section content (ignoring whitespace)
seen = set()
deduped = []
for f, sec in results:
    norm = re.sub(r'\s+', '', sec)
    if norm not in seen:
        seen.add(norm)
        deduped.append((f, sec))

with open('deduped_problems.txt', 'w', encoding='utf-8') as out:
    for f, sec in deduped:
        out.write(f"=== FILE: {f} ===\n")
        out.write(sec + "\n\n")

print(f"Deduplicated to {len(deduped)} problems.")
