import re

fp = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"

with open(fp, 'r', encoding='utf-8') as f:
    text = f.read()

queries = ["水轮机", "安装高度", "应力张量", "PM", "弯管", "量纲", "闸门", "壁律", "层流"]

with open('search_results_utf8.txt', 'w', encoding='utf-8') as f_out:
    for q in queries:
        f_out.write(f"=== SEARCH: {q} ===\n")
        matches = [m.start() for m in re.finditer(re.escape(q), text)]
        f_out.write(f"Found {len(matches)} matches\n")
        for idx in matches[:5]:
            start = max(0, idx - 150)
            end = min(len(text), idx + 450)
            f_out.write(text[start:end])
            f_out.write("\n" + "-"*50 + "\n")
        f_out.write("="*80 + "\n\n")

print("Done searching and writing to search_results_utf8.txt")
