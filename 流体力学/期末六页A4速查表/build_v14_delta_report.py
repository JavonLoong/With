from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
BASE = ROOT / "速查表v10_全量测试评判报告" / "05_全量逐题解决路径.csv"
OUT = ROOT / "速查表v14_差异评估报告"


ADJUSTMENTS = {
    "流体运动学/连续/流线迹线": {
        "low_add": 8.0,
        "low_cap": 78.0,
        "normal_add": 2.0,
        "normal_cap": 82.0,
        "reason": "v14 M17 增加流线/迹线/脉线、随体加速度、连续/流函数/势函数证明入口。",
    },
    "边界层/外绕流阻力": {
        "low_add": 8.0,
        "low_cap": 80.0,
        "normal_add": 2.0,
        "normal_cap": 83.0,
        "reason": "v14 M17 增加边界层积分通链、有压梯度/分离、外绕流阻力面积选择。",
    },
    "概念简答/定义解释": {
        "low_add": 6.0,
        "low_cap": 76.0,
        "normal_add": 1.5,
        "normal_cap": 80.0,
        "reason": "v14 M17 增加概念长答三句结构；v12 M20 已补证明题骨架。",
    },
    "量纲分析/相似准则": {
        "low_add": 8.0,
        "low_cap": 82.0,
        "normal_add": 2.0,
        "normal_cap": 84.0,
        "reason": "v14 M17 增加 Re/Fr/Ma/We 换算、力/压强/流量比例和 Buckingham 易错项。",
    },
    "可压缩流/喷管/激波/膨胀波": {
        "low_add": 5.0,
        "low_cap": 78.0,
        "normal_add": 1.0,
        "normal_cap": 82.0,
        "reason": "v14 M17 增加面积-马赫小表和 PM 常用值；完整斜激波/PM/面积表仍靠教材。",
    },
    "Bernoulli/机械能/动量控制体": {
        "low_add": 4.0,
        "low_cap": 78.0,
        "normal_add": 1.0,
        "normal_cap": 86.0,
        "reason": "v13 M16 增加往年卷定位；v10/v14 已保留控制体收口，复杂方向仍需读图。",
    },
    "势流/圆柱/镜像/升力": {
        "low_add": 2.0,
        "low_cap": 80.0,
        "normal_add": 0.5,
        "normal_cap": 86.0,
        "reason": "v13 增加往年定位；势流主体早已较强，提升较小。",
    },
    "粘性管路/沿程局部损失/泵水轮机": {
        "low_add": 2.0,
        "low_cap": 78.0,
        "normal_add": 0.5,
        "normal_cap": 86.0,
        "reason": "v13 增加往年定位；管路主体早已较强，提升较小。",
    },
    "水波/水击/课程概念缺口": {
        "low_add": 4.0,
        "low_cap": 72.0,
        "normal_add": 0.0,
        "normal_cap": 72.0,
        "reason": "v12/M20 和 v14/M17 增加水击/水波入口，但完整推导仍不足。",
    },
}


