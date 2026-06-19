with open('headings_v108.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    if "母题" in line:
        print(line.strip())
