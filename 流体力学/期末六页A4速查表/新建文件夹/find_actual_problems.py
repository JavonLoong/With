with open('matched_readable.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's search for actual problems with numerical examples.
# Typically they look like \qt{...} or \realq{...} or contains "已知" and numbers.
sections = content.split("================================================================================\n")

for idx, sec in enumerate(sections):
    if not sec.strip():
        continue
    # Let's see if it has numbers like "kW" or "kPa" or "m" and keywords
    if any(k in sec for k in ['吸水管', '汽蚀', '水轮机', '弯管', '法兰']):
        if '已知' in sec or '真题' in sec or '原题' in sec:
            lines = sec.strip().split('\n')
            # Let's print the first 20 lines of the section
            print(f"--- Section {idx} ---")
            for l in lines[:25]:
                print(l)
            print("...\n" + "-"*40)
