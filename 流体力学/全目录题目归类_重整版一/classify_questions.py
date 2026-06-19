from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "流体力学"
INDEX = ROOT / "期末练习题_按题型整理" / "全量题目索引.csv"
OUT = ROOT / "全目录题目归类_重整版一"
OUT.mkdir(parents=True, exist_ok=True)


FOLDER_DEFAULT = {
    "01_静水压力_测压_闸门": ("第2章 流体静力学", "母题1：静水压强/测压/闸门受力", "静水压强与平面/曲面受力"),
    "02_Bernoulli_机械能_动量控制体": ("第4章 动力学基础", "母题2：Bernoulli/PVZ/控制体动量", "能量方程与动量方程"),
    "03_流体运动学_连续_应力张量": ("第3章 运动学与应力", "母题3：运动学/连续/应力张量", "速度场、加速度、应力向量"),
    "04_势流_无旋_圆柱_镜像_升力": ("第5/6章 理想不可压无旋流动", "母题4：势流叠加/圆柱绕流/镜像/升力", "势函数流函数与叠加"),
    "05_可压缩流_喷管_激波_膨胀波": ("第7章 可压缩流", "母题5：可压缩流/Laval喷管/激波/膨胀波", "等熵流、喷管、激波"),
    "06_粘性管路_沿程局部损失_泵水轮机": ("第8/10章 粘性管流与工程损失", "母题6：粘性管路/沿程局部损失/泵水轮机", "管路能量损失"),
    "07_边界层_外绕流阻力": ("第8/9章 边界层与外绕流", "母题7：边界层/外绕流阻力", "平板边界层与阻力"),
    "08_量纲分析_相似准则": ("相似理论", "母题8：量纲分析/模型相似", "Pi定理与相似准则"),
    "09_水波_水击_明渠": ("水波/水击/明渠", "母题9：水波/水击/明渠", "自由液面与非定常波动"),
    "10_概念简答_综合证明": ("概念综合", "母题10：概念辨析/证明/综合判断", "概念简答与证明"),
}


