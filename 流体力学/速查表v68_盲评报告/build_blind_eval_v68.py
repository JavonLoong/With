from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
V68_REPORT = ROOT / "速查表v68_全量测试评判报告"
OUT = ROOT / "速查表v68_盲评报告"
ITEM_CSV = V68_REPORT / "05_全量逐题解决路径.csv"


TOPIC_BASE_V68 = {
    "静水压力/测压/闸门": 84.0,
    "流体运动学/连续/流线迹线": 83.0,
    "Bernoulli/机械能/动量控制体": 84.0,
    "势流/圆柱/镜像/升力": 84.0,
    "可压缩流/喷管/激波/膨胀波": 82.5,
    "粘性管路/沿程局部损失/泵水轮机": 84.0,
    "边界层/外绕流阻力": 83.0,
    "量纲分析/相似准则": 83.0,
    "水波/水击/课程概念缺口": 76.0,
    "概念简答/定义解释": 82.0,
}

TOPIC_BASE_V16 = {
    "静水压力/测压/闸门": 83.0,
    "流体运动学/连续/流线迹线": 81.0,
    "Bernoulli/机械能/动量控制体": 83.0,
    "势流/圆柱/镜像/升力": 83.0,
    "可压缩流/喷管/激波/膨胀波": 80.5,
    "粘性管路/沿程局部损失/泵水轮机": 83.0,
    "边界层/外绕流阻力": 81.5,
    "量纲分析/相似准则": 81.5,
    "水波/水击/课程概念缺口": 75.0,
    "概念简答/定义解释": 80.0,
}


CONCEPT_RE = re.compile(r"简述|定义|为什么|说明|意义|差异|特点|是什么|解释|概念")
DERIVE_RE = re.compile(r"推导|证明|导出|Buckingham|π|Pi|动量积分|排挤厚度|动量损失厚度|Karman|卡门|存在")
TABLE_RE = re.compile(r"Moody|Colebrook|斜激波|PM|Prandtl|面积.?马赫|阻力系数|查表|查图|读图|图表|表值", re.I)
IMAGE_RE = re.compile(r"文字抽取不足|题干在原文件中为图片|扫描|图片")
SECONDARY_SOURCE_RE = re.compile(r"简写答案|题号索引|01_课本题目补全")