def fnum(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def adjusted_percent(row: dict[str, str]) -> tuple[float, str]:
    topic = row.get("inferred_topic", "")
    old = fnum(row.get("normalized_percent", "0"))
    rule = ADJUSTMENTS.get(topic)
    if not rule:
        return old, "无 v14 定向调整。"
    if old < 70:
        new = min(old + rule["low_add"], rule["low_cap"])
    else:
        new = min(old + rule["normal_add"], rule["normal_cap"])
    return round(new, 1), rule["reason"]


def avg(rows: list[dict[str, str]], key: str) -> float:
    vals = [fnum(r[key]) for r in rows if r.get(key)]
    return round(sum(vals) / len(vals), 1) if vals else 0.0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with BASE.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    out_rows: list[dict[str, str]] = []
    for row in rows:
        new_percent, reason = adjusted_percent(row)
        max_score = fnum(row.get("max_score", "10"))
        old_percent = fnum(row.get("normalized_percent", "0"))
        new_score = round(max_score * new_percent / 100, 2)
        new_row = dict(row)
        new_row["v10_percent"] = f"{old_percent:.1f}"
        new_row["v14_adjusted_percent"] = f"{new_percent:.1f}"
        new_row["v14_estimated_score"] = f"{new_score:.2f}"
        new_row["v14_adjustment_reason"] = reason
        out_rows.append(new_row)

    csv_path = OUT / "05_全量逐题解决路径_v14差异估计.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in out_rows:
        by_topic[row["inferred_topic"]].append(row)

    topic_rows = []
    for topic, group in by_topic.items():
        topic_rows.append(
            {
                "topic": topic,
                "count": len(group),
                "v10_avg": avg(group, "v10_percent"),
                "v14_avg": avg(group, "v14_adjusted_percent"),
                "low_before": sum(1 for r in group if fnum(r["v10_percent"]) < 70),
                "low_after": sum(1 for r in group if fnum(r["v14_adjusted_percent"]) < 70),
            }
        )
    topic_rows.sort(key=lambda r: (r["v14_avg"], -r["count"]))

    readable_past = [r for r in out_rows if r["group"].startswith("往年")]
    textbook = [r for r in out_rows if not r["group"].startswith("往年")]

    summary = {
        "item_count": len(out_rows),
        "v10_all_avg": avg(out_rows, "v10_percent"),
        "v14_all_avg": avg(out_rows, "v14_adjusted_percent"),
        "v10_past_avg": avg(readable_past, "v10_percent"),
        "v14_past_avg": avg(readable_past, "v14_adjusted_percent"),
        "v10_textbook_avg": avg(textbook, "v10_percent"),
        "v14_textbook_avg": avg(textbook, "v14_adjusted_percent"),
        "low_before": sum(1 for r in out_rows if fnum(r["v10_percent"]) < 70),
        "low_after": sum(1 for r in out_rows if fnum(r["v14_adjusted_percent"]) < 70),
    }
    (OUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    topic_md = ["# v14 差异评估：题型汇总", ""]
    topic_md.append("| 题型 | 题数 | v10均值 | v14差异估计 | 低于70%: v10→v14 |")
    topic_md.append("|---|---:|---:|---:|---:|")
    for r in topic_rows:
        topic_md.append(
            f"| {r['topic']} | {r['count']} | {r['v10_avg']} | {r['v14_avg']} | {r['low_before']}→{r['low_after']} |"
        )
    (OUT / "01_题型汇总.md").write_text("\n".join(topic_md), encoding="utf-8")

    low_after = [r for r in out_rows if fnum(r["v14_adjusted_percent"]) < 70]
    low_after.sort(key=lambda r: (fnum(r["v14_adjusted_percent"]), r["inferred_topic"]))
    low_md = ["# v14 后仍低于 70% 的项目", ""]
    low_md.append("| item | 来源 | 题号 | 题型 | v10 | v14估计 | 仍需补充 |")
    low_md.append("|---|---|---|---|---:|---:|---|")
    for r in low_after[:120]:
        low_md.append(
            f"| {r['item_id']} | {r['source_label']} | {r['question_no']} | {r['inferred_topic']} | {r['v10_percent']} | {r['v14_adjusted_percent']} | {r['needed_supplement']} |"
        )
    (OUT / "02_v14后仍低分项.md").write_text("\n".join(low_md), encoding="utf-8")

    final = [
        "# 速查表 v14 差异评估报告",
        "",
        "## 结论",
        "",
        "这是基于 v10 全量逐题路径的差异估计，不是重新 OCR 所有扫描题，也不是满分证明。调整只应用于 v12--v14 明确新增覆盖的模块。",
        "",
        f"- 全部 {summary['item_count']} 项：v10 平均 {summary['v10_all_avg']}/100，v14 差异估计 {summary['v14_all_avg']}/100。",
        f"- 可读往年题：v10 平均 {summary['v10_past_avg']}/100，v14 差异估计 {summary['v14_past_avg']}/100。",
        f"- 课本/作业题：v10 平均 {summary['v10_textbook_avg']}/100，v14 差异估计 {summary['v14_textbook_avg']}/100。",
        f"- 低于 70% 的项目：v10 有 {summary['low_before']} 项，v14 差异估计仍有 {summary['low_after']} 项。",
        "",
        "## 本轮有效提升",
        "",
        "- M16 往年题号索引主要改善定位速度，不直接提高公式覆盖上限。",
        "- M17 低分题补丁主要改善运动学、边界层、概念长答、相似律和可压小表。",
        "- M20 证明骨架继续支撑长推导题。",
        "",
        "## 仍不能证明满分的原因",
        "",
        "1. 扫描题和图片题仍存在 OCR/读图瓶颈。",
        "2. 完整 Moody、斜激波、PM、面积--马赫数、阻力系数图仍需要教材。",
        "3. 长推导题即使有骨架，也需要考生能把题目边界条件接上。",
        "",
        "## 生成文件",
        "",
        "- `01_题型汇总.md`",
        "- `02_v14后仍低分项.md`",
        "- `05_全量逐题解决路径_v14差异估计.csv`",
        "- `run_summary.json`",
    ]
    (OUT / "最终报告.md").write_text("\n".join(final), encoding="utf-8")


if __name__ == "__main__":
    main()

