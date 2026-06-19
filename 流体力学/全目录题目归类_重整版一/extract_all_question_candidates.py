from __future__ import annotations

import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from classify_questions import classify, representative_score


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "流体力学"
OUT = ROOT / "全目录题目归类_重整版一"
OUT.mkdir(parents=True, exist_ok=True)

TEXT_SUFFIXES = {".txt", ".md", ".tex", ".csv"}
SKIP_DIR_PARTS = {
    "全目录题目归类_重整版一",
    ".git",
    "__pycache__",
}

QUESTION_HINTS = [
    "求",
    "问",
    "试求",
    "计算",
    "证明",
    "判断",
    "估算",
    "比较",
    "已知",
    "如图",
    "书 ",
    "习题",
    "题 ",
    "真题",
]


def safe_read(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "latin1"):
        try:
            return path.read_text(encoding=enc, errors="strict")
        except Exception:
            continue
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def compact(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\(begin|end)\{[^}]+\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def likely_question(text: str) -> bool:
    if len(text) < 35:
        return False
    if len(text) > 8000:
        return False
    score = 0
    for h in QUESTION_HINTS:
        if h in text:
            score += 1
    if re.search(r"(?:书|题|习题)\s*\d+\.\d+", text):
        score += 3
    if re.search(r"\d+(?:\.\d+)?\s*(?:m/s|Pa|kPa|MPa|kg/m|cm|mm|m\^?2|m3/s|N)", text):
        score += 1
    if re.search(r"\(\d+\)|（\d+）|[a-d]\)", text):
        score += 1
    bad = ["覆盖约", "预计分数", "v11", "v10", "扣分", "报告", "覆盖率"]
    if score < 2 and any(b in text for b in bad):
        return False
    return score >= 2


def split_text_blocks(raw: str) -> list[str]:
    text = raw.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Prefer headings/tasks/items as boundaries.
    boundary = (
        r"(?=\n\s*#{1,4}\s+)"
        r"|(?=\n\s*\\(?:section|subsection|subsubsection)\*?\{)"
        r"|(?=\n\s*\\(?:item|task)\b)"
        r"|(?=\n\s*(?:题|书|习题)\s*\d+\.\d+)"
        r"|(?=\n\s*\d{1,2}[.、．]\s+)"
        r"|(?=\n\s*\[\d+\]\.)"
    )
    pieces = re.split(boundary, "\n" + text)
    blocks: list[str] = []
    for p in pieces:
        p = compact(p)
        if not p:
            continue
        if len(p) > 2500:
            # Long solved notes usually contain several tasks; cut again by common submarkers.
            sub = re.split(r"(?=\s*(?:题|书|习题)\s*\d+\.\d+)|(?=\s*\[\d+\]\.)|(?=\s*\(\d+\)\s*)", p)
            for s in sub:
                s = compact(s)
                if likely_question(s):
                    blocks.append(s[:4500])
        elif likely_question(p):
            blocks.append(p[:4500])
    return blocks


def csv_candidates(path: Path) -> list[str]:
    out: list[str] = []
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            with path.open("r", encoding=enc, newline="", errors="strict") as f:
                reader = csv.DictReader(f)
                fields = reader.fieldnames or []
                q_fields = [
                    x
                    for x in fields
                    if any(k in x.lower() for k in ["question", "题", "text", "原题", "题面"])
                ]
                if not q_fields:
                    return []
                for row in reader:
                    text = " ".join(row.get(fld, "") for fld in q_fields)
                    text = compact(text)
                    if likely_question(text):
                        out.append(text[:4500])
                return out
        except Exception:
            continue
    return out


def norm_hash(text: str) -> str:
    x = text.lower()
    x = re.sub(r"\s+", "", x)
    x = re.sub(r"[，。、“”‘’；：？！,.!?;:\-_=+()（）\[\]【】{}<>《》]", "", x)
    x = x[:650]
    return hashlib.sha1(x.encode("utf-8", errors="ignore")).hexdigest()


def original_questionish(text: str) -> bool:
    reject = [
        "公式血缘表",
        "覆盖约",
        "预计分数",
        "关联章节",
        "HTML",
        "视觉组件",
        "压缩方案",
        "速查表",
        "扣分",
        "报告",
        "适用条件 |",
    ]
    if any(x in text for x in reject):
        return False
    verbs = sum(1 for x in ["求", "问", "试求", "计算", "证明", "判断", "估算", "比较"] if x in text)
    markers = 0
    if re.search(r"(?:书|题|习题)\s*\d+\.\d+", text):
        markers += 2
    if re.search(r"\b\d{1,2}-\d{1,2}\b", text):
        markers += 2
    if re.search(r"Q\d{3,5}|题干|真题|作业|如图|已知", text):
        markers += 1
    if re.search(r"\(\d+\)|（\d+）|[a-d]\)", text):
        markers += 1
    numbers = len(re.findall(r"\d+(?:\.\d+)?\s*(?:m/s|Pa|kPa|MPa|kg|cm|mm|m\^?2|m3/s|N)", text))
    return verbs >= 1 and (markers >= 1 or numbers >= 2)


def source_kind(path: Path) -> str:
    s = str(path)
    if "速查表" in s or "评判报告" in s or "cheatsheet" in s.lower():
        return "旧速查表/评判报告"
    if "期末试题" in s or "期末" in path.name or "真题" in path.name:
        return "往年/真题"
    if "作业" in s:
        return "作业/答案"
    if "教材" in s or "课本" in s:
        return "教材/课本"
    if "题库" in s:
        return "题库"
    return "其他文本"


def main() -> None:
    files = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.suffix.lower() in TEXT_SUFFIXES
        and not any(part in SKIP_DIR_PARTS for part in p.parts)
    ]

    candidates: list[dict[str, object]] = []
    seen_per_file: set[tuple[str, str]] = set()
    cid = 1
    for path in files:
        texts = csv_candidates(path) if path.suffix.lower() == ".csv" else split_text_blocks(safe_read(path))
        for idx, text in enumerate(texts, 1):
            key = (str(path), norm_hash(text))
            if key in seen_per_file:
                continue
            seen_per_file.add(key)
            topic_folder = ""
            chapter, mother, child, confidence = classify(text, topic_folder)
            fake_row = {
                "group": source_kind(path),
                "source_label": path.name,
            }
            score = representative_score(text, fake_row, chapter, mother, child)
            candidates.append(
                {
                    "candidate_id": f"C{cid:05d}",
                    "dedup_hash": norm_hash(text),
                    "chapter": chapter,
                    "mother": mother,
                    "child_type": child,
                    "confidence": confidence,
                    "represent_score": score,
                    "source_kind": source_kind(path),
                    "source_file": str(path),
                    "block_no": idx,
                    "question_text": text,
                }
            )
            cid += 1

    # Keep highest-scoring representative per normalized hash.
    best_by_hash: dict[str, dict[str, object]] = {}
    for c in candidates:
        h = str(c["dedup_hash"])
        if h not in best_by_hash or int(c["represent_score"]) > int(best_by_hash[h]["represent_score"]):
            best_by_hash[h] = c
    deduped = list(best_by_hash.values())
    deduped.sort(key=lambda r: (str(r["mother"]), -int(r["represent_score"])))
    allowed_original_sources = {"往年/真题", "作业/答案", "教材/课本", "题库"}
    original_like = [
        r
        for r in deduped
        if str(r["source_kind"]) in allowed_original_sources
        and "全目录题目归类_重整版一" not in str(r["source_file"])
        and original_questionish(str(r["question_text"]))
    ]

    fields = [
        "candidate_id",
        "dedup_hash",
        "chapter",
        "mother",
        "child_type",
        "confidence",
        "represent_score",
        "source_kind",
        "source_file",
        "block_no",
        "question_text",
    ]
    with (OUT / "全目录候选题归类表_重整版一.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(candidates)
    with (OUT / "去重后题目归类表_重整版一.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(deduped)
    with (OUT / "原题去重归类表_重整版一.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(original_like)

    by_mother: dict[str, list[dict[str, object]]] = defaultdict(list)
    for r in deduped:
        by_mother[str(r["mother"])].append(r)
    top_rows = []
    for mother, rs in by_mother.items():
        top_rows.extend(sorted(rs, key=lambda r: int(r["represent_score"]), reverse=True)[:12])
    with (OUT / "候选池每类代表题Top题_重整版一.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(top_rows)

    original_by_mother: dict[str, list[dict[str, object]]] = defaultdict(list)
    for r in original_like:
        original_by_mother[str(r["mother"])].append(r)
    original_top_rows = []
    for mother, rs in original_by_mother.items():
        original_top_rows.extend(sorted(rs, key=lambda r: int(r["represent_score"]), reverse=True)[:12])
    with (OUT / "原题每类代表题Top题_重整版一.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(original_top_rows)

    file_counts = Counter(source_kind(p) for p in files)
    cand_counts = Counter(str(r["source_kind"]) for r in candidates)
    mother_counts = Counter(str(r["mother"]) for r in deduped)
    chapter_counts = Counter(str(r["chapter"]) for r in deduped)
    original_mother_counts = Counter(str(r["mother"]) for r in original_like)

    lines: list[str] = []
    lines.append("# 全目录候选题扫描报告：重整版一")
    lines.append("")
    lines.append("## 0. 范围")
    lines.append("")
    lines.append(f"- 扫描根目录：`{ROOT}`")
    lines.append(f"- 文本类文件数：{len(files)}")
    lines.append(f"- 候选题块数：{len(candidates)}")
    lines.append(f"- 去重后候选题数：{len(deduped)}")
    lines.append(f"- 排除旧速查表/评判报告后的原题候选数：{len(original_like)}")
    lines.append("")
    lines.append("> 这里的候选题池比主索引更宽，会包含答案稿、旧速查表评判报告、教材摘录里的题。它适合用来找母题/子题，但正式进入六页资料前还要人工筛掉重复和非题干块。")
    lines.append("")
    lines.append("## 1. 文件来源统计")
    lines.append("")
    lines.append("| 来源类型 | 文件数 | 候选题块数 |")
    lines.append("|---|---:|---:|")
    for k in sorted(set(file_counts) | set(cand_counts)):
        lines.append(f"| {k} | {file_counts.get(k, 0)} | {cand_counts.get(k, 0)} |")
    lines.append("")
    lines.append("## 2. 去重后按章节统计")
    lines.append("")
    lines.append("| 章节 | 去重候选题数 |")
    lines.append("|---|---:|")
    for k, v in chapter_counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## 3. 去重后按母题统计")
    lines.append("")
    lines.append("| 母题 | 去重候选题数 |")
    lines.append("|---|---:|")
    for k, v in mother_counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## 4. 每个母题最值得抽为开卷资料的候选题")
    lines.append("")
    for mother, rs in sorted(by_mother.items(), key=lambda kv: len(kv[1]), reverse=True):
        lines.append(f"### {mother}")
        lines.append("")
        lines.append("| 排名 | 分数 | id | 子题 | 来源 | 摘要 |")
        lines.append("|---:|---:|---|---|---|---|")
        for rank, r in enumerate(sorted(rs, key=lambda x: int(x["represent_score"]), reverse=True)[:8], 1):
            text = str(r["question_text"])[:120].replace("|", "/")
            lines.append(
                f"| {rank} | {r['represent_score']} | {r['candidate_id']} | {r['child_type']} | {Path(str(r['source_file'])).name} | {text} |"
            )
        lines.append("")

    lines.append("## 5. 原题候选：按母题统计")
    lines.append("")
    lines.append("| 母题 | 原题候选数 |")
    lines.append("|---|---:|")
    for k, v in original_mother_counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    lines.append("## 6. 原题候选：每个母题最值得抽为模板的题")
    lines.append("")
    for mother, rs in sorted(original_by_mother.items(), key=lambda kv: len(kv[1]), reverse=True):
        lines.append(f"### {mother}")
        lines.append("")
        lines.append("| 排名 | 分数 | id | 子题 | 来源类型 | 来源文件 | 摘要 |")
        lines.append("|---:|---:|---|---|---|---|---|")
        for rank, r in enumerate(sorted(rs, key=lambda x: int(x["represent_score"]), reverse=True)[:8], 1):
            text = str(r["question_text"])[:120].replace("|", "/")
            lines.append(
                f"| {rank} | {r['represent_score']} | {r['candidate_id']} | {r['child_type']} | {r['source_kind']} | {Path(str(r['source_file'])).name} | {text} |"
            )
        lines.append("")

    lines.append("## 7. 现阶段判断")
    lines.append("")
    lines.append("- 最适合做六页资料核心母题的单题，仍优先选：两油箱变径突扩钢管题、Laval 喷管汞柱/正激波题、半圆柱气膜馆绕流升力题。")
    lines.append("- 本扫描显示目录里确实存在超过主索引的候选题块；但很多来自旧报告和答案稿，不能直接等同于 2000 道互不重复原题。")
    lines.append("- 下一步应从 `候选池每类代表题Top题_重整版一.csv` 人工定稿母题与子题，再写 PDF。")

    (OUT / "全目录候选题扫描报告_重整版一.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"text_files={len(files)}")
    print(f"candidate_blocks={len(candidates)}")
    print(f"deduped_candidates={len(deduped)}")
    print(OUT / "全目录候选题扫描报告_重整版一.md")


if __name__ == "__main__":
    main()
