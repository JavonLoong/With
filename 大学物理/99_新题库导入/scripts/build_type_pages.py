from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import pdfplumber


ROOT = Path(r"D:\虚拟C盘\学习\大学物理")
PRIMARY = ROOT / r"99_新题库导入\source_extracted\大学物理2\大学物理2\期末\量子和光"
OUT_DIR = ROOT / r"99_新题库导入\processed"
NAV_DIR = ROOT / r"00_导航与计划"


CATEGORIES = [
    {
        "id": "01_interference_young",
        "title": "01 干涉：光程差、双缝、相干性",
        "formula": [
            "Δφ = 2πδ/λ",
            "δ = d sinθ ≈ dx/D",
            "Δx = λD/d",
            "介质片额外光程差：Δ = (n - 1)e",
        ],
        "action": "先写光程差 δ，再按明纹 δ=kλ、暗纹 δ=(k+1/2)λ 判断。",
        "keywords": ["光程", "相位差", "双缝", "相干", "条纹间距", "杨氏", "劳埃德", "介质板", "光源宽度", "白光", "缝宽"],
    },
    {
        "id": "02_interference_film_michelson",
        "title": "02 干涉：薄膜、等厚、迈克耳孙",
        "formula": [
            "薄膜正入射几何光程差：2ne",
            "先判断半波损失，再定明暗条件",
            "劈尖相邻条纹厚度差：Δe=λ/(2n)",
            "迈克耳孙：2Δd=Nλ",
        ],
        "action": "薄膜题第一步永远先判半波损失；动镜题永远先写 2Δd=Nλ。",
        "keywords": ["薄膜", "增透", "劈尖", "牛顿环", "等厚", "迈克耳孙", "Michelson", "动镜", "反射镜", "膜厚", "半波损失", "空气膜"],
    },
    {
        "id": "03_diffraction_single_slit_rayleigh",
        "title": "03 衍射：单缝、圆孔、瑞利判据",
        "formula": [
            "单缝暗纹：a sinθ=kλ, k=1,2,...",
            "中央明纹角宽：Δθ≈2λ/a",
            "透镜焦平面中央明纹宽：Δx≈2fλ/a",
            "瑞利判据：θ_min=1.22λ/D",
        ],
        "action": "看到单缝先找暗纹级次；看到望远镜/圆孔先用 1.22λ/D。",
        "keywords": ["单缝", "中央明纹", "暗纹", "夫琅禾费", "圆孔", "瑞利", "望远镜", "孔径", "分辨角", "分辨率"],
    },
    {
        "id": "04_diffraction_grating_missing_order",
        "title": "04 衍射：光栅、缺级、分辨本领",
        "formula": [
            "光栅主极大：d sinθ=kλ",
            "缺级联立：d sinθ=kλ 与 a sinθ=mλ",
            "最高级次：abs(k)≤d/λ",
            "分辨本领：R=λ/Δλ=kN",
        ],
        "action": "最高级次看 sinθ≤1；缺级题把光栅主极大和单缝暗纹联立。",
        "keywords": ["光栅", "缺级", "主极大", "谱线", "刻线", "栅距", "分辨本领", "色散", "缝数"],
    },
    {
        "id": "05_bragg_xray_electron_diffraction",
        "title": "05 布拉格、X 射线、电子衍射",
        "formula": [
            "布拉格：2d sinφ=kλ",
            "φ 是入射线与晶面的掠射角",
            "若给法线夹角，要先换成 90°-θ",
            "电子德布罗意波长：λ=h/p",
        ],
        "action": "先判断题给的是掠射角还是法线角，再代布拉格公式。",
        "keywords": ["布拉格", "X射线", "X 射线", "晶体", "晶格", "电子衍射", "掠射角", "晶面", "衍射极大"],
    },
    {
        "id": "06_polarization_intensity_brewster",
        "title": "06 偏振：强度链、偏振度、布儒斯特角",
        "formula": [
            "自然光过第一片：I1=I0/2",
            "马吕斯定律：I=I_in cos²α",
            "偏振度：P=(Imax-Imin)/(Imax+Imin)",
            "布儒斯特：tan i_B=n2/n1, 且 i_B+r=90°",
        ],
        "action": "第一片只有自然光才除 2；后续只乘 cos²。布儒斯特题要画法线和折射角。",
        "keywords": ["自然光", "偏振片", "马吕斯", "检偏", "起偏", "布儒斯特", "反射完全偏振", "偏振度", "部分偏振", "光强", "透射光"],
    },
    {
        "id": "07_polarization_birefringence_waveplate",
        "title": "07 偏振：双折射、波片、旋光",
        "formula": [
            "波片相位差：Δφ=2π(n_o-n_e)d/λ",
            "四分之一波片：abs(Δφ)=π/2",
            "二分之一波片：abs(Δφ)=π",
            "旋光：θ=αl 或按题给旋光率",
        ],
        "action": "波片只改相位差；双折射题先判光轴、o/e 光和振动方向。",
        "keywords": ["双折射", "o光", "e光", "o 光", "e 光", "方解石", "波片", "四分之一", "二分之一", "光轴", "旋光", "晶片", "椭圆偏振", "圆偏振"],
    },
    {
        "id": "08_quantum_blackbody_photoelectric",
        "title": "08 量子：黑体辐射、光电效应",
        "formula": [
            "维恩：λ_m T=b",
            "斯特藩：M=σT⁴",
            "光电效应：hν=W+Kmax=W+eU_s",
            "红限：ν0=W/h, λ0=hc/W",
        ],
        "action": "黑体题先区分峰值波长和总辐出度；光电题先写爱因斯坦方程。",
        "keywords": ["黑体", "维恩", "斯特藩", "光电", "逸出", "截止", "遏止", "红限", "饱和电流", "光电子"],
    },
    {
        "id": "09_quantum_compton_debroglie_uncertainty",
        "title": "09 量子：康普顿、德布罗意、不确定关系",
        "formula": [
            "康普顿：Δλ=λ_C(1-cosφ)",
            "光子：E=hν=hc/λ, p=h/λ",
            "德布罗意：λ=h/p",
            "不确定关系：ΔxΔp≥ℏ/2",
        ],
        "action": "散射角用康普顿；电子加速用德布罗意；问最小不确定量用不确定关系。",
        "keywords": ["康普顿", "散射", "德布罗意", "物质波", "不确定", "电子加速", "光子", "动量", "反冲电子"],
    },
    {
        "id": "10_quantum_wavefunction_schrodinger_well",
        "title": "10 量子：波函数、薛定谔、势阱、本征态",
        "formula": [
            "概率密度：ρ=abs(Ψ)²",
            "归一化：∫abs(Ψ)² dx=1",
            "无限深势阱：ψ_n=√(2/a)sin(nπx/a)",
            "能级：E_n=n²h²/(8ma²)",
        ],
        "action": "看到三角函数展开动量本征态；看到势阱先写边界条件和标准本征函数。",
        "keywords": ["波函数", "薛定谔", "归一化", "概率密度", "无限深", "势阱", "势垒", "本征", "动量本征", "谐振子", "隧道"],
    },
    {
        "id": "11_atomic_quantum_numbers_laser_solid",
        "title": "11 原子：氢原子、量子数、激光、固体",
        "formula": [
            "氢原子：E_n=-13.6/n² eV",
            "跃迁：hν=abs(E_i-E_f)",
            "量子数：n; l=0...n-1; m_l=-l...l; m_s=±1/2",
            "壳层容量：2n²",
        ],
        "action": "氢原子题先写能级差；量子数题先检查取值范围；激光题背三条件。",
        "keywords": ["氢原子", "能级", "量子数", "泡利", "角动量", "自旋", "激光", "受激", "粒子数反转", "固体", "能带", "禁带", "壳层", "支壳层"],
    },
]


