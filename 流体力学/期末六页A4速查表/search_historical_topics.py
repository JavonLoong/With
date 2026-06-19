import os
import re

dir_path = r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一'
tex_files = [f for f in os.listdir(dir_path) if f.endswith('.tex')]

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

with open('topic_search_results.txt', 'w', encoding='utf-8') as f_out:
    for topic, kws in topics_kws.items():
        f_out.write(f"=== TOPIC: {topic} ===\n")
        matches_found = []
        for tf in tex_files:
            fp = os.path.join(dir_path, tf)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # find paragraphs
            paras = content.split('\n\n')
            for p_idx, para in enumerate(paras):
                if any(kw in para for kw in kws):
                    # check if this looks like a complete question with \qt or \realq or \subq
                    if any(cmd in para for cmd in [r'\qt', r'\realq', r'\subq', r'\realq{', r'\subq{']):
                        matches_found.append((tf, p_idx, para))
        # Sort or select the longest/most complete ones
        matches_found.sort(key=lambda x: len(x[2]), reverse=True)
        for tf, p_idx, para in matches_found[:3]:
            f_out.write(f"File: {tf}, Para: {p_idx}\n{para}\n")
            f_out.write("-" * 50 + "\n")
        f_out.write("=" * 80 + "\n\n")

print("Finished searching topics in historical tex files")
