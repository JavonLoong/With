from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
BASE = ROOT / "速查表v14_差异评估报告" / "05_全量逐题解决路径_v14差异估计.csv"
AUDIT = ROOT / "速查表v14_剩余低分项审计" / "01_v14剩余低分项_审计明细.csv"
OUT = ROOT / "速查表v16_差异评估报告"


def fnum(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def avg(rows: list[dict[str, str]], key: str) -> float:
    vals = [fnum(r.get(key, "")) for r in rows if r.get(key, "")]
    return round(sum(vals) / len(vals), 1) if vals else 0.0


def classify_nonlow(row: dict[str, str]) -> str:
    need = row.get("needed_supplement", "")
    if any(k in need for k in ["完整表", "查表", "Moody", "斜激波", "PM", "面积-马赫", "面积--马赫", "阻力系数图"]):
        return "真限制：完整图表/查表"
    return ""


def v16_adjust(row: dict[str, str], audit_class: str) -> tuple[float, str, str]:
    old = fnum(row.get("v14_adjusted_percent", row.get("normalized_percent", "0")))
    topic = row.get("inferred_topic", "")

    if audit_class.startswith("假低分"):
        # 不把题源/OCR/索引副本当作速查表缺口；分数不硬抬，只在有效均值里排除。
        return old, "v16 未调分：题源或二次整理稿问题，纳入另表审计，不代表速查表公式缺失。", "excluded_effective"

    if audit_class == "真限制：完整图表/查表" or classify_nonlow(row) == "真限制：完整图表/查表":
        if topic in {"可压缩流/喷管/激波/膨胀波", "粘性管路/沿程局部损失/泵水轮机", "边界层/外绕流阻力"}:
            # v16 M18 增加查表入口和查后公式，提升定位/过程分，但完整数值仍靠教材，不能过高。
            return min(old + 2.0, 74.0), "v16 M18 增加教材查表入口和查后接公式；完整数值表仍需教材。", "improved_lookup"
        return min(old + 1.0, 72.0), "v16 M18 改善查表定位；完整图表仍需教材。", "improved_lookup"

    if audit_class == "真限制：长推导/边界条件衔接":
        return old, "v16 未显著新增长推导；仍靠 M20/M24/M25 骨架和考前手写训练。", "unchanged_derivation"

    if audit_class == "真限制：相似律冷门变量":
        return min(old + 1.0, 70.0), "v16 没有新增冷门变量表；M25 流程可保基本过程分。", "minor_similarity"

    return old, "无 v16 定向调整。", "unchanged"


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(["---"] * len(rows[0])) + "|"]
    for row in rows[1:]:
        out.append("| " + " | ".join(c.replace("\n", "<br>") for c in row) + " |")
    return "\n".join(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    with BASE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    audit_by_id: dict[str, dict[str, str]] = {}
    if AUDIT.exists():
        with AUDIT.open("r", encoding="utf-8-sig", newline="") as f:
            audit_by_id = {r["item_id"]: r for r in csv.DictReader(f)}

    out_rows: list[dict[str, str]] = []
    for row in rows:
        audit = audit_by_id.get(row["item_id"], {})
        audit_class = audit.get("audit_class", "")
        new_percent, reason, effect_class = v16_adjust(row, audit_class)
        max_score = fnum(row.get("max_score", "10"))
        new = dict(row)
        new["v16_adjusted_percent"] = f"{new_percent:.1f}"
        new["v16_estimated_score"] = f"{max_score * new_percent / 100:.2f}"
        new["v16_adjustment_reason"] = reason
        new["v16_effect_class"] = effect_class
        new["audit_class"] = audit_class
        new["audit_action"] = audit.get("audit_action", "")
        out_rows.append(new)

    csv_path = OUT / "05_全量逐题解决路径_v16差异估计.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    effective = [r for r in out_rows if r["v16_effect_class"] != "excluded_effective"]
    past = [r for r in out_rows if r["group"].startswith("往年")]
    past_effective = [r for r in effective if r["group"].startswith("往年")]
    textbook_effective = [r for r in effective if not r["group"].startswith("往年")]

    summary = {
        "item_count": len(out_rows),
        "effective_item_count": len(effective),
        "excluded_false_low_count": len(out_rows) - len(effective),
        "v14_all_avg": avg(out_rows, "v14_adjusted_percent"),
        "v16_all_avg": avg(out_rows, "v16_adjusted_percent"),
        "v14_effective_avg": avg(effective, "v14_adjusted_percent"),
        "v16_effective_avg": avg(effective, "v16_adjusted_percent"),
        "v14_past_avg": avg(past, "v14_adjusted_percent"),
        "v16_past_avg": avg(past, "v16_adjusted_percent"),
        "v16_past_effective_avg": avg(past_effective, "v16_adjusted_percent"),
        "v16_textbook_effective_avg": avg(textbook_effective, "v16_adjusted_percent"),
        "low_v14": sum(1 for r in out_rows if fnum(r["v14_adjusted_percent"]) < 70),
        "low_v16": sum(1 for r in out_rows if fnum(r["v16_adjusted_percent"]) < 70),
        "low_v16_effective": sum(1 for r in effective if fnum(r["v16_adjusted_percent"]) < 70),
    }
    (OUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    topic_rows = [["题型", "题数", "v14均值", "v16均值", "v16低于70"]]
    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in effective:
        by_topic[row["inferred_topic"]].append(row)
    for topic, group in sorted(by_topic.items(), key=lambda kv: avg(kv[1], "v16_adjusted_percent")):
        topic_rows.append([
            topic,
            str(len(group)),
            f'{avg(group, "v14_adjusted_percent"):.1f}',
            f'{avg(group, "v16_adjusted_percent"):.1f}',
            str(sum(1 for r in group if fnum(r["v16_adjusted_percent"]) < 70)),
        ])
    (OUT / "01_题型汇总.md").write_text("# v16 差异评估：题型汇总\n\n" + md_table(topic_rows), encoding="utf-8")

    effect_counts = Counter(r["v16_effect_class"] for r in out_rows)
    effect_rows = [["v16处理类别", "数量", "含义"]]
    meanings = {
        "excluded_effective": "题源/OCR/二次整理稿造成假低分；不计入有效均值。",
        "improved_lookup": "v16 M18 新增查表入口和查后公式，提升定位和过程分。",
        "unchanged_derivation": "长推导仍需手写训练，六页只给骨架。",
        "minor_similarity": "相似律冷门变量小幅改善，仍需教材定义。",
        "unchanged": "无定向调整。",
    }
    for cls, n in effect_counts.most_common():
        effect_rows.append([cls, str(n), meanings.get(cls, "")])
    (OUT / "02_v16处理分类.md").write_text("# v16 处理分类\n\n" + md_table(effect_rows), encoding="utf-8")

    low_rows = [r for r in out_rows if fnum(r["v16_adjusted_percent"]) < 70]
    low_rows.sort(key=lambda r: (r["v16_effect_class"], fnum(r["v16_adjusted_percent"]), r["item_id"]))
    low_table = [["item", "来源", "题号", "题型", "v16", "处理", "仍需动作"]]
    for r in low_rows[:120]:
        low_table.append([
            r["item_id"],
            r["source_label"],
            r["question_no"],
            r["inferred_topic"],
            r["v16_adjusted_percent"],
            r["v16_effect_class"],
            r.get("audit_action") or r.get("needed_supplement", ""),
        ])
    (OUT / "03_v16后仍低分项.md").write_text("# v16 后仍低于70%的项目\n\n" + md_table(low_table), encoding="utf-8")

    final = f"""# 速查表 v16 差异评估报告

## 结论

v16 的目标不是继续堆公式，而是修正 v15 里的 M18 导航残留，并把“允许带教材”转化为查表和原题定位能力。

- 全量 {summary['item_count']} 项：v14 差异估计 {summary['v14_all_avg']}/100，v16 差异估计 {summary['v16_all_avg']}/100。
- 排除题源/OCR/二次整理稿假低分后，有效 {summary['effective_item_count']} 项：v14 {summary['v14_effective_avg']}/100，v16 {summary['v16_effective_avg']}/100。
- 往年题：v14 {summary['v14_past_avg']}/100，v16 {summary['v16_past_avg']}/100。
- v16 后低于70%的项目：全量 {summary['low_v16']} 项；排除假低分后 {summary['low_v16_effective']} 项。

## 关键判断

1. v16 没有证明“零基础满分”；这个目标仍不能被当前证据证明。
2. v16 比 v15 更适合考场：概念题入口回到 M20/M23，M18 专门负责查教材表和原题定位。
3. 剩余真限制主要是完整图表查值、长推导边界条件、冷门相似变量；这些无法只靠六页纸完全消除。

## 生成文件

- `01_题型汇总.md`
- `02_v16处理分类.md`
- `03_v16后仍低分项.md`
- `05_全量逐题解决路径_v16差异估计.csv`
- `run_summary.json`
"""
    (OUT / "最终报告.md").write_text(final, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
