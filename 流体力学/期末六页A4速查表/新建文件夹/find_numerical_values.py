import os
import re

folder = r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一'
tex_files = [f for f in os.listdir(folder) if f.endswith('.tex')]

keywords = ['汽蚀', '吸水管', '安装高度', '水轮机', '弯管', '法兰', '螺栓', '喷嘴']

results = []
for f in tex_files:
    path = os.path.join(folder, f)
    with open(path, 'rb') as file_obj:
        content = file_obj.read().decode('utf-8', errors='ignore')
    
    # Let's search for \qt{...} blocks
    # A block starts with \qt{ and ends before another \qt{ or \mt{ or \subq{
    blocks = re.split(r'(\\qt\{|\\subq\{|\\realq\{)', content)
    reassembled = []
    if len(blocks) > 1:
        for i in range(1, len(blocks), 2):
            header = blocks[i]
            body = blocks[i+1] if (i+1) < len(blocks) else ""
            reassembled.append(header + body)
            
    for b in reassembled:
        if any(kw in b for kw in keywords):
            # Check if it has numbers like "kW" or "kPa" or "N" or digits
            digits = re.findall(r'\d+', b)
            if len(digits) > 3: # likely has numbers
                results.append((f, b))

# Deduplicate
seen = set()
dedup = []
for f, b in results:
    norm = re.sub(r'\s+', '', b)
    if norm not in seen:
        seen.add(norm)
        dedup.append((f, b))

print(f"Found {len(dedup)} numerical problem candidates.")
with open('numerical_candidates.txt', 'w', encoding='utf-8') as out:
    for f, b in dedup:
        out.write(f"=== FILE: {f} ===\n")
        out.write(b + "\n\n")
