from __future__ import annotations

import csv
import re
from collections import Counter, OrderedDict
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


BASE = Path(r"D:\虚拟C盘\学习\固体力学\考题_按知识点整理")
CSV_PATH = BASE / "固体力学历年题库_知识点训练版.csv"
SCREENSHOT_MD = BASE / "固体力学历年题库_知识点训练版_截图.md"
OUT_DIR = Path(r"D:\虚拟C盘\学习\固体力学\期末复习资料")
OUT_PDF = OUT_DIR / "梁专题_历年题截图集.pdf"
OUT_INDEX = OUT_DIR / "梁专题_历年题截图集_索引.csv"

PRIMARY_KP = {
    "K05.1",
    "K05.2",
    "K06.1",
    "K07.1",
    "K07.2",
    "K07.3",
    "K10.1",
    "K10.2",
}

EXTRA_KEYWORDS = [
    "粘合",
    "胶合",
    "叠合",
    "组合梁",
    "复合材料梁",
    "多层",
    "三层梁",
    "两层梁",
    "弯曲刚度",
    "中性轴",
    "等强度梁",
]

SECTION_ORDER = OrderedDict(
    [
        ("S1", "支反力、剪力图、弯矩图、危险截面"),
        ("S2", "截面几何、弯曲正应力、强度校核"),
        ("S3", "挠曲线、转角、挠度、能量法"),
        ("S4", "多材料、多层梁、粘合与不粘合"),
    ]
)


def register_fonts() -> str:
    font_name = "STSong-Light"
    pdfmetrics.registerFont(UnicodeCIDFont(font_name))
    return font_name


def parse_screenshot_map() -> dict[str, Path]:
    text = SCREENSHOT_MD.read_text(encoding="utf-8")
    mapping: dict[str, Path] = {}
    pattern = re.compile(r"####\s+(Q\d+)\s+-.*?\n\n(?:!\[[^\]]*\]\(([^)]+)\))?", re.S)
    for match in pattern.finditer(text):
        qid, image = match.group(1), match.group(2)
        if image:
            mapping[qid] = Path(image.replace("/", "\\"))
    return mapping


def select_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            text = "".join(
                [
                    row.get("question") or "",
                    row.get("topic_name") or "",
                    row.get("kp_name") or "",
                ]
            )
            if row.get("kp") in PRIMARY_KP or any(k in text for k in EXTRA_KEYWORDS):
                rows.append(row)
    return rows


def row_section(row: dict[str, str]) -> str:
    kp = row.get("kp", "")
    text = row.get("question", "")
    if kp in {"K05.1", "K05.2"}:
        return "S1"
    if kp in {"K06.1", "K07.1", "K07.2", "K07.3"}:
        return "S2"
    if kp in {"K10.1", "K10.2"}:
        return "S3"
    if any(k in text for k in EXTRA_KEYWORDS):
        return "S4"
    return "S2"


