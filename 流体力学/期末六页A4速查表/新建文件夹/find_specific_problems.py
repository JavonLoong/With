with open('deduped_problems.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's split by "=== FILE: "
parts = text.split("=== FILE: ")

targets = ['吸水管', '水轮机', '弯管']

found = {t: [] for t in targets}
for part in parts:
    if not part.strip():
        continue
    for t in targets:
        if t in part:
            found[t].append(part)

for t in targets:
    print("*"*40)
    print(f"TARGET: {t} | Found {len(found[t])} matches.")
    print("*"*40)
    # Print the first few matches
    for idx, f in enumerate(found[t][:3]):
        print(f"--- MATCH {idx+1} ---")
        print(f[:800]) # print first 800 chars
        print("\n" + "-"*40 + "\n")
