import os
import re

folder = r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一'
tex_files = [f for f in os.listdir(folder) if f.endswith('.tex')]

search_terms = ['吸水管', '安装高度', '汽蚀', '水轮机', '弯管', '法兰', '喷嘴', '动量']

results = []
for f in tex_files:
    path = os.path.join(folder, f)
    with open(path, 'rb') as file_obj:
        content = file_obj.read().decode('utf-8', errors='ignore')
    
    for term in search_terms:
        matches = list(re.finditer(re.escape(term), content))
        if matches:
            results.append((f, term, len(matches)))

for r in results:
    print(f"File: {r[0]}, Term: {r[1]}, Matches: {r[2]}")
