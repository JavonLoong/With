from __future__ import annotations

import datetime as dt
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown
import fitz
from bs4 import BeautifulSoup, Tag


TITLE = "高中物理科学史可考细节汇总"
SUBTITLE = "考试导向 · 细节库 · 高级讲义版"


def find_source_md(base: Path) -> Path:
    candidates = sorted(
        base.glob("*科学史可考细节汇总.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("未找到“*科学史可考细节汇总.md”源文件")
    return candidates[0]


def find_chrome() -> Path:
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    found = shutil.which("chrome") or shutil.which("msedge") or shutil.which("chromium")
    if found:
        return Path(found)
    raise FileNotFoundError("未找到 Chrome 或 Edge，无法无头导出 PDF")


def convert_markdown(md_text: str) -> BeautifulSoup:
    body = markdown.markdown(
        md_text,
        extensions=[
            "tables",
            "fenced_code",
            "sane_lists",
            "toc",
            "smarty",
        ],
        output_format="html5",
    )
    soup = BeautifulSoup(body, "html.parser")
    return soup


def normalize_body(soup: BeautifulSoup) -> tuple[str, list[dict[str, str]]]:
    first_h1 = soup.find("h1")
    if first_h1:
        first_h1.decompose()

    headings: list[dict[str, str]] = []
    heading_index = 0
    section_index = 0
    for heading in soup.find_all(re.compile("^h[2-4]$")):
        heading_index += 1
        if heading.name == "h2":
            section_index += 1
            heading["data-section"] = f"{section_index:02d}"
        heading_id = f"sec-{heading_index:03d}"
        heading["id"] = heading_id
        text = heading.get_text(" ", strip=True)
        if heading.name in {"h2", "h3"}:
            headings.append({"level": heading.name, "id": heading_id, "text": text})

    for table in soup.find_all("table"):
        table["class"] = table.get("class", []) + ["study-table"]
        rows = table.find_all("tr")
        col_count = 0
        for row in rows:
            col_count = max(col_count, len(row.find_all(["th", "td"])))
        if col_count == 2:
            table["class"] = table.get("class", []) + ["kv-table"]
        elif col_count >= 5:
            table["class"] = table.get("class", []) + ["wide-table"]
        else:
            table["class"] = table.get("class", []) + ["medium-table"]

        first_header = [cell.get_text(" ", strip=True) for cell in table.find_all("th")[:2]]
        if first_header in (["项目", "内容"], ["人物", "贡献"]):
            table["class"] = table.get("class", []) + ["profile-table"]

        nearest_heading = table.find_previous(
            lambda tag: isinstance(tag, Tag) and tag.name in {"h2", "h3"}
        )
        if nearest_heading:
            heading_text = nearest_heading.get_text(" ", strip=True)
            if "一页必背版" in heading_text:
                table["class"] = table.get("class", []) + ["must-memorize-table"]
            elif "默写空表" in heading_text:
                table["class"] = table.get("class", []) + ["recall-table"]

    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text.endswith("：") and len(text) <= 18:
            p["class"] = p.get("class", []) + ["lead-label"]

    return str(soup), headings


def build_toc(headings: list[dict[str, str]]) -> str:
    items = []
    for item in headings:
        level_class = "toc-h2" if item["level"] == "h2" else "toc-h3"
        if item["level"] == "h3" and len(items) > 85:
            continue
        items.append(
            f'<a class="{level_class}" href="#{html.escape(item["id"])}">'
            f"<span>{html.escape(item['text'])}</span></a>"
        )
    return "\n".join(items)


def make_html(body_html: str, headings: list[dict[str, str]], source_name: str) -> str:
    today = dt.date.today().isoformat()
    section_count = sum(1 for h in headings if h["level"] == "h2")
    topic_count = sum(1 for h in headings if h["level"] == "h3")
    toc_html = build_toc(headings)

    css = r"""
@page {
  size: A4;
  margin: 18mm 15mm 18mm;
}

* {
  box-sizing: border-box;
}

html {
  font-size: 14px;
}

body {
  margin: 0;
  color: #1d2733;
  background: #fff;
  font-family: "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC", "PingFang SC", "SimSun", Arial, sans-serif;
  line-height: 1.58;
  font-variant-numeric: tabular-nums;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

a {
  color: inherit;
  text-decoration: none;
}

.cover {
  min-height: 258mm;
  padding: 26mm 20mm 16mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #f8fafc;
  background:
    linear-gradient(135deg, rgba(9, 44, 72, .96), rgba(14, 78, 92, .92)),
    linear-gradient(45deg, #0f2f4c, #185e67);
  page-break-after: always;
  position: relative;
  overflow: hidden;
}

.cover::before {
  content: "";
  position: absolute;
  inset: 16mm;
  border: 1px solid rgba(255, 255, 255, .24);
  pointer-events: none;
}

.cover::after {
  content: "";
  position: absolute;
  right: -35mm;
  bottom: -22mm;
  width: 115mm;
  height: 115mm;
  border: 18mm solid rgba(255, 255, 255, .08);
  transform: rotate(18deg);
}

.cover-top,
.cover-bottom {
  position: relative;
  z-index: 1;
}

.kicker {
  display: inline-block;
  padding: 5px 10px;
  border: 1px solid rgba(255, 255, 255, .38);
  color: #c7f3ff;
  font-size: 12px;
  letter-spacing: 1.5px;
}

.cover h1 {
  margin: 22mm 0 5mm;
  max-width: 150mm;
  font-size: 36px;
  line-height: 1.18;
  font-weight: 800;
  letter-spacing: 0;
}

.subtitle {
  margin: 0;
  font-size: 18px;
  color: #d9f2f7;
}

.cover-grid {
  margin-top: 22mm;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  max-width: 140mm;
}

.metric {
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, .24);
  background: rgba(255, 255, 255, .08);
}

.metric strong {
  display: block;
  font-size: 21px;
  color: #fff;
}

.metric span {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  color: #bfe9ef;
}

.cover-note {
  max-width: 145mm;
  color: #dceff4;
  font-size: 12.5px;
}

.document-meta {
  display: flex;
  gap: 16px;
  color: #c6dbe3;
  font-size: 11px;
}

.toc-page {
  page-break-after: always;
  padding-top: 1mm;
}

.toc-title {
  margin: 0 0 7mm;
  padding-bottom: 3mm;
  border-bottom: 2px solid #174a66;
  color: #173f5f;
  font-size: 24px;
}

.toc-grid {
  columns: 2;
  column-gap: 10mm;
}

.toc-grid a {
  display: block;
  break-inside: avoid;
  border-bottom: 1px solid #e2e8f0;
}

.toc-h2 {
  margin: 0 0 3px;
  padding: 6px 0 4px;
  color: #123b5d;
  font-weight: 700;
  font-size: 13.5px;
}

.toc-h3 {
  margin: 0;
  padding: 2px 0 2px 8px;
  color: #475569;
  font-size: 11.5px;
}

.main {
  counter-reset: chapter;
}

.main > blockquote:first-child {
  margin-top: 0;
}

h2 {
  counter-increment: chapter;
  margin: 0 0 6mm;
  padding: 0 0 4mm;
  color: #123b5d;
  border-bottom: 2px solid #b8d6e6;
  font-size: 23px;
  line-height: 1.32;
  page-break-before: always;
  break-after: avoid;
}

.main h2:first-of-type {
  page-break-before: auto;
}

h2::before {
  content: attr(data-section);
  display: inline-block;
  min-width: 10mm;
  margin-right: 4mm;
  padding: 1mm 2.2mm;
  color: #fff;
  background: #174a66;
  font-size: 13px;
  text-align: center;
  vertical-align: 2px;
}

h3 {
  margin: 7mm 0 3mm;
  padding-left: 4mm;
  color: #174a66;
  border-left: 4px solid #4f9db3;
  font-size: 16.2px;
  line-height: 1.38;
  break-after: avoid;
}

h4 {
  margin: 5mm 0 2mm;
  color: #334155;
  font-size: 14.2px;
  line-height: 1.36;
  break-after: avoid;
}

p {
  margin: 2.2mm 0;
}

.lead-label {
  margin: 4mm 0 1.5mm;
  color: #174a66;
  font-weight: 700;
}

blockquote {
  margin: 0 0 6mm;
  padding: 4mm 5mm;
  color: #243b53;
  background: #f1f7fb;
  border-left: 4px solid #4f9db3;
}

ul,
ol {
  margin: 2mm 0 4mm 6mm;
  padding: 0;
}

li {
  margin: 1.1mm 0;
  padding-left: 1mm;
}

hr {
  margin: 7mm 0;
  border: 0;
  border-top: 1px solid #d8e4ea;
}

strong {
  color: #172a3a;
}

code {
  padding: .2mm 1mm;
  border-radius: 2px;
  color: #0f3a4e;
  background: #eef6f8;
  font-family: Consolas, "Courier New", monospace;
  font-size: .92em;
}

pre {
  margin: 3mm 0 5mm;
  padding: 3.5mm 4mm;
  border: 1px solid #cbdde6;
  background: #f8fbfc;
  white-space: pre-wrap;
  word-break: break-word;
}

table {
  width: 100%;
  margin: 3mm 0 5mm;
  border-collapse: collapse;
  border-spacing: 0;
  page-break-inside: auto;
  break-inside: auto;
  color: #243447;
  font-size: 12.2px;
}

thead {
  display: table-header-group;
}

tr {
  page-break-inside: avoid;
  break-inside: avoid;
}

th,
td {
  border: 1px solid #c6d5de;
  padding: 2.4mm 2.5mm;
  vertical-align: top;
  word-break: break-word;
  overflow-wrap: anywhere;
}

th {
  color: #123b5d;
  background: #e5f1f6;
  font-weight: 700;
  text-align: left;
}

tbody tr:nth-child(even) td {
  background: #f8fbfc;
}

.profile-table,
.kv-table {
  table-layout: fixed;
}

.profile-table th:first-child,
.profile-table td:first-child,
.kv-table th:first-child,
.kv-table td:first-child {
  width: 26%;
  color: #173f5f;
  background: #f3f8fb;
  font-weight: 700;
}

.medium-table {
  table-layout: fixed;
}

.wide-table {
  table-layout: auto;
  font-size: 10.4px;
}

.wide-table th,
.wide-table td {
  padding: 1.8mm 1.6mm;
}

.must-memorize-table {
  font-size: 8.6px;
  line-height: 1.24;
  margin: 2mm 0 3mm;
}

.must-memorize-table th,
.must-memorize-table td {
  padding: 1mm 1.15mm;
}

.must-memorize-table th:nth-child(1),
.must-memorize-table td:nth-child(1) {
  width: 17%;
}

.must-memorize-table th:nth-child(2),
.must-memorize-table td:nth-child(2) {
  width: 28%;
}

.recall-table {
  font-size: 9.8px;
}

.recall-table th,
.recall-table td {
  padding: 1.6mm 1.5mm;
}

.study-table + p,
.study-table + ul,
.study-table + ol {
  margin-top: 2mm;
}

.main > p:first-child,
.main > blockquote:first-child {
  page-break-after: avoid;
}

@media print {
  h2,
  h3,
  h4 {
    break-after: avoid;
  }

  table,
  blockquote,
  pre {
    break-inside: auto;
  }
}
"""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{html.escape(TITLE)} - 高级版</title>
<style>{css}</style>
</head>
<body>
<section class="cover">
  <div class="cover-top">
    <div class="kicker">PHYSICS HISTORY REVIEW</div>
    <h1>{html.escape(TITLE)}</h1>
    <p class="subtitle">{html.escape(SUBTITLE)}</p>
    <div class="cover-grid">
      <div class="metric"><strong>{section_count}</strong><span>个主模块</span></div>
      <div class="metric"><strong>{topic_count}</strong><span>个细分条目</span></div>
      <div class="metric"><strong>A4</strong><span>打印友好版式</span></div>
    </div>
  </div>
  <div class="cover-bottom">
    <p class="cover-note">整理逻辑：人物与背景、实验装置、现象、推理、结论、意义、易混点和题干关键词。适合考前快速查漏、打印批注和按章节复习。</p>
    <div class="document-meta">
      <span>源文件：{html.escape(source_name)}</span>
      <span>生成日期：{today}</span>
    </div>
  </div>
</section>

<section class="toc-page">
  <h1 class="toc-title">目录</h1>
  <nav class="toc-grid">
    {toc_html}
  </nav>
</section>

<article class="main">
{body_html}
</article>
</body>
</html>"""


def export_pdf(chrome: Path, html_path: Path, pdf_path: Path) -> None:
    user_data = Path(tempfile.mkdtemp(prefix="codex-physics-pdf-"))
    try:
        uri = html_path.resolve().as_uri()
        cmd = [
            str(chrome),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--user-data-dir={user_data}",
            f"--print-to-pdf={pdf_path}",
            uri,
        ]
        subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(user_data, ignore_errors=True)


def add_pdf_footer(pdf_path: Path) -> None:
    doc = fitz.open(str(pdf_path))
    total = len(doc)
    for index, page in enumerate(doc):
        if index == 0:
            continue
        width = page.rect.width
        height = page.rect.height
        y = height - 27
        page.draw_line(
            fitz.Point(42, height - 38),
            fitz.Point(width - 42, height - 38),
            color=(0.78, 0.84, 0.88),
            width=0.45,
        )
        footer_title = "Physics History Review · Advanced Guide"
        page_no = f"{index + 1:02d} / {total:02d}"
        page.insert_text(
            fitz.Point(42, y),
            footer_title,
            fontsize=7.5,
            color=(0.32, 0.40, 0.48),
        )
        page.insert_text(
            fitz.Point(width - 75, y),
            page_no,
            fontsize=7.5,
            color=(0.32, 0.40, 0.48),
        )

    temp_path = pdf_path.with_name(f"{pdf_path.stem}.tmp{pdf_path.suffix}")
    doc.save(str(temp_path), garbage=4, deflate=True)
    doc.close()
    temp_path.replace(pdf_path)


def main() -> int:
    base = Path.cwd()
    md_path = find_source_md(base)
    html_path = base / f"{md_path.stem}_高级版.html"
    pdf_path = base / f"{md_path.stem}_高级版.pdf"

    md_text = md_path.read_text(encoding="utf-8-sig")
    soup = convert_markdown(md_text)
    body_html, headings = normalize_body(soup)
    html_doc = make_html(body_html, headings, md_path.name)
    html_path.write_text(html_doc, encoding="utf-8-sig")

    chrome = find_chrome()
    export_pdf(chrome, html_path, pdf_path)
    add_pdf_footer(pdf_path)

    print(f"HTML: {html_path}")
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
