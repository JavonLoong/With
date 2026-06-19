import re

with open(r'filtered_matches.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's write a script that outputs sections containing specific keywords
keywords_map = {
    "PM膨胀角": ["PM", "膨胀", "Prandtl", "PM角"],
    "斜激波": ["斜激波", "楔角", "波角", "beta"],
    "离心泵吸水高度": ["吸水管", "汽蚀", "安装高度", "离心泵"],
    "水轮机": ["水轮机", "输出功率", "取能"],
    "CV动量": ["螺栓", "法兰", "弯管", "动量"],
    "静水压": ["闸门", "曲面", "平面", "浮力"],
    "HP层流": ["H-P", "圆管层流", "Poiseuille"],
    "壁律": ["壁律", "近壁", "摩擦速度"],
    "量纲分析": ["量纲", "Buckingham", "定理"],
    "应力张量": ["张量", "指定平面", "应力矢量"]
}

with open('extracted_from_filtered.txt', 'w', encoding='utf-8') as f_out:
    for topic, kws in keywords_map.items():
        f_out.write(f"=== TOPIC: {topic} ===\n")
        # Find paragraphs in text
        paras = text.split("\n\n")
        found = 0
        for para in paras:
            if any(kw in para for kw in kws):
                f_out.write(para + "\n")
                f_out.write("-" * 40 + "\n")
                found += 1
                if found >= 3:
                    break
        f_out.write("=" * 80 + "\n\n")

print("Finished extracting matching paragraphs")
