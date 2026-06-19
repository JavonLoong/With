import re

fp = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"

with open(fp, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find all \qt{...} and \ans{...} or \subq or \realq or whatever.
# We'll split the file by \qt or \subq or \realq or \section or \subsection or \paragraph
parts = re.split(r'(\\qt|\\subq|\\realq|\\stepq|\\conceptq|\\symq|\\formq|\\quickq|\\errq|\\warn)', content)

# recombine
questions = []
for i in range(1, len(parts), 2):
    cmd = parts[i]
    body = parts[i+1]
    # find the matching closing brace for the title if any, or just take first block
    # let's just keep it simple: cmd + body
    questions.append(cmd + body)

topics_kws = {
    "PM膨胀角": ["PM", "膨胀角", "Prandtl-Meyer"],
    "斜激波": ["斜激波", "楔角", "波角"],
    "离心泵吸水": ["吸水管", "安装高度", "汽蚀"],
    "水轮机": ["水轮机", "输出功率", "水功率"],
    "CV动量": ["弯管", "喷嘴", "法兰", "螺栓", "控制体"],
    "静水压": ["闸门", "曲面", "压力中心", "浮力"],
    "H-P层流": ["圆管层流", "Hagen-Poiseuille", "Poiseuille"],
    "壁律": ["壁律", "摩擦速度", "对数区"],
    "量纲分析": ["量纲", "Buckingham", "定理"],
    "应力张量": ["应力张量", "指定平面", "法向应力"]
}

with open('exact_topic_latex.txt', 'w', encoding='utf-8') as f_out:
    for topic, kws in topics_kws.items():
        f_out.write(f"=== TOPIC: {topic} ===\n")
        matches = []
        for q in questions:
            if any(kw in q for kw in kws):
                matches.append(q)
        # sort by length, get top 3
        matches.sort(key=len, reverse=True)
        for m in matches[:3]:
            f_out.write(m.strip() + "\n")
            f_out.write("-" * 50 + "\n")
        f_out.write("=" * 80 + "\n\n")

print("Finished extracting exact latex from version 21")