RULES = [
    {
        "chapter": "第7章 可压缩流",
        "mother": "母题5：可压缩流/Laval喷管/激波/膨胀波",
        "child": "Laval喷管背压-阻塞-正激波位置判定",
        "keywords": ["Laval", "喷管", "喉部", "背压", "下游", "汞柱", "水银", "面积比", "A_t", "A_e", "正激波"],
    },
    {
        "chapter": "第7章 可压缩流",
        "mother": "母题5：可压缩流/Laval喷管/激波/膨胀波",
        "child": "正激波/斜激波/膨胀波查表计算",
        "keywords": ["正激波", "斜激波", "膨胀波", "Prandtl", "Meyer", "激波角", "偏转角", "马赫波", "脱体激波"],
    },
    {
        "chapter": "第8/10章 粘性管流与工程损失",
        "mother": "母题6：粘性管路/沿程局部损失/泵水轮机",
        "child": "水池-管路-泵阀-局部损失综合",
        "keywords": ["水池", "油箱", "管路", "水泵", "泵", "水轮机", "阀", "局部损失", "沿程", "粗糙度", "Moody", "突扩", "突缩", "安装高度", "输出功率"],
    },
    {
        "chapter": "第8/10章 粘性管流与工程损失",
        "mother": "母题6：粘性管路/沿程局部损失/泵水轮机",
        "child": "层流管流/Hagen-Poiseuille/剪应力",
        "keywords": ["层流", "管内", "H-P", "Poiseuille", "压降", "剪应力", "壁面切应力", "圆管", "速度分布"],
    },
    {
        "chapter": "第8/10章 粘性管流与工程损失",
        "mother": "母题6：粘性管路/沿程局部损失/泵水轮机",
        "child": "Couette/多层粘性剪切流",
        "keywords": ["Couette", "平板间", "上下平板", "两层", "黏度", "粘度", "剪应力连续", "倾斜平板"],
    },
    {
        "chapter": "第5/6章 理想不可压无旋流动",
        "mother": "母题4：势流叠加/圆柱绕流/镜像/升力",
        "child": "圆柱绕流/有环量/半圆柱升力",
        "keywords": ["圆柱", "半圆柱", "绕流", "环量", "升力", "库塔", "儒可夫斯基", "气膜", "表面压力", "驻点"],
    },
    {
        "chapter": "第5/6章 理想不可压无旋流动",
        "mother": "母题4：势流叠加/圆柱绕流/镜像/升力",
        "child": "点源点汇点涡偶极子/镜像法/壁面",
        "keywords": ["点源", "点汇", "点涡", "偶极", "偶极子", "镜像", "壁面", "半平面", "流函数", "势函数", "叠加"],
    },
    {
        "chapter": "第4章 动力学基础",
        "mother": "母题2：Bernoulli/PVZ/控制体动量",
        "child": "机械能方程/PVZ/孔口出流/虹吸",
        "keywords": ["伯努利", "Bernoulli", "PVZ", "机械能", "孔口", "虹吸", "文丘里", "毕托", "测压管", "水头"],
    },
    {
        "chapter": "第4章 动力学基础",
        "mother": "母题2：Bernoulli/PVZ/控制体动量",
        "child": "控制体动量/弯管/喷嘴/叶片受力",
        "keywords": ["控制体", "动量", "弯管", "喷嘴", "喷射", "叶片", "冲击", "反力", "推力", "动量矩"],
    },
    {
        "chapter": "第2章 流体静力学",
        "mother": "母题1：静水压强/测压/闸门受力",
        "child": "平面闸门/曲面压力/浮力稳定",
        "keywords": ["闸门", "平面", "曲面", "压力中心", "压强分布", "浮力", "稳定", "倾斜", "U形管", "测压"],
    },
    {
        "chapter": "第3章 运动学与应力",
        "mother": "母题3：运动学/连续/应力张量",
        "child": "速度场/加速度/流线/连续方程/应力向量",
        "keywords": ["速度场", "加速度", "流线", "迹线", "连续", "散度", "旋度", "涡量", "应力张量", "应力向量", "单位法向"],
    },
    {
        "chapter": "第8/9章 边界层与外绕流",
        "mother": "母题7：边界层/外绕流阻力",
        "child": "平板边界层厚度/阻力/转捩",
        "keywords": ["边界层", "平板", "层流边界层", "湍流边界层", "转捩", "摩擦阻力", "排挤厚度", "动量厚度", "Blasius"],
    },
    {
        "chapter": "第8/9章 边界层与外绕流",
        "mother": "母题7：边界层/外绕流阻力",
        "child": "外绕流阻力/小球/圆柱/阻力系数",
        "keywords": ["阻力系数", "小球", "圆球", "圆柱阻力", "迎风面积", "终端速度", "Stokes", "绕流阻力"],
    },
    {
        "chapter": "相似理论",
        "mother": "母题8：量纲分析/模型相似",
        "child": "Pi定理/相似准则/模型试验",
        "keywords": ["量纲", "相似", "模型", "原型", "Pi", "π", "雷诺相似", "弗劳德", "马赫相似", "欧拉数"],
    },
]