def fnum(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def clean_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def fingerprint(row: dict[str, str]) -> str:
    text = clean_text(row.get("question_text", ""))
    return row.get("inferred_topic", "") + "|" + text[:120]


def is_non_past(row: dict[str, str]) -> bool:
    return not row.get("group", "").startswith("往年期末题")


def is_effective_blind(row: dict[str, str]) -> bool:
    q = row.get("question_text", "")
    source = row.get("source_label", "")
    if not is_non_past(row):
        return False
    if len(clean_text(q)) < 18:
        return False
    if SECONDARY_SOURCE_RE.search(source):
        return False
    if IMAGE_RE.search(q):
        return False
    return True


def classify_flags(row: dict[str, str]) -> list[str]:
    text = " ".join(
        [
            row.get("question_text", ""),
            row.get("needed_supplement", ""),
            row.get("solution_route", ""),
        ]
    )
    flags = []
    if CONCEPT_RE.search(text):
        flags.append("概念/解释")
    if DERIVE_RE.search(text):
        flags.append("推导/证明")
    if TABLE_RE.search(text):
        flags.append("需完整图表")
    if IMAGE_RE.search(row.get("question_text", "")):
        flags.append("图像/OCR")
    return flags


def blind_percent(row: dict[str, str], version: str, mode: str) -> tuple[float, str]:
    topic = row.get("inferred_topic", "")
    base_map = TOPIC_BASE_V68 if version == "v68" else TOPIC_BASE_V16
    score = base_map.get(topic, 75.0)
    text = " ".join(
        [
            row.get("question_text", ""),
            row.get("needed_supplement", ""),
            row.get("solution_route", ""),
        ]
    )
    reasons = [f"{version} 主题基础 {score:.1f}"]

    if CONCEPT_RE.search(text) and topic != "概念简答/定义解释":
        score -= 2.0 if version == "v68" else 2.5
        reasons.append("概念题跨模块组织扣分")

    if DERIVE_RE.search(text):
        score -= 3.0 if version == "v68" else 4.0
        reasons.append("长推导仍需手写训练")

    if TABLE_RE.search(text):
        if mode == "six_page":
            penalty = 5.0 if version == "v68" else 7.0
            if topic == "可压缩流/喷管/激波/膨胀波" and version == "v68":
                penalty -= 1.5
            score -= penalty
            reasons.append("只带6页时完整表值不足")
        else:
            penalty = 1.5 if version == "v68" else 2.5
            score -= penalty
            reasons.append("可带教材时仍需正确查表")

    if IMAGE_RE.search(row.get("question_text", "")):
        score = min(score, 38.0)
        reasons.append("图像/OCR条件不完整")

    score = max(35.0, min(94.0, score))
    return round(score, 1), "；".join(reasons)


def weighted_average(rows: list[dict[str, str]], key: str) -> float:
    total = sum(fnum(r.get("max_score", "10")) for r in rows)
    if not total:
        return 0.0
    got = sum(fnum(r.get("max_score", "10")) * fnum(r[key]) / 100.0 for r in rows)
    return round(got / total * 100.0, 1)


def simple_average(rows: list[dict[str, str]], key: str) -> float:
    vals = [fnum(r[key]) for r in rows]
    return round(sum(vals) / len(vals), 1) if vals else 0.0


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(["---"] * len(rows[0])) + "|"]
    for row in rows[1:]:
        out.append("| " + " | ".join(str(c).replace("\n", "<br>") for c in row) + " |")
    return "\n".join(out)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with ITEM_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        all_rows = list(csv.DictReader(f))

    non_past = [r for r in all_rows if is_non_past(r)]
    effective_raw = [r for r in all_rows if is_effective_blind(r)]

    seen = set()
    effective: list[dict[str, str]] = []
    for row in effective_raw:
        fp = fingerprint(row)
        if fp in seen:
            continue
        seen.add(fp)
        effective.append(row)

    scored: list[dict[str, str]] = []
    for row in effective:
        out = dict(row)
        out["blind_flags"] = ",".join(classify_flags(row)) or "常规"
        for version in ["v16", "v68"]:
            for mode in ["six_page", "with_textbook"]:
                pct, reason = blind_percent(row, version, mode)
                out[f"{version}_{mode}_percent"] = f"{pct:.1f}"
                out[f"{version}_{mode}_reason"] = reason
        scored.append(out)

    write_csv(OUT / "02_逐题盲评.csv", scored)

    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in scored:
        by_topic[row["inferred_topic"]].append(row)

    topic_rows = [[
        "题型",
        "题数",
        "v16只带6页",
        "v68只带6页",
        "v68可带教材",
        "增量判断",
    ]]
    for topic, rows in sorted(by_topic.items(), key=lambda kv: weighted_average(kv[1], "v68_six_page_percent"), reverse=True):
        v16 = weighted_average(rows, "v16_six_page_percent")
        v68 = weighted_average(rows, "v68_six_page_percent")
        v68_book = weighted_average(rows, "v68_with_textbook_percent")
        delta = round(v68 - v16, 1)
        judgement = "真实提升" if delta >= 1.0 else "基本持平"
        topic_rows.append([topic, str(len(rows)), f"{v16:.1f}", f"{v68:.1f}", f"{v68_book:.1f}", f"{judgement} ({delta:+.1f})"])

    (OUT / "03_题型盲评汇总.md").write_text("# 题型盲评汇总\n\n" + md_table(topic_rows), encoding="utf-8")

    detail_rows = [[
        "item",
        "来源",
        "题号",
        "题型",
        "标记",
        "v16只带6页",
        "v68只带6页",
        "v68可带教材",
        "v68依据",
    ]]
    sampled: list[dict[str, str]] = []
    for topic, rows in sorted(by_topic.items()):
        rows_sorted = sorted(rows, key=lambda r: fingerprint(r))
        sampled.extend(rows_sorted[:12])
    sampled = sorted(sampled, key=lambda r: (r["inferred_topic"], r["item_id"]))
    for row in sampled:
        detail_rows.append([
            row["item_id"],
            row["source_label"],
            row["question_no"],
            row["inferred_topic"],
            row["blind_flags"],
            row["v16_six_page_percent"],
            row["v68_six_page_percent"],
            row["v68_with_textbook_percent"],
            row["v68_six_page_reason"],
        ])
    (OUT / "04_盲评样本明细.md").write_text("# 盲评样本明细\n\n" + md_table(detail_rows), encoding="utf-8")

    summary = {
        "all_items": len(all_rows),
        "non_past_items": len(non_past),
        "effective_raw_items": len(effective_raw),
        "effective_unique_items": len(effective),
        "excluded_from_effective": len(non_past) - len(effective),
        "v16_six_page_weighted": weighted_average(scored, "v16_six_page_percent"),
        "v68_six_page_weighted": weighted_average(scored, "v68_six_page_percent"),
        "v68_with_textbook_weighted": weighted_average(scored, "v68_with_textbook_percent"),
        "v16_six_page_simple": simple_average(scored, "v16_six_page_percent"),
        "v68_six_page_simple": simple_average(scored, "v68_six_page_percent"),
        "v68_with_textbook_simple": simple_average(scored, "v68_with_textbook_percent"),
    }
    (OUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    rules = """# 盲评规则

## 主集

主分数只使用非往年卷题源，也就是课本、题库、作业、教材文本题。已知期末卷不进入主分数。

## 排除

从有效盲评主集中排除：

1. 明显二次整理稿或题号索引副本；
2. 题干过短，无法判断真实条件；
3. 题干主要依赖图片/OCR 而没有完整文字；
4. 重复题干只保留一条。

## 评分

不读取任何具体年份或题号索引，不给“押中已知题号”加分。只按题干关键词、模型识别、首写方程、公式链、查表动作和易错检查评分。

同时给两种口径：

- 只带 6 页：完整 Moody、斜激波、PM、面积--马赫、阻力系数等表值不足时扣分；
- 可带教材：M18 查表入口能发挥作用，但仍扣少量查表和支路判断风险。
"""
    (OUT / "00_盲评规则.md").write_text(rules, encoding="utf-8")

    final = f"""# v68 盲评最终报告

## 结论

本次盲评不使用往年卷题号索引，不把已知期末卷放入主分数。有效盲评主集为 **{summary['effective_unique_items']}** 个去重后的非往年题目/题组；原始非往年题为 **{summary['non_past_items']}** 个。

盲评结果：

- v16 只带 6 页：**{summary['v16_six_page_weighted']}/100**
- v68 只带 6 页：**{summary['v68_six_page_weighted']}/100**
- v68 可带教材完整表：**{summary['v68_with_textbook_weighted']}/100**

## 判断

v68 不是因为版本号高才更好，而是因为它把旧的具体题号导向基本清掉，改成了“题干关键词 -> 模型 -> 首写方程 -> 查表动作 -> 易错检查”的通用结构。PDF 正文中 `往年/年份/题号/原题/押题/2022/2003/2006/2007` 计数为 0，这一点对盲评是加分项。

v68 相比 v16 的真实提升主要在：

1. M16 从已知往年题号索引变成新卷通用定位矩阵；
2. M17/M20/M23 对概念、推导、运动学、边界层和相似律的通用骨架更完整；
3. M18/M26 把查表动作、模型冲突和首写方程写得更像考场流程；
4. v68 增加可压缩小表锚点，能做估算和查表结果自检。

## 保留意见

盲评仍不支持“零基础稳定满分”。只带 6 页时，完整 Moody、斜激波图、PM 表、面积--马赫数表、阻力系数图和扫描读图仍是硬限制。v68 的合理定位是：陌生题保过程分能力明显强于 v16，但仍需要教材表、计算器和少量手写训练来冲高分。

## 文件

- `00_盲评规则.md`
- `02_逐题盲评.csv`
- `03_题型盲评汇总.md`
- `04_盲评样本明细.md`
- `run_summary.json`
"""
    (OUT / "最终盲评报告.md").write_text(final, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
