import re

filepath = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

keywords = ['膨胀角', 'PM', '斜激波', '泵吸水管', '汽蚀', '水轮机', '法兰', '螺栓', '静水', '闸门', 'H-P', '层流']
results = []

# split by paragraph or section
paragraphs = content.split('\n\n')
for idx, para in enumerate(paragraphs):
    matched = []
    for kw in keywords:
        if kw in para:
            matched.append(kw)
    if matched:
        # check size of paragraph to avoid printing the whole file
        if len(para) < 2000:
            results.append(f"--- Paragraph {idx} (Matches: {matched}) ---\n{para}\n")
        else:
            results.append(f"--- Paragraph {idx} (Matches: {matched}, Size: {len(para)}) ---\n{para[:1000]}... [TRUNCATED]\n")

with open('search_results.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(results))

print(f"Done, found {len(results)} matches")
