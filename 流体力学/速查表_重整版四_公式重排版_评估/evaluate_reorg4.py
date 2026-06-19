from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

TARGET = ROOT / "期末六页A4速查表" / "新建文件夹" / "期末六页A4速查表_重整版四_公式重排版.pdf"
V80_CSV = ROOT / "速查表v80_全量测试评判报告" / "05_全量逐题解决路径.csv"


def extract_pdf_text(pdf: Path) -> tuple[list[str], str]:
    doc = fitz.open(pdf)
    pages = [page.get_text() for page in doc]
    return pages, "\n".join(pages)


def topic_score(topic: str) -> tuple[float, str]:
    if "粘性管路" in topic or "泵水轮机" in topic:
        return 8.6, "管路/泵/水轮机母题在第1页和第4页反复覆盖，公式链和代表题强。"
    if "可压缩" in topic or "喷管" in topic or "激波" in topic:
        return 8.2, "等熵/Laval/正激波/斜激波/PM 覆盖厚，但仍依赖完整表。"
    if "势流" in topic or "圆柱" in topic or "镜像" in topic:
        return 8.4, "势流基本流、圆柱、镜像、环量和证明链较完整。"
    if "边界层" in topic or "外绕" in topic:
        return 8.0, "平板、位移/动量厚度、动量积分和阻力公式较完整。"
    if "流体运动学" in topic or "连续" in topic or "流线" in topic:
        return 7.0, "第6页有场变量、散度旋度、流线迹线，但入口靠后且例题少。"
    if "Bernoulli" in topic or "机械能" in topic or "动量控制体" in topic:
        return 7.2, "机械能很强，但一般控制体动量、动量矩、弯管受力的独立模板偏弱。"
    if "量纲" in topic or "相似" in topic:
        return 6.4, "有 Buckingham/无量纲/相似词条，但不是独立完整页，模型律和流程不够醒目。"
    if "静水" in topic or "测压" in topic or "闸门" in topic:
        return 5.6, "有静水压词条和零散补丁，但平面/曲面闸门、压力中心、压力体不够成体系。"
    if "水波" in topic or "水击" in topic or "明渠" in topic:
        return 5.2, "只点到水击/深水波/明渠，缺少完整解题链。"
    if "概念" in topic or "定义" in topic:
        return 6.2, "公式和母题很多，但概念短答库、定义比较题、适用条件的可检索性较弱。"
    return 6.5, "未明确命中主母题，按中低覆盖估计。"


def load_topic_weights(csv_path: Path) -> dict[str, dict[str, float]]:
    weights: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "max_score": 0.0})
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            topic = row["inferred_topic"]
            weights[topic]["count"] += 1
            weights[topic]["max_score"] += float(row["max_score"])
    return dict(weights)


def term_counts(text: str) -> dict[str, int]:
    terms = [
        "母题",
        "公式链",
        "步骤",
        "子题",
        "真题",
        "原题",
        "作业代表题",
        "静水",
        "闸门",
        "压力中心",
        "控制体",
        "动量矩",
        "势流",
        "Laval",
        "激波",
        "膨胀波",
        "Moody",
        "Colebrook",
        "汽蚀",
        "虹吸",
        "并联",
        "水轮机",
        "N-S",
        "H-P",
        "Couette",
        "Stokes",
        "边界层",
        "量纲",
        "Buckingham",
        "相似",
        "水击",
        "深水波",
        "明渠",
        "堰",
    ]
    return {term: text.count(term) for term in terms}


