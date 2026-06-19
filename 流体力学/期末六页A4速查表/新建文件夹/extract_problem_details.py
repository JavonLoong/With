import os
import re

folder = r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一'
tex_files = [f for f in os.listdir(folder) if f.endswith('.tex')]

keywords = ['汽蚀', '安装高度', '吸水管', '水轮机', '弯管', '法兰', '喷嘴', '动量']

extracted = {}

for f in tex_files:
    path = os.path.join(folder, f)
    with open(path, 'rb') as file_obj:
        content = file_obj.read().decode('utf-8', errors='ignore')
    
    # Let's split by \subq or other headers to find the sections
    sections = re.split(r'(\\subq\{|\\conceptq\{|\\stepq\{|\\infoh\{|\\errq\{)', content)
    
    # Reassemble sections
    reassembled = []
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            header_type = sections[i]
            body = sections[i+1] if (i+1) < len(sections) else ""
            reassembled.append(header_type + body)
            
    for sec in reassembled:
        for kw in keywords:
            if kw in sec:
                # Get the first line as a title to identify
                first_line = sec.split('\n')[0]
                key = (first_line, kw)
                if key not in extracted or len(sec) > len(extracted[key]):
                    extracted[key] = sec

with open('extracted_sections.txt', 'w', encoding='utf-8') as out:
    for (title, kw), sec in extracted.items():
        out.write("="*80 + "\n")
        out.write(f"KEYWORD: {kw} | TITLE: {title}\n")
        out.write("="*80 + "\n")
        out.write(sec + "\n\n")

print("Done! Extracted", len(extracted), "sections.")
