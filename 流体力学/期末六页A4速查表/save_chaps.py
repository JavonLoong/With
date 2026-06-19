with open('期末六页A4速查表_v108_母题层级强化版.tex', 'r', encoding='utf-8') as f:
    chaps = []
    for idx, line in enumerate(f):
        if '\\chap{' in line:
            chaps.append(f"{idx+1}: {line.strip()}")
with open('chaps_utf8.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(chaps))