def clean_text(text: str) -> str:
    text = (text or "").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_units(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    if len(text) < 900:
        return [text]

    markers = [
        r"(?=\s*\[\d+\]\.)",
        r"(?=\s*\d{1,2}[-．.]\d{1,2}\s)",
        r"(?=\s*书\s*\d+\.\d+)",
        r"(?=\s*题\s*\d+\.\d+)",
        r"(?=\s*\(\d+\)\s*)",
        r"(?=\s*[一二三四五六七八九十]+、)",
    ]
    pattern = "|".join(markers)
    parts = [p.strip() for p in re.split(pattern, text) if len(p.strip()) > 35]
    if len(parts) <= 1:
        return [text]

    merged: list[str] = []
    buf = ""
    for part in parts:
        if len(buf) < 160:
            buf = (buf + " " + part).strip()
        else:
            merged.append(buf)
            buf = part
    if buf:
        merged.append(buf)
    return merged[:40]


def keyword_hits(text: str, keywords: list[str]) -> int:
    low = text.lower()
    total = 0
    for kw in keywords:
        if kw.lower() in low:
            total += 1
    return total


def classify(text: str, folder: str) -> tuple[str, str, str, str]:
    default = FOLDER_DEFAULT.get(folder, ("未定章节", "母题X：待人工复核", "待人工复核"))
    best = (0, default[0], default[1], default[2])
    for rule in RULES:
        hits = keyword_hits(text, rule["keywords"])
        score = hits * 3
        if default[0] == rule["chapter"]:
            score += 1
        if default[1] == rule["mother"]:
            score += 2
        if score > best[0]:
            best = (score, rule["chapter"], rule["mother"], rule["child"])

    score, chapter, mother, child = best
    if score >= 10:
        conf = "高"
    elif score >= 5:
        conf = "中"
    else:
        conf = "低-按原文件夹归类"
        chapter, mother, child = default
    return chapter, mother, child, conf


def representative_score(text: str, row: dict[str, str], chapter: str, mother: str, child: str) -> int:
    s = min(18, max(1, len(text) // 140))
    group = row.get("group", "")
    if "往年" in group or "期末" in group:
        s += 10
    if "作业" in group:
        s += 3
    if "图" in text or "如图" in text or "[[PDF_PAGE" in text:
        s += 5
    s += min(8, len(re.findall(r"求|问|证明|判断|计算|估算|比较", text)))
    s += min(8, len(re.findall(r"\(\d+\)|（\d+）|[a-d]\)", text)))
    quantities = re.findall(r"[A-Za-zΑ-Ωα-ω_][A-Za-z0-9_]*\s*=|[0-9]+(?:\.[0-9]+)?\s*(?:m/s|Pa|kPa|MPa|kg|cm|mm|m\^?2|m3/s|N)", text)
    s += min(12, len(quantities) // 2)
    if any(k in mother for k in ["Laval", "管路", "圆柱", "控制体", "边界层"]):
        s += 4
    if any(k in child for k in ["综合", "判定", "位置", "泵", "升力", "控制体"]):
        s += 3
    return int(s)


def need_original_confirm(text: str) -> str:
    if "[[PDF_PAGE" in text or len(text) < 60:
        return "是"
    if "缺" in text and ("题面" in text or "条件" in text):
        return "是"
    return "否"


def read_rows() -> list[dict[str, str]]:
    with INDEX.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    src_rows = read_rows()
    out_rows: list[dict[str, object]] = []
    uid = 1

    for row in src_rows:
        units = split_units(row.get("question_text", ""))
        if not units:
            units = [""]
        for i, text in enumerate(units, 1):
            chapter, mother, child, confidence = classify(text, row.get("type_folder", ""))
            score = representative_score(text, row, chapter, mother, child)
            out_rows.append(
                {
                    "unit_id": f"U{uid:05d}",
                    "source_item_id": row.get("item_id", ""),
                    "split_no": i,
                    "chapter": chapter,
                    "topic_folder": row.get("type_folder", ""),
                    "mother": mother,
                    "child_type": child,
                    "confidence": confidence,
                    "represent_score": score,
                    "need_original_confirm": need_original_confirm(text),
                    "source_group": row.get("group", ""),
                    "source_label": row.get("source_label", ""),
                    "question_no": row.get("question_no", ""),
                    "question_text": text,
                    "source_file": row.get("source_file", ""),
                }
            )
            uid += 1

    fields = [
        "unit_id",
        "source_item_id",
        "split_no",
        "chapter",
        "topic_folder",
        "mother",
        "child_type",
        "confidence",
        "represent_score",
        "need_original_confirm",
        "source_group",
        "source_label",
        "question_no",
        "question_text",
        "source_file",
    ]
    all_csv = OUT / "全题归类表_重整版一.csv"
    write_csv(all_csv, out_rows, fields)

    top_rows: list[dict[str, object]] = []
    by_mother: dict[str, list[dict[str, object]]] = defaultdict(list)
    for r in out_rows:
        by_mother[str(r["mother"])].append(r)
    for mother, rs in by_mother.items():
        for r in sorted(rs, key=lambda x: int(x["represent_score"]), reverse=True)[:8]:
            top_rows.append(r)
    top_csv = OUT / "每类代表题Top题_重整版一.csv"
    write_csv(top_csv, top_rows, fields)

    chapter_counts = Counter(str(r["chapter"]) for r in out_rows)
    mother_counts = Counter(str(r["mother"]) for r in out_rows)
    child_counts = Counter(str(r["child_type"]) for r in out_rows)
    source_counts = Counter(str(r["source_group"]) for r in out_rows)
    conf_counts = Counter(str(r["confidence"]) for r in out_rows)

    top_overall = sorted(out_rows, key=lambda x: int(x["represent_score"]), reverse=True)[:25]

    lines: list[str] = []
    lines.append("# 全目录题目归类报告：重整版一")
    lines.append("")
    lines.append("## 0. 处理范围")
    lines.append("")
    lines.append(f"- 根目录：`{ROOT}`")
    lines.append(f"- 读取主索引：`{INDEX}`")
    lines.append(f"- 原结构化题目条目：{len(src_rows)}")
    lines.append(f"- 拆分后题目单元：{len(out_rows)}")
    lines.append(f"- 需回看原题/OCR确认：{sum(1 for r in out_rows if r['need_original_confirm'] == '是')}")
    lines.append("")
    lines.append("> 说明：当前目录里可直接机器读取的主索引是 591 条结构化题。你说的“2000 道”大概率还包括 PDF/图片/答案版/重复稿中未进入索引的题；本版先把已结构化题全量归类，后续可以继续做 OCR 补题。")
    lines.append("")

    lines.append("## 1. 按章节归类统计")
    lines.append("")
    lines.append("| 章节 | 题目单元数 |")
    lines.append("|---|---:|")
    for k, v in chapter_counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    lines.append("## 2. 按母题归类统计")
    lines.append("")
    lines.append("| 母题 | 题目单元数 |")
    lines.append("|---|---:|")
    for k, v in mother_counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    lines.append("## 3. 子题/题型分布")
    lines.append("")
    lines.append("| 子题/题型 | 题目单元数 |")
    lines.append("|---|---:|")
    for k, v in child_counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    lines.append("## 4. 来源与置信度")
    lines.append("")
    lines.append("| 来源 | 题目单元数 |")
    lines.append("|---|---:|")
    for k, v in source_counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("| 归类置信度 | 题目单元数 |")
    lines.append("|---|---:|")
    for k, v in conf_counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    lines.append("## 5. 每个母题的代表题 Top")
    lines.append("")
    for mother, rs in sorted(by_mother.items(), key=lambda kv: len(kv[1]), reverse=True):
        lines.append(f"### {mother}")
        lines.append("")
        lines.append("| 排名 | 分数 | unit_id | 章节 | 子题 | 来源 | 题面摘要 |")
        lines.append("|---:|---:|---|---|---|---|---|")
        for rank, r in enumerate(sorted(rs, key=lambda x: int(x["represent_score"]), reverse=True)[:6], 1):
            text = str(r["question_text"])
            text = text[:120].replace("|", "/")
            lines.append(
                f"| {rank} | {r['represent_score']} | {r['unit_id']} | {r['chapter']} | {r['child_type']} | {r['source_label']} | {text} |"
            )
        lines.append("")

    lines.append("## 6. 全部题库里最值得做成开卷资料母题的综合题")
    lines.append("")
    lines.append("### 单题最综合优先级")
    lines.append("")
    lines.append("1. `Q0033` / 对应拆分单元：两油箱经突扩钢管连接，分短管局部损失与长管沿程损失，求输油流量、A/B 点压强、所需液面差。")
    lines.append("   - 理由：同时覆盖 PVZ、流量-流速、Re 判流态、沿程损失、局部损失、突扩、管内点压强、表压/绝压与单位检查。")
    lines.append("   - 建议定位：母题6 管路/泵阀/损失综合 的核心真题。")
    lines.append("2. `Q0002` 的 Laval 喷管汞柱题。")
    lines.append("   - 理由：覆盖喉部阻塞、面积-马赫数、背压判定、出口正激波/管内正激波、设计工况水银柱。")
    lines.append("   - 建议定位：母题5 可压缩流 的核心真题。")
    lines.append("3. `Q0034` / 半圆柱气膜馆绕流升力题。")
    lines.append("   - 理由：覆盖圆柱势流速度分布、Bernoulli 压力分布、曲面投影积分、升力方向。")
    lines.append("   - 建议定位：母题4 势流/圆柱/升力 的核心真题。")
    lines.append("")

    lines.append("### 按评分自动选出的 Top 25")
    lines.append("")
    lines.append("| 排名 | 分数 | unit_id | 母题 | 子题 | 来源 | 摘要 |")
    lines.append("|---:|---:|---|---|---|---|---|")
    for rank, r in enumerate(top_overall, 1):
        text = str(r["question_text"])[:130].replace("|", "/")
        lines.append(
            f"| {rank} | {r['represent_score']} | {r['unit_id']} | {r['mother']} | {r['child_type']} | {r['source_label']} | {text} |"
        )
    lines.append("")

    lines.append("## 7. 下一步")
    lines.append("")
    lines.append("1. 先人工确认 `need_original_confirm=是` 的题是否需要回看图片/PDF。")
    lines.append("2. 再从 `每类代表题Top题_重整版一.csv` 中选每个母题 1-3 道，写成六页开卷资料的母题模板。")
    lines.append("3. 若要逼近你说的 2000 道，需要对未入索引 PDF/图片继续 OCR，然后并入本表。")

    report = OUT / "全目录题目归类报告_重整版一.md"
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"ROOT={ROOT}")
    print(f"source_rows={len(src_rows)}")
    print(f"units={len(out_rows)}")
    print(f"report={report}")
    print(f"all_csv={all_csv}")
    print(f"top_csv={top_csv}")


if __name__ == "__main__":
    main()
