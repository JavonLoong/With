with open(r'selected_matches.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines[:100]):
    print(f"{idx+1}: {line.strip()}")
