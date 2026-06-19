import os

path = r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版十六_旧版关键词归位稿.tex'
if not os.path.exists(path):
    # try another filename
    path = r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版十二_审计缺口闭合稿.tex'

with open(path, 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')

# Search for the questions
# Let's split by \qt{
parts = content.split('\\qt{')

results = []
for p in parts:
    if '镀锌钢管' in p or '水轮机管路' in p:
        results.append('\\qt{' + p)

with open('latex_extracted.txt', 'w', encoding='utf-8') as out:
    for r in results:
        out.write(r + '\n' + "="*40 + '\n')

print("Done, extracted", len(results), "sections.")
