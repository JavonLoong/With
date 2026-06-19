import re

with open('exact_topic_latex.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's search for \qt{...} or \subq{...} blocks
# Since exact_topic_latex.txt has many matches, let's search for sections with \qt or \subq or \realq or \ans
# that contain specific keywords.

keywords = ["PM", "斜激波", "吸水", "水轮机", "法兰", "闸门", "层流", "壁律", "量纲", "应力张量"]

with open('concrete_problems.txt', 'w', encoding='utf-8') as f_out:
    # Let's find matches in the source file directly, as it's more complete.
    fp_src = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"
    with open(fp_src, 'r', encoding='utf-8') as f:
        src_content = f.read()
    
    # split by \qt or \subq or \realq or \conceptq or \stepq
    items = re.split(r'(\\qt|\\subq|\\realq|\\stepq|\\conceptq|\\symq|\\formq|\\quickq|\\errq|\\warn)', src_content)
    
    rebuilt = []
    for i in range(1, len(items), 2):
        rebuilt.append(items[i] + items[i+1])
        
    for kw in keywords:
        f_out.write(f"=== KEYWORD: {kw} ===\n")
        matches = [item for item in rebuilt if kw.lower() in item.lower()]
        matches.sort(key=len, reverse=True)
        for m in matches[:5]:
            f_out.write(m.strip() + "\n")
            f_out.write("-" * 50 + "\n")
        f_out.write("=" * 80 + "\n\n")

print("Done extracting concrete problems")
