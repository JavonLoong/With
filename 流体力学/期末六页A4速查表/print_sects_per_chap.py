with open('期末六页A4速查表_v108_母题层级强化版.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's split by chap
import re
chaps = re.split(r'\\chap\{', text)
for i in range(1, len(chaps)):
    chap_title = chaps[i].split('}')[0]
    print(f"Chap {i}: {chap_title}")
    # find all \sect in this chap
    sects = re.findall(r'\\sect\{([^}]+)\}', chaps[i])
    for s in sects[:15]:  # print first 15 sects
        print(f"  Sect: {s}")