QUESTION_RE = re.compile(r"(?m)^\s*(\d+)\.\s*\(本题\s*(\d+)\s*分\)\((\d+)\)")
HEADING_RE = re.compile(r"(一\s*选择题|二\s*填空题|三\s*计算题|四\s*问答题|一、选择题|二、填空题|三、计算题|四、问答题)")


@dataclass
class Record:
    category_id: str
    category_title: str
    source_file: str
    source_page: int
    number: int
    score: int
    bank_id: str
    qtype: str
    question: str
    answer: str


def read_pdf_text(path: Path) -> tuple[str, list[tuple[int, int, int]]]:
    parts: list[str] = []
    spans: list[tuple[int, int, int]] = []
    pos = 0
    with pdfplumber.open(path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            chunk = f"\n[[PAGE {page_no}]]\n{text}\n"
            start = pos
            parts.append(chunk)
            pos += len(chunk)
            spans.append((start, pos, page_no))
    return "".join(parts), spans


def page_for_pos(spans: list[tuple[int, int, int]], pos: int) -> int:
    for start, end, page_no in spans:
        if start <= pos < end:
            return page_no
    return spans[-1][2] if spans else 1


def clean_block(text: str) -> str:
    text = re.sub(r"\[\[PAGE\s+\d+\]\]", "", text)
    text = re.sub(r"\n第\s*\d+\s*页\s*\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def qtype_for_pos(text: str, pos: int) -> str:
    last = "题目"
    for m in HEADING_RE.finditer(text[:pos]):
        heading = m.group(1)
        if "选择" in heading:
            last = "选择题"
        elif "填空" in heading:
            last = "填空题"
        elif "计算" in heading:
            last = "计算题"
        elif "问答" in heading:
            last = "问答题"
    return last


def split_items(text: str, spans: list[tuple[int, int, int]]) -> dict[int, dict]:
    matches = list(QUESTION_RE.finditer(text))
    items: dict[int, dict] = {}
    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        number = int(m.group(1))
        score = int(m.group(2))
        bank_id = m.group(3)
        block = clean_block(text[start:end])
        items[number] = {
            "number": number,
            "score": score,
            "bank_id": bank_id,
            "qtype": qtype_for_pos(text, start),
            "page": page_for_pos(spans, start),
            "block": block,
        }
    return items


def answer_path_for(question_path: Path) -> Path | None:
    stem = question_path.stem
    candidates = [
        question_path.with_name(stem + "答案.pdf"),
        question_path.with_name(stem + "_答案.pdf"),
        question_path.with_name(stem + " 答案.pdf"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def classify(source_name: str, question: str) -> dict:
    hay = source_name + "\n" + question
    scores: list[tuple[int, int, dict]] = []
    for idx, cat in enumerate(CATEGORIES):
        score = sum(1 for kw in cat["keywords"] if kw in hay)
        scores.append((score, -idx, cat))
    scores.sort(reverse=True)
    best = scores[0][2] if scores[0][0] > 0 else CATEGORIES[-1]

    # File-level nudges for broad source files.
    if "干涉" in source_name and best["id"].startswith(("03", "04", "05", "06", "07", "08", "09", "10", "11")):
        best = CATEGORIES[1] if any(k in hay for k in ["薄膜", "劈尖", "牛顿环", "迈克耳孙"]) else CATEGORIES[0]
    if "衍射" in source_name and best["id"].startswith(("01", "02", "06", "07", "08", "09", "10", "11")):
        best = CATEGORIES[4] if any(k in hay for k in ["布拉格", "X射线", "X 射线", "晶体"]) else (CATEGORIES[3] if "光栅" in hay else CATEGORIES[2])
    if "偏振" in source_name and not best["id"].startswith(("06", "07")):
        best = CATEGORIES[6] if any(k in hay for k in ["双折射", "波片", "方解石", "旋光", "光轴"]) else CATEGORIES[5]
    if "量子" in source_name and best["id"].startswith(("01", "02", "03", "04", "05", "06", "07")):
        if any(k in hay for k in ["黑体", "光电", "红限", "逸出"]):
            best = CATEGORIES[7]
        elif any(k in hay for k in ["康普顿", "德布罗意", "不确定", "散射"]):
            best = CATEGORIES[8]
        elif any(k in hay for k in ["波函数", "薛定谔", "势阱", "本征"]):
            best = CATEGORIES[9]
        else:
            best = CATEGORIES[10]
    if "激光" in source_name:
        best = CATEGORIES[10]
    return best


def collect_records() -> list[Record]:
    records: list[Record] = []
    question_pdfs = sorted(
        p for p in PRIMARY.glob("*.pdf")
        if "答案" not in p.stem and "_答案" not in p.stem
    )
    for qpdf in question_pdfs:
        apdf = answer_path_for(qpdf)
        qtext, qspans = read_pdf_text(qpdf)
        qitems = split_items(qtext, qspans)
        aitems = {}
        if apdf:
            atext, aspans = read_pdf_text(apdf)
            aitems = split_items(atext, aspans)
        for number, q in qitems.items():
            answer = aitems.get(number, {}).get("block", "")
            cat = classify(qpdf.name, q["block"])
            records.append(
                Record(
                    category_id=cat["id"],
                    category_title=cat["title"],
                    source_file=str(qpdf),
                    source_page=q["page"],
                    number=q["number"],
                    score=q["score"],
                    bank_id=q["bank_id"],
                    qtype=q["qtype"],
                    question=q["block"],
                    answer=answer,
                )
            )
    return records


def rel(path: str | Path, base: Path) -> str:
    p = Path(path)
    return os.path.relpath(p, base).replace(os.sep, "/")


def render_html(records: list[Record]) -> str:
    by_cat: dict[str, list[Record]] = {cat["id"]: [] for cat in CATEGORIES}
    for r in records:
        by_cat.setdefault(r.category_id, []).append(r)

    nav = []
    sections = []
    total = len(records)
    for cat in CATEGORIES:
        recs = by_cat.get(cat["id"], [])
        calc_count = sum(1 for r in recs if r.qtype == "计算题")
        nav.append(
            f'<a href="#{cat["id"]}"><span>{html.escape(cat["title"])}</span><b>{len(recs)}</b></a>'
        )
        formulas = "".join(f"<li>{html.escape(x)}</li>" for x in cat["formula"])
        cards = []
        ordered = sorted(
            recs,
            key=lambda r: (0 if r.qtype == "计算题" else 1 if r.qtype == "填空题" else 2, r.source_file, r.number),
        )
        for r in ordered:
            src_rel = html.escape(f"{rel(r.source_file, NAV_DIR)}#page={r.source_page}")
            q = html.escape(r.question)
            a = html.escape(r.answer or "答案源中未抽到对应条目；先按题干来源回原 PDF 查看，后续补人工答案。")
            badge = "calc" if r.qtype == "计算题" else "fill" if r.qtype == "填空题" else "choice"
            cards.append(
                f"""
                <article class="qcard {badge}">
                  <header>
                    <div>
                      <strong>{html.escape(r.qtype)} #{r.number}</strong>
                      <span>题库ID {html.escape(r.bank_id)} / {r.score} 分 / 源页 {r.source_page}</span>
                    </div>
                    <a href="{src_rel}">打开原 PDF</a>
                  </header>
                  <section class="question"><pre>{q}</pre></section>
                  <section class="answer"><h4>标准答案/解法</h4><pre>{a}</pre></section>
                </article>
                """
            )
        sections.append(
            f"""
            <section id="{cat["id"]}" class="page">
              <div class="page-head">
                <p class="eyebrow">本页 {len(recs)} 题，其中计算题 {calc_count} 题</p>
                <h2>{html.escape(cat["title"])}</h2>
                <p>{html.escape(cat["action"])}</p>
                <ul>{formulas}</ul>
              </div>
              <div class="cards">{''.join(cards)}</div>
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>大学物理2期末新题库同类题11页速刷</title>
  <style>
    :root {{
      --ink: #152033;
      --muted: #64748b;
      --line: #d8e0ea;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --accent: #0f766e;
      --accent2: #b45309;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      line-height: 1.55;
    }}
    .shell {{
      display: grid;
      grid-template-columns: 310px minmax(0, 1fr);
      min-height: 100vh;
    }}
    nav {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 22px 18px;
      background: #101827;
      color: #fff;
    }}
    nav h1 {{
      font-size: 22px;
      line-height: 1.25;
      margin: 0 0 8px;
    }}
    nav p {{
      margin: 0 0 18px;
      color: #cbd5e1;
      font-size: 14px;
    }}
    nav a {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 12px;
      margin: 6px 0;
      color: #eef2ff;
      text-decoration: none;
      border: 1px solid rgba(255,255,255,.12);
      background: rgba(255,255,255,.04);
      border-radius: 8px;
      font-size: 14px;
    }}
    nav a b {{
      color: #fbbf24;
      font-weight: 700;
    }}
    main {{
      padding: 28px;
    }}
    .intro, .page {{
      max-width: 1180px;
      margin: 0 auto 28px;
    }}
    .intro {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 26px;
    }}
    .intro h2 {{
      margin: 0 0 10px;
      font-size: 30px;
    }}
    .page-head {{
      background: var(--panel);
      border-left: 6px solid var(--accent);
      border-top: 1px solid var(--line);
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px 22px;
      margin-bottom: 14px;
    }}
    .page-head h2 {{
      margin: 0 0 8px;
      font-size: 25px;
    }}
    .page-head ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 8px 18px;
      margin: 12px 0 0;
      padding-left: 20px;
    }}
    .eyebrow {{
      color: var(--accent);
      font-weight: 700;
      margin: 0 0 6px;
    }}
    .qcard {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 12px 0;
      overflow: hidden;
    }}
    .qcard.calc {{
      border-left: 6px solid var(--accent2);
    }}
    .qcard.fill {{
      border-left: 6px solid #2563eb;
    }}
    .qcard.choice {{
      border-left: 6px solid #64748b;
    }}
    .qcard header {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      padding: 12px 16px;
      background: #eef2f7;
      border-bottom: 1px solid var(--line);
    }}
    .qcard header span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-top: 2px;
    }}
    .qcard header a {{
      flex: 0 0 auto;
      color: var(--accent);
      font-weight: 700;
      text-decoration: none;
      font-size: 14px;
    }}
    .question, .answer {{
      padding: 14px 16px;
    }}
    .answer {{
      border-top: 1px solid var(--line);
      background: #fbfcfe;
    }}
    .answer h4 {{
      margin: 0 0 8px;
      color: var(--accent2);
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      font-size: 15px;
    }}
    @media (max-width: 900px) {{
      .shell {{ display: block; }}
      nav {{ position: relative; height: auto; }}
      main {{ padding: 16px; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <nav>
      <h1>大学物理2期末<br>同类题 11 页速刷</h1>
      <p>严格按波动光学、量子物理范围抽取。共 {total} 题。计算题优先放在每页前面。</p>
      {''.join(nav)}
    </nav>
    <main>
      <section class="intro">
        <h2>使用方法</h2>
        <p>每一页只练同一种模型：先背页首公式，再看题干，最后对标准答案。大题按答案区步骤抄写，应保留公式、代入、单位和结论。</p>
        <p>来源主库：{html.escape(str(PRIMARY))}</p>
      </section>
      {''.join(sections)}
    </main>
  </div>
</body>
</html>"""


def render_md_summary(records: list[Record]) -> str:
    by_cat: dict[str, list[Record]] = {cat["id"]: [] for cat in CATEGORIES}
    for r in records:
        by_cat.setdefault(r.category_id, []).append(r)
    rows = []
    for cat in CATEGORIES:
        recs = by_cat.get(cat["id"], [])
        rows.append(
            f"| {cat['title']} | {len(recs)} | {sum(1 for r in recs if r.qtype == '计算题')} | {cat['action']} |"
        )
    return "\n".join(
        [
            "# 大学物理2期末新题库同类题抽取索引",
            "",
            "来源：`D:\\虚拟C盘\\学习\\大学物理\\99_新题库导入\\source_extracted\\大学物理2\\大学物理2\\期末\\量子和光`",
            "",
            f"总题数：{len(records)}",
            "",
            "| 页面 | 题数 | 计算题数 | 做题动作 |",
            "|---|---:|---:|---|",
            *rows,
            "",
            "主复习入口：",
            "",
            "[大学物理2期末新题库同类题11页速刷.html](大学物理2期末新题库同类题11页速刷.html)",
            "",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = collect_records()

    json_path = OUT_DIR / "大学物理2期末新题库同类题_records.json"
    json_path.write_text(json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2), encoding="utf-8")

    html_path = NAV_DIR / "大学物理2期末新题库同类题11页速刷.html"
    html_path.write_text(render_html(records), encoding="utf-8")

    md_path = NAV_DIR / "大学物理2期末新题库同类题抽取索引.md"
    md_path.write_text(render_md_summary(records), encoding="utf-8")

    print(f"records={len(records)}")
    print(json_path)
    print(html_path)
    print(md_path)
    counts: dict[str, int] = {}
    calcs: dict[str, int] = {}
    for r in records:
        counts[r.category_title] = counts.get(r.category_title, 0) + 1
        if r.qtype == "计算题":
            calcs[r.category_title] = calcs.get(r.category_title, 0) + 1
    for cat in CATEGORIES:
        print(f"{cat['title']}: {counts.get(cat['title'], 0)} total, {calcs.get(cat['title'], 0)} calc")


if __name__ == "__main__":
    main()
