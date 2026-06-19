from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
V14_CSV = ROOT / "速查表v14_差异评估报告" / "05_全量逐题解决路径_v14差异估计.csv"
OUT_DIR = ROOT / "速查表v14_剩余低分项审计"


def pct(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0)
    except ValueError:
        return 0.0


def classify(row: dict[str, str]) -> tuple[str, str, str]:
    label = row.get("source_label", "")
    source_file = row.get("source_file", "")
    text = row.get("question_text", "")
    topic = row.get("inferred_topic", "")
    need = row.get("needed_supplement", "")
    qno = row.get("question_no", "")

    generated_partial = (
        "题干在原文件中为图片或标题索引" in text
        or "简写答案" in label
        or "更简写答案" in label
        or label == "01_课本题目补全.md"
    )
    if generated_partial:
        if "第七章作业3" in label:
            return (
                "假低分：二次整理稿/题干不完整",
                "不建议继续占用六页空间；7.19/7.20/7.21 已在 P4/T4/Q7/M17 有专门流程。若要提高评测，应改用课本原题截图或完整转写。",
                "可压第7章作业3的简写答案被当成题源，题干信息不足，分数偏低不等于速查表缺公式。",
            )
        if label == "01_课本题目补全.md" and qno in {"4", "7"}:
            return (
                "假低分：题号索引未补原题",
                "不改六页内容；完整题目/答案已另见 07_书10.2_平板层流边界层.md、10_书10.10_火车摩擦阻力功率.md 和 13_粘性流动作业-2_题目与答案.tex。",
                "当前低分来自题号索引副本，不是完整题；完整题源在同一作业文件夹中已经存在。",
            )
        return (
            "假低分：题干/OCR不足",
            "优先补全原题文字或截图；不应直接把这个分数视作知识缺口。",
            "题干不可读或来自二次整理文件。",
        )

    if any(key in need for key in ["完整表", "查表", "Moody", "斜激波", "PM", "面积-马赫", "面积--马赫", "阻力系数图"]):
        return (
            "真限制：完整图表/查表",
            "六页表保留“查什么、怎么接公式”；完整数值仍查允许携带的教材。若强塞全表，会牺牲更多通用题。",
            "这是资料物理限制，不是单个公式缺失。",
        )

    if any(key in need for key in ["长篇推导", "复杂坐标", "边界条件"]):
        return (
            "真限制：长推导/边界条件衔接",
            "v14 已给骨架；想拿满分需要考前按2-3题手写训练，把题目边界条件接到骨架上。",
            "这类题靠速查表只能保结构分，不能替代推导熟练度。",
        )

    if "量纲" in topic or "相似" in topic:
        return (
            "真限制：相似律冷门变量",
            "保留Buckingham和常用准则；非常规变量按教材定义补充。",
            "题目变量组合冷门时，六页表只能给流程。",
        )

    if "粘性管路" in topic:
        return (
            "真限制：物性/局部损失系数",
            "题给系数直接代；未给时查教材表。v14 已保留管路能量方程和Moody使用方法。",
            "不是公式缺口，主要是参数来源限制。",
        )

    return (
        "待人工复核",
        "需要回看原题，判断是公式缺口还是读题/表格限制。",
        "分类规则未命中。",
    )


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    out = ["| " + " | ".join(rows[0]) + " |"]
    out.append("|" + "|".join(["---"] * len(rows[0])) + "|")
    for row in rows[1:]:
        out.append("| " + " | ".join(cell.replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with V14_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    lows = [r for r in rows if pct(r, "v14_adjusted_percent") < 70]
    for r in lows:
        c, action, reason = classify(r)
        r["audit_class"] = c
        r["audit_action"] = action
        r["audit_reason"] = reason

    counts = Counter(r["audit_class"] for r in lows)
    topic_counts = Counter(r.get("inferred_topic", "") for r in lows)
    class_by_topic: dict[str, Counter[str]] = defaultdict(Counter)
    for r in lows:
        class_by_topic[r.get("inferred_topic", "")][r["audit_class"]] += 1

    out_csv = OUT_DIR / "01_v14剩余低分项_审计明细.csv"
    fieldnames = [
        "item_id",
        "source_label",
        "question_no",
        "inferred_topic",
        "v10_percent",
        "v14_adjusted_percent",
        "audit_class",
        "audit_action",
        "audit_reason",
        "needed_supplement",
        "question_text",
        "source_file",
    ]
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(lows)

    summary_rows = [["类别", "数量", "处理结论"]]
    class_action = {
        "假低分：二次整理稿/题干不完整": "不改六页内容；应换完整原题再评。",
        "假低分：题号索引未补原题": "先补原题；不能据此扣速查表。",
        "假低分：题干/OCR不足": "先做OCR/截图转写。",
        "真限制：完整图表/查表": "靠教材完整表；六页只放入口和接公式。",
        "真限制：长推导/边界条件衔接": "速查表给骨架，需手写训练。",
        "真限制：相似律冷门变量": "保流程，冷门变量查教材。",
        "真限制：物性/局部损失系数": "参数查教材或题给。",
        "待人工复核": "回看原题。",
    }
    for cls, n in counts.most_common():
        summary_rows.append([cls, str(n), class_action.get(cls, "")])

    detail_rows = [[
        "item",
        "来源",
        "题号",
        "题型",
        "v14",
        "审计分类",
        "建议动作",
    ]]
    for r in sorted(lows, key=lambda x: (x["audit_class"], pct(x, "v14_adjusted_percent"), x.get("item_id", ""))):
        detail_rows.append([
            r.get("item_id", ""),
            r.get("source_label", ""),
            r.get("question_no", ""),
            r.get("inferred_topic", ""),
            f'{pct(r, "v14_adjusted_percent"):.1f}',
            r["audit_class"],
            r["audit_action"],
        ])

    topic_rows = [["题型", "低分数", "主要原因"]]
    for topic, n in topic_counts.most_common():
        common_class = class_by_topic[topic].most_common(1)[0][0]
        topic_rows.append([topic, str(n), common_class])

    report = f"""# v14 剩余低分项审计报告

## 结论

v14 差异评估中低于 70% 的项目共有 **{len(lows)}** 项。审计后看，低分并不等价于“六页速查表缺了 25 个知识点”：

- 相当一部分来自二次整理稿、题号索引或题干不完整文件，属于评测样本问题。
- 真正不能靠六页纸完全解决的部分，主要是完整图表查值、扫描读图、长推导边界条件衔接。
- 继续盲目往六页里塞内容，收益很低；下一步如果要提升分数，应优先补全原题/OCR和做专题手写训练，而不是单纯改排版。

## 分类统计

{md_table(summary_rows)}

## 按题型看低分来源

{md_table(topic_rows)}

## 逐项审计

{md_table(detail_rows)}

## 对 v15 的判断

暂不建议仅因为这 25 项继续生成 v15。当前 v14 已经把能压缩进六页的通用流程和公式放入；剩余收益主要来自：

1. 把 `第七章作业3_简写答案.md`、`01_课本题目补全.md` 这类二次整理题源替换成完整原题截图/OCR。
2. 对斜激波、PM、面积--马赫、Moody、阻力系数图，使用教材完整表；六页纸只保留查表入口和查后公式。
3. 对运动学、相似律、边界层积分、概念证明题，按 v14 的骨架手写 2--3 遍，否则零基础考场临时翻表仍不稳。

明细 CSV：`01_v14剩余低分项_审计明细.csv`
"""
    (OUT_DIR / "00_v14剩余低分项审计报告.md").write_text(report, encoding="utf-8")

    print(f"wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
