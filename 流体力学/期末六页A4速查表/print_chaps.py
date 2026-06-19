with open('期末六页A4速查表_v108_母题层级强化版.tex', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if '\\chap{' in line:
            print(f"{idx+1}: {line.strip()}")
