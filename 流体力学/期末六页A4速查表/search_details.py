import re

with open(r'all_matched_details.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's write a search script that outputs paragraphs matching key phrases
keywords = [
    r"离心泵",
    r"水轮机",
    r"螺栓",
    r"PM",
    r"斜激波",
    r"张量",
    r"壁律",
    r"量纲"
]

for kw in keywords:
    print(f"--- MATCHES FOR: {kw} ---")
    matches = re.findall(rf"(Index: \d+ \| Keywords: .*?\n.*?(?=\nIndex: \d+ \| Keywords: |$))", content, re.DOTALL)
    count = 0
    for match in matches:
        if re.search(kw, match):
            count += 1
            print(match[:500] + "\n... [TRUNCATED]\n")
            if count >= 3:
                break
