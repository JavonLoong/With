import re

fp = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"

with open(fp, 'r', encoding='utf-8') as f:
    text = f.read()

# We want to extract blocks. Let's extract every \qt{...} and its immediate siblings up to the next \qt or \mt or \sect
pattern = r'(\\qt\{.*?\})(.*?)(?=\\qt|\\mt|\\sect|\\begin\{multicols\}|\\end\{document\}|$)'
matches = re.findall(pattern, text, re.DOTALL)

with open('all_qt_blocks.txt', 'w', encoding='utf-8') as f_out:
    for i, (qt_head, qt_body) in enumerate(matches):
        f_out.write(f"=== BLOCK {i+1} ===\n")
        f_out.write(qt_head + "\n")
        f_out.write(qt_body.strip() + "\n")
        f_out.write("="*80 + "\n\n")

print(f"Done extracting {len(matches)} blocks")
