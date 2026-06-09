from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz
import markdown


SOURCE_NAME = "高中物理科学史可考细节汇总.md"
OUTPUT_STEM = "高中物理科学史_全面去包装版"


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


def clean_markdown(md_text: str) -> str:
    text = md_text.lstrip("\ufeff")

    text = re.sub(
        r"\n?> 适用目标：.*?\n> 使用方法：.*?\n\n",
        "\n\n",
        text,
        count=1,
        flags=re.S,
    )

    replacements = {
        "## 十三、最容易出错的判断题": "## 十三、易错判断题",
        "## 十四、考试复习建议": "## 十四、复习建议",
        "### 1. 背诵顺序": "### 1. 顺序",
        "### 2. 每个条目必须会答的 6 个问题": "### 2. 6 个问题",
        "### 3. 临考压缩版口诀": "### 3. 口诀",
        "## 十五、一页必背版": "## 十五、人物-关键词-结论-易错表",
        "## 十六、默写空表": "## 十六、训练空表",
        "## 十七、30 道判断训练题": "## 十七、判断训练题",
        "### 1. 题目区": "### 1. 题目",
        "### 2. 答案区": "### 2. 答案",
        "## 十八、后续可补充区": "## 十八、补充项",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    removable_paragraphs = [
        r"使用方法：先盖住“必记结论”和“易错反向表述”，只看“人物”和“题干关键词”默背。能把最后两列说准，科学史选择题基本不会大面积丢分。\n\n",
        r"使用方法：第一次只填“人物/对象”；第二次把“实验或现象”和“结论”都填出；第三次专门补“易错点”。填完后回看上一节一页必背版和前文详细条目。\n\n",
        r"做题方法：先只判断“对/错/不严谨”，不要急着看答案。科学史题最常考的不是生僻年份，而是“谁提出、谁验证、实验能直接推出什么、不能推出什么”。\n\n",
    ]
    for paragraph in removable_paragraphs:
        text = re.sub(paragraph, "", text)

    text = text.replace("一页必背版", "人物-关键词-结论-易错表")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def make_html(md_text: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        output_format="html5",
    )
    css = """
@page { size: A4; margin: 15mm 13mm 16mm; }
* { box-sizing: border-box; }
body {
  margin: 0;
  color: #111827;
  background: #fff;
  font-family: "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC", Arial, sans-serif;
  font-size: 12px;
  line-height: 1.52;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
h1 {
  margin: 0 0 8mm;
  padding-bottom: 3mm;
  border-bottom: 1.5px solid #111827;
  font-size: 24px;
  line-height: 1.25;
}
h2 {
  margin: 8mm 0 4mm;
  padding: 2mm 0 2mm;
  border-top: 1px solid #9ca3af;
  border-bottom: 1px solid #d1d5db;
  font-size: 17px;
  line-height: 1.28;
  break-after: avoid;
}
h3 {
  margin: 5mm 0 2.5mm;
  font-size: 14px;
  line-height: 1.3;
  break-after: avoid;
}
h4 {
  margin: 4mm 0 2mm;
  font-size: 12.5px;
  line-height: 1.3;
  break-after: avoid;
}
p { margin: 2mm 0; }
ul, ol { margin: 1.5mm 0 4mm 6mm; padding: 0; }
li { margin: 1mm 0; }
table {
  width: 100%;
  margin: 2.5mm 0 5mm;
  border-collapse: collapse;
  table-layout: fixed;
  break-inside: auto;
  font-size: 10.8px;
}
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td {
  border: 1px solid #d1d5db;
  padding: 1.8mm 1.9mm;
  vertical-align: top;
  word-break: break-word;
  overflow-wrap: anywhere;
}
th {
  background: #f3f4f6;
  font-weight: 700;
  text-align: left;
}
tbody tr:nth-child(even) td { background: #fafafa; }
blockquote {
  margin: 2mm 0 4mm;
  padding: 3mm 4mm;
  border-left: 3px solid #9ca3af;
  background: #f9fafb;
}
code {
  font-family: Consolas, "Courier New", monospace;
  font-size: .92em;
}
hr {
  margin: 6mm 0;
  border: 0;
  border-top: 1px solid #d1d5db;
}
"""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{OUTPUT_STEM}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def export_pdf(chrome: Path, html_path: Path, pdf_path: Path) -> None:
    user_data = Path(tempfile.mkdtemp(prefix="codex-clean-pdf-"))
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
            fitz.Point(38, height - 30),
            fitz.Point(width - 38, height - 30),
            color=(0.7, 0.7, 0.7),
            width=0.35,
        )
        page.insert_text(
            fitz.Point(width - 52, height - 18),
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
    source_path = base / SOURCE_NAME
    md_path = base / f"{OUTPUT_STEM}.md"
    html_path = base / f"{OUTPUT_STEM}.html"
    pdf_path = base / f"{OUTPUT_STEM}.pdf"

    cleaned = clean_markdown(source_path.read_text(encoding="utf-8-sig"))
    md_path.write_text(cleaned, encoding="utf-8-sig")
    html_path.write_text(make_html(cleaned), encoding="utf-8-sig")
    export_pdf(find_chrome(), html_path, pdf_path)
    add_footer(pdf_path)

    print(f"MD: {md_path}")
    print(f"HTML: {html_path}")
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
