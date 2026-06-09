from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz
import markdown


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
    raise FileNotFoundError("Chrome/Edge not found")


def make_html(md_text: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    css = """
@page { size: A4; margin: 14mm 12mm 15mm; }
* { box-sizing: border-box; }
body {
  margin: 0;
  color: #111827;
  background: #fff;
  font-family: "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC", Arial, sans-serif;
  font-size: 10.6px;
  line-height: 1.36;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
h1 {
  margin: 0 0 7mm;
  padding-bottom: 3mm;
  border-bottom: 1px solid #111827;
  font-size: 20px;
  line-height: 1.2;
}
h2 {
  margin: 6mm 0 2.5mm;
  padding: 1.5mm 0;
  border-top: 1px solid #9ca3af;
  border-bottom: 1px solid #d1d5db;
  font-size: 13px;
  line-height: 1.2;
  break-after: avoid;
}
table {
  width: 100%;
  margin: 0 0 4mm;
  border-collapse: collapse;
  table-layout: fixed;
  break-inside: auto;
}
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td {
  border: 1px solid #d1d5db;
  padding: 1.15mm 1.25mm;
  vertical-align: top;
  word-break: break-word;
  overflow-wrap: anywhere;
}
th {
  background: #f3f4f6;
  font-weight: 700;
  text-align: left;
}
p { margin: 2mm 0; }
"""
    today = dt.date.today().isoformat()
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>高中物理科学史</title>
<style>{css}</style>
</head>
<body>
{body}
<!-- generated: {today} -->
</body>
</html>
"""


def export_pdf(chrome: Path, html_path: Path, pdf_path: Path) -> None:
    user_data = Path(tempfile.mkdtemp(prefix="codex-skeleton-pdf-"))
    try:
        subprocess.run(
            [
                str(chrome),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--user-data-dir={user_data}",
                f"--print-to-pdf={pdf_path}",
                html_path.resolve().as_uri(),
            ],
            check=True,
        )
    finally:
        shutil.rmtree(user_data, ignore_errors=True)


def add_footer(pdf_path: Path) -> None:
    doc = fitz.open(str(pdf_path))
    total = len(doc)
    for index, page in enumerate(doc):
        width = page.rect.width
        height = page.rect.height
        page.draw_line(
            fitz.Point(36, height - 30),
            fitz.Point(width - 36, height - 30),
            color=(0.7, 0.7, 0.7),
            width=0.35,
        )
        page.insert_text(
            fitz.Point(width - 48, height - 18),
            f"{index + 1} / {total}",
            fontsize=7,
            color=(0.25, 0.25, 0.25),
        )
    temp_path = pdf_path.with_suffix(".tmp.pdf")
    doc.save(str(temp_path), garbage=4, deflate=True)
    doc.close()
    temp_path.replace(pdf_path)


def main() -> int:
    base = Path.cwd()
    md_path = base / "高中物理科学史_骨架版.md"
    html_path = base / "高中物理科学史_骨架版.html"
    pdf_path = base / "高中物理科学史_骨架版.pdf"

    md_text = md_path.read_text(encoding="utf-8-sig")
    html_path.write_text(make_html(md_text), encoding="utf-8-sig")
    export_pdf(find_chrome(), html_path, pdf_path)
    add_footer(pdf_path)
    print(f"HTML: {html_path}")
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