def main() -> None:
    pages, text = extract_pdf_text(TARGET)
    counts = term_counts(text)
    weights = load_topic_weights(V80_CSV)

    topic_rows = []
    total_weight = 0.0
    weighted_score = 0.0
    for topic, data in sorted(weights.items(), key=lambda kv: -kv[1]["max_score"]):
        score, reason = topic_score(topic)
        w = data["max_score"]
        total_weight += w
        weighted_score += score * w
        topic_rows.append((topic, int(data["count"]), w, score, reason))

    overall = weighted_score / total_weight if total_weight else 0.0

    page_summaries = []
    for i, page in enumerate(pages, 1):
        head = page[:900].replace("\n", " ")
        page_summaries.append((i, len(page), head))

    report = []
    report.append("# 重整版四_公式重排版 评估报告")
    report.append("")
    report.append(f"- 目标文件：`{TARGET}`")
    report.append(f"- 页数：{len(pages)}")
    report.append(f"- 抽取字符数：{sum(len(p) for p in pages)}")
    report.append(f"- 估算综合覆盖：{overall:.1f}/10，折算约 {overall * 10:.0f}/100")
    report.append("")
    report.append("## 结论")
    report.append("")
    report.append("这是一个“母题公式链压缩版”，不是“考场题干定位版”。它把管路、势流、可压缩流、粘性管流、边界层做得很厚，适合已经知道题型后快速套公式；但对完全陌生题目的第一步定位、静水压闸门、概念短答、水击水波、动量矩和广义控制体题支撑不足。")
    report.append("")
    report.append("与 v80 这类导航型版本相比，它的优势是单母题公式密度高，劣势是翻找成本高、可迁移的题干索引弱，并且含有较多“真题/原题/作业代表题”痕迹，存在为了覆盖已见题而挤压通用概念入口的风险。")
    report.append("")
    report.append("## 页结构")
    report.append("")
    for i, chars, head in page_summaries:
        report.append(f"- 第 {i} 页，约 {chars} 字：{head}")
    report.append("")
    report.append("## 关键词计数")
    report.append("")
    report.append("| 关键词 | 次数 |")
    report.append("| --- | ---: |")
    for term, count in counts.items():
        report.append(f"| {term} | {count} |")
    report.append("")
    report.append("## 按题型估算")
    report.append("")
    report.append("| 题型 | 题数 | 权重分 | 估计覆盖/10 | 判断 |")
    report.append("| --- | ---: | ---: | ---: | --- |")
    for topic, n, w, score, reason in topic_rows:
        report.append(f"| {topic} | {n} | {w:.1f} | {score:.1f} | {reason} |")
    report.append("")
    report.append("## 强项")
    report.append("")
    report.append("1. 管路机械能综合很强：PVZ 加损失、突扩、沿程/局部、泵吸水、水轮机、串并联、孔板/文丘里都有。")
    report.append("2. 可压缩流很强：Laval、阻塞、正激波、斜激波、PM 膨胀、背压八状态都有。")
    report.append("3. 势流页完整度高：基本流、圆柱、镜像、环量、Rankine 体、边角流和证明链都有。")
    report.append("4. 粘性管流和边界层公式链密度高：N-S 简化、H-P、Couette、两层流体、Stokes、Blasius、动量积分都覆盖。")
    report.append("")
    report.append("## 主要问题")
    report.append("")
    report.append("1. 不适合零基础快速定位：没有类似 v80 的“题干词 -> 模型 -> 页码”总入口。")
    report.append("2. 静水压和闸门不足：有词条但不成体系，平面/曲面压力、压力中心、压力体、浮力稳定不够醒目。")
    report.append("3. 控制体动量偏弱：一般弯管/喷嘴/射流受力、动量矩、角动量不是独立强入口。")
    report.append("4. 概念简答弱：定义、比较、适用条件、物理意义的短答库不足。")
    report.append("5. 水击/水波/明渠很薄：只点到，不足以支撑完整题。")
    report.append("6. 含较多真题/原题/作业代表题痕迹：利于已见题得分，但会占用通用能力空间。")
    report.append("")
    report.append("## 建议")
    report.append("")
    report.append("如果要继续用这个版式，建议不要再往里面塞新公式。优先加一个极短目录层：按题干词、要求量、图形特征反查母题。若必须在 6 页内调整，建议从重复的“子题真题/原题”中删 10%-15%，换成静水压闸门、控制体动量、概念短答、水击水波的通用模板。")

    (OUT / "评估报告.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
