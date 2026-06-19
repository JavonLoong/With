import re

with open(r'd:\虚拟C盘\学习\流体力学\速查表v8_全量测试评判报告\05_全量逐题解决路径.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find the sections starting with "3. 水轮机输出功率"
# and "7.有一水平喷嘴"
# and "2. 泵吸水管最大安装高度" or similar.

def extract_section(title, text):
    matches = [m.start() for m in re.finditer(re.escape(title), text)]
    results = []
    for idx, m in enumerate(matches):
        # Let's extract 2000 characters after the title
        end = min(len(text), m + 2000)
        results.append(f"=== MATCH {idx} FOR {title} ===")
        results.append(text[m:end])
    return "\n\n".join(results)

out_text = ""
out_text += extract_section("3. 水轮机输出功率", text) + "\n\n"
out_text += extract_section("固定喷嘴法兰螺栓上所受的力", text) + "\n\n"
out_text += extract_section("2. 泵吸水管最大安装高度", text) + "\n\n"

with open('full_extracted_solutions.txt', 'w', encoding='utf-8') as f_out:
    f_out.write(out_text)
