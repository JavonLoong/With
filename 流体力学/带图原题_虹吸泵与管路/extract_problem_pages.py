from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


SOURCES = [
    {
        "name": "虹吸管_教材习题5-7",
        "pdf": ROOT / "张扬军（车辆学院）" / "教材" / "《流体力学》教材.pdf",
        "terms": ["5-7", "虹吸管", "汽化压强"],
    },
    {
        "name": "并联管路_教材例题9-8",
        "pdf": ROOT / "张扬军（车辆学院）" / "教材" / "《流体力学》教材.pdf",
        "terms": ["例题 9-8", "并联管路", "Q1 和 Q2"],
    },
    {
        "name": "泵吸水管最大安装高度_作业题2",
        "pdf": ROOT / "第5-8章作业与复习_整理" / "粘性流动作业-2" / "13_粘性流动作业-2_题目与答案.pdf",
        "terms": ["泵吸水管最大安装高度", "汽化压力", "最大安装高度"],
    },
    {
        "name": "水轮机输出功率_作业题3",
        "pdf": ROOT / "第5-8章作业与复习_整理" / "粘性流动作业-2" / "13_粘性流动作业-2_题目与答案.pdf",
        "terms": ["水轮机输出功率", "压力表读数", "上游水面"],
    },
]


def page_score(text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if term in text)


def render_page(doc: fitz.Document, page_index: int, stem: str) -> Path:
    page = doc[page_index]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
    path = OUT / f"{stem}_pdf第{page_index + 1}页.png"
    pix.save(path)
    return path


def render_neighbors(doc: fitz.Document, page_index: int, stem: str) -> list[Path]:
    paths = []
    for idx in range(max(0, page_index - 1), min(len(doc), page_index + 2)):
        paths.append(render_page(doc, idx, f"{stem}_邻近"))
    return paths


def main() -> None:
    lines = ["# 带图原题页提取索引", ""]
    for source in SOURCES:
        pdf = source["pdf"]
        terms = source["terms"]
        if not pdf.exists():
            lines.append(f"- {source['name']}：未找到 PDF：`{pdf}`")
            continue

        doc = fitz.open(pdf)
        scores = []
        for i, page in enumerate(doc):
            text = page.get_text()
            score = page_score(text, terms)
            if score:
                scores.append((score, i, text[:500].replace("\n", " ")))

        if not scores:
            lines.append(f"- {source['name']}：PDF 中未搜索到关键词 `{', '.join(terms)}`")
            continue

        scores.sort(reverse=True)
        _, page_index, snippet = scores[0]
        image = render_page(doc, page_index, source["name"])
        neighbor_images = []
        if source["name"].startswith("虹吸管"):
            neighbor_images = render_neighbors(doc, page_index, source["name"])
        lines.append(f"## {source['name']}")
        lines.append("")
        lines.append(f"- 来源 PDF：`{pdf}`")
        lines.append(f"- 命中 PDF 第 {page_index + 1} 页")
        lines.append(f"- 页图：`{image}`")
        if neighbor_images:
            lines.append("- 相邻页补充：")
            for neighbor in neighbor_images:
                lines.append(f"  - `{neighbor}`")
        lines.append(f"- 文本片段：{snippet}")
        lines.append("")

    (OUT / "00_带图原题页提取索引.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