def wrap_text(text: str, font: str, size: float, max_width: float) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if pdfmetrics.stringWidth(trial, font, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font: str,
    size: float,
    leading: float,
    max_lines: int | None = None,
) -> float:
    lines = wrap_text(text, font, size, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip("。；，,") + "..."
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def footer(c: canvas.Canvas, font: str, page_no: int) -> None:
    width, _ = A4
    c.setStrokeColor(colors.HexColor("#D7D7D7"))
    c.line(18 * mm, 12 * mm, width - 18 * mm, 12 * mm)
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont(font, 8)
    c.drawRightString(width - 18 * mm, 7 * mm, f"第 {page_no} 页")
    c.setFillColor(colors.black)


def draw_title_page(c: canvas.Canvas, font: str, rows: list[dict[str, str]], image_map: dict[str, Path]) -> int:
    width, height = A4
    page_no = 1
    c.setFillColor(colors.HexColor("#0F2A2A"))
    c.rect(0, height - 52 * mm, width, 52 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(font, 25)
    c.drawString(22 * mm, height - 28 * mm, "固体力学梁专题历年题截图集")
    c.setFont(font, 11)
    c.drawString(22 * mm, height - 40 * mm, "范围：支反力、剪力图、弯矩图、弯曲应力、挠度转角、复合/粘合梁")

    counts = Counter(row_section(r) for r in rows)
    with_images = sum(1 for r in rows if r["id"] in image_map)
    missing = len(rows) - with_images

    y = height - 72 * mm
    c.setFillColor(colors.black)
    c.setFont(font, 14)
    c.drawString(22 * mm, y, "筛选结果")
    y -= 10 * mm
    facts = [
        f"共筛出 {len(rows)} 条梁专题相关题目。",
        f"其中 {with_images} 条已有原卷截图；{missing} 条为原始回忆版文字题，保留为文字页。",
        "筛选规则：K05、K06、K07、K10 梁相关知识点，并额外纳入含粘合、胶合、叠合、多层、弯曲刚度等关键词的近年题。",
        "用途：先按章节刷题，再用题号回到原卷核对上下文。",
    ]
    for item in facts:
        y = draw_wrapped(c, item, 24 * mm, y, width - 48 * mm, font, 11, 6 * mm)
        y -= 2 * mm

    y -= 4 * mm
    c.setFont(font, 14)
    c.drawString(22 * mm, y, "分组")
    y -= 9 * mm
    c.setFont(font, 11)
    for sid, title in SECTION_ORDER.items():
        c.drawString(28 * mm, y, f"{title}：{counts.get(sid, 0)} 题")
        y -= 7 * mm

    footer(c, font, page_no)
    c.showPage()
    return page_no + 1


def draw_index_pages(c: canvas.Canvas, font: str, grouped: dict[str, list[dict[str, str]]], page_no: int) -> int:
    width, height = A4
    margin_x = 16 * mm
    y = height - 20 * mm
    c.setFont(font, 18)
    c.drawString(margin_x, y, "题目索引")
    y -= 12 * mm
    c.setFont(font, 8.5)
    for sid, title in SECTION_ORDER.items():
        c.setFont(font, 12)
        c.setFillColor(colors.HexColor("#0F2A2A"))
        c.drawString(margin_x, y, f"{title}（{len(grouped.get(sid, []))} 题）")
        c.setFillColor(colors.black)
        y -= 7 * mm
        c.setFont(font, 8.5)
        for row in grouped.get(sid, []):
            if y < 22 * mm:
                footer(c, font, page_no)
                c.showPage()
                page_no += 1
                y = height - 20 * mm
                c.setFont(font, 8.5)
            source = row.get("source", "")
            kp = row.get("kp", "")
            q = row.get("question", "")
            line = f"{row['id']}  {kp}  {source}  {q[:44]}"
            y = draw_wrapped(c, line, margin_x, y, width - 2 * margin_x, font, 8.5, 4.8 * mm, max_lines=2)
            y -= 1.2 * mm
        y -= 3 * mm
    footer(c, font, page_no)
    c.showPage()
    return page_no + 1


def draw_question_page(
    c: canvas.Canvas,
    font: str,
    row: dict[str, str],
    image_path: Path | None,
    section_title: str,
    page_no: int,
) -> int:
    width, height = A4
    margin_x = 14 * mm
    top = height - 16 * mm
    c.setFillColor(colors.HexColor("#0F2A2A"))
    c.setFont(font, 12)
    c.drawString(margin_x, top, f"{row['id']}  {section_title}")
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont(font, 8.5)
    meta = f"{row.get('source', '')}  |  {row.get('kp', '')} {row.get('kp_name', '')}"
    c.drawString(margin_x, top - 6 * mm, meta[:120])
    c.setFillColor(colors.black)

    y = top - 13 * mm
    if image_path and image_path.exists():
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img_w, img_h = img.size
            max_w = width - 2 * margin_x
            max_h = height - 42 * mm
            scale = min(max_w / img_w, max_h / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale
            x = (width - draw_w) / 2
            c.setStrokeColor(colors.HexColor("#DDDDDD"))
            c.rect(x - 2 * mm, y - draw_h - 2 * mm, draw_w + 4 * mm, draw_h + 4 * mm, stroke=1, fill=0)
            c.drawImage(ImageReader(img), x, y - draw_h, width=draw_w, height=draw_h)
    else:
        c.setFillColor(colors.HexColor("#F6F6F2"))
        c.roundRect(margin_x, 35 * mm, width - 2 * margin_x, height - 72 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#333333"))
        c.setFont(font, 10)
        c.drawString(margin_x + 5 * mm, height - 44 * mm, "原始回忆版文字题")
        draw_wrapped(
            c,
            row.get("question", ""),
            margin_x + 5 * mm,
            height - 56 * mm,
            width - 2 * margin_x - 10 * mm,
            font,
            10.5,
            6 * mm,
        )
        c.setFillColor(colors.black)

    footer(c, font, page_no)
    c.showPage()
    return page_no + 1


def write_index_csv(rows: list[dict[str, str]], image_map: dict[str, Path]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["id", "section", "kp", "kp_name", "source", "path", "image_path", "question"]
    with OUT_INDEX.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            sid = row_section(row)
            writer.writerow(
                {
                    "id": row["id"],
                    "section": SECTION_ORDER[sid],
                    "kp": row.get("kp", ""),
                    "kp_name": row.get("kp_name", ""),
                    "source": row.get("source", ""),
                    "path": row.get("path", ""),
                    "image_path": str(image_map.get(row["id"], "")),
                    "question": row.get("question", ""),
                }
            )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    font = register_fonts()
    image_map = parse_screenshot_map()
    rows = select_rows()
    rows.sort(key=lambda r: (list(SECTION_ORDER).index(row_section(r)), r.get("source", ""), r.get("id", "")))
    write_index_csv(rows, image_map)

    grouped: dict[str, list[dict[str, str]]] = {sid: [] for sid in SECTION_ORDER}
    for row in rows:
        grouped[row_section(row)].append(row)

    c = canvas.Canvas(str(OUT_PDF), pagesize=A4)
    c.setTitle("固体力学梁专题历年题截图集")
    page_no = draw_title_page(c, font, rows, image_map)
    page_no = draw_index_pages(c, font, grouped, page_no)
    for sid, title in SECTION_ORDER.items():
        for row in grouped[sid]:
            page_no = draw_question_page(c, font, row, image_map.get(row["id"]), title, page_no)
    c.save()

    print(f"PDF: {OUT_PDF}")
    print(f"INDEX: {OUT_INDEX}")
    print(f"QUESTIONS: {len(rows)}")
    print(f"WITH_SCREENSHOTS: {sum(1 for r in rows if r['id'] in image_map)}")


if __name__ == "__main__":
    main()
