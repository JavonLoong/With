import re

with open(r'd:\虚拟C盘\学习\流体力学\速查表v8_全量测试评判报告\05_全量逐题解决路径.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's search for "水轮机" and find the block containing it.
# We will write all paragraphs containing "水轮机" or "螺栓" or "法兰" or "吸水管" to a utf-8 file.

matches = []
for word in ["水轮机", "螺栓", "法兰", "吸水管"]:
    for m in re.finditer(word, text):
        start = max(0, text.rfind('\n\n', 0, m.start()))
        end = min(len(text), text.find('\n\n', m.end()))
        matches.append(f"--- MATCH FOR {word} ---")
        matches.append(text[start:end].strip())
        matches.append("="*50)

with open('extracted_v8_questions.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(matches))
