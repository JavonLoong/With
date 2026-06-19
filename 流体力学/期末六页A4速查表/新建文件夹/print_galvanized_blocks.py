with open('numerical_matched.txt', 'r', encoding='utf-8') as f:
    text = f.read()

parts = text.split("================================================================================\n")
for idx, p in enumerate(parts):
    if '镀锌钢管' in p:
        print(f"--- BLOCK {idx} containing 镀锌钢管 ---")
        print(p)
        print("*"*60)
