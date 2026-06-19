import re
with open('期末六页A4速查表_v108_母题层级强化版.tex', 'r', encoding='utf-8') as f:
    text = f.read()

chaps = re.split(r'\\chap\{', text)
output = []
for i in range(1, len(chaps)):
    chap_title = chaps[i].split('}')[0]
    output.append(f"Chap {i}: {chap_title}")
    sects = re.findall(r'\\sect\{([^}]+)\}', chaps[i])
    for s in sects:
        output.append(f"  Sect: {s}")
with open('sects_utf8.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(output))
