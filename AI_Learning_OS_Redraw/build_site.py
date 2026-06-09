"""读 <workdir>/content/*.json + <workdir>/illustrations/* 渲染成单文件 HTML。

使用 B 模板（统一现代模板），所有图片以 base64 内嵌，单文件可分享。
"""
from __future__ import annotations
import argparse
import base64
import html
import json
import re
from pathlib import Path

PAGE_RE = re.compile(r"p(\d+)")


def page_num(s: str) -> int:
    m = PAGE_RE.match(s)
    return int(m.group(1)) if m else 9999


def b64_img(p: Path) -> str:
    if not p.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"


def emphasize(text: str, words: list[str]) -> str:
    """把 quote 里的关键词包成 <span class=em>。"""
    if not text:
        return ""
    out = html.escape(text)
    for w in sorted(words or [], key=len, reverse=True):
        ew = html.escape(w)
        out = out.replace(ew, f'<span class="em">{ew}</span>')
    return out


# --------- 各 layout 模板 ----------
def render_two_card(data: dict, illus: list[str]) -> str:
    cards_html = []
    for i, c in enumerate(data.get("cards") or []):
        feat = "featured" if c.get("featured") else ""
        img_src = illus[i] if i < len(illus) else ""
        cards_html.append(f"""
        <article class="card {feat}">
          <div class="ckey">{html.escape(c.get('key',''))}</div>
          <h2>{html.escape(c.get('title',''))}</h2>
          <div class="desc">{html.escape(c.get('desc',''))}</div>
          <div class="illu">{f'<img src="{img_src}" alt="">' if img_src else ''}</div>
        </article>""")
    return f"""
      <header class="head">
        {f'<span class="tag">{html.escape(data.get("section_tag",""))}</span>' if data.get("section_tag") else ''}
        <h1>{html.escape(data.get('page_title',''))}</h1>
      </header>
      <section class="grid grid-2">{''.join(cards_html)}</section>
      {render_quote(data)}"""


def render_three_card(data: dict, illus: list[str]) -> str:
    cards_html = []
    for i, c in enumerate(data.get("cards") or []):
        feat = "featured" if c.get("featured") else ""
        img_src = illus[i] if i < len(illus) else ""
        cards_html.append(f"""
        <article class="card {feat}">
          <div class="ckey">{html.escape(c.get('key',''))}</div>
          <h2>{html.escape(c.get('title',''))}</h2>
          <div class="desc">{html.escape(c.get('desc',''))}</div>
          <div class="illu">{f'<img src="{img_src}" alt="">' if img_src else ''}</div>
        </article>""")
    return f"""
      <header class="head">
        {f'<span class="tag">{html.escape(data.get("section_tag",""))}</span>' if data.get("section_tag") else ''}
        <h1>{html.escape(data.get('page_title',''))}</h1>
      </header>
      <section class="grid grid-3">{''.join(cards_html)}</section>
      {render_quote(data)}"""


def render_one_illu(data: dict, illus: list[str]) -> str:
    c = (data.get("cards") or [{}])[0]
    img_src = illus[0] if illus else ""
    return f"""
      <header class="head">
        {f'<span class="tag">{html.escape(data.get("section_tag",""))}</span>' if data.get("section_tag") else ''}
        <h1>{html.escape(data.get('page_title',''))}</h1>
      </header>
      <section class="one-illu">
        <div class="illu-big">{f'<img src="{img_src}" alt="">' if img_src else ''}</div>
        {f'<div class="caption">{html.escape(c.get("desc",""))}</div>' if c.get("desc") else ''}
      </section>
      {render_quote(data)}"""


def render_full_image(data: dict, illus: list[str]) -> str:
    img_src = illus[0] if illus else ""
    return f"""
      <section class="full-image">
        {f'<img src="{img_src}" alt="">' if img_src else ''}
      </section>"""


def render_cover(data: dict, illus: list[str]) -> str:
    img_src = illus[0] if illus else ""
    return f"""
      <section class="cover">
        <div class="cover-text">
          {f'<div class="cover-tag">{html.escape(data.get("section_tag",""))}</div>' if data.get("section_tag") else ''}
          <h1 class="cover-title">{html.escape(data.get('page_title',''))}</h1>
          {f'<div class="cover-sub">{emphasize(data.get("quote",""), data.get("quote_emphasis") or [])}</div>' if data.get('quote') else ''}
        </div>
        {f'<div class="cover-illu"><img src="{img_src}" alt=""></div>' if img_src else ''}
      </section>"""


def render_section(data: dict, illus: list[str]) -> str:
    return f"""
      <section class="section-divider">
        <div class="section-tag-big">{html.escape(data.get("section_tag",""))}</div>
        <h1 class="section-title">{html.escape(data.get('page_title',''))}</h1>
        {f'<div class="section-sub">{emphasize(data.get("quote",""), data.get("quote_emphasis") or [])}</div>' if data.get('quote') else ''}
      </section>"""


def render_closing(data: dict, illus: list[str]) -> str:
    img_src = illus[0] if illus else ""
    return f"""
      <section class="closing">
        {f'<div class="closing-illu"><img src="{img_src}" alt=""></div>' if img_src else ''}
        <div class="closing-quote">{emphasize(data.get('quote') or data.get('page_title',''), data.get('quote_emphasis') or [])}</div>
      </section>"""


def render_comparison(data: dict, illus: list[str]) -> str:
    # 类似 two-card 但表格化
    cards_html = []
    for i, c in enumerate(data.get("cards") or []):
        feat = "featured" if c.get("featured") else ""
        img_src = illus[i] if i < len(illus) else ""
        cards_html.append(f"""
        <article class="card cmp {feat}">
          <div class="ckey">{html.escape(c.get('key',''))}</div>
          <h2>{html.escape(c.get('title',''))}</h2>
          <div class="desc">{html.escape(c.get('desc',''))}</div>
          <div class="illu">{f'<img src="{img_src}" alt="">' if img_src else ''}</div>
        </article>""")
    return f"""
      <header class="head">
        {f'<span class="tag">{html.escape(data.get("section_tag",""))}</span>' if data.get("section_tag") else ''}
        <h1>{html.escape(data.get('page_title',''))}</h1>
      </header>
      <section class="grid grid-2 cmp-grid">{''.join(cards_html)}</section>
      {render_quote(data)}"""


def render_quote(data: dict) -> str:
    q = data.get("quote")
    if not q:
        return ""
    return f'<footer class="quote">{emphasize(q, data.get("quote_emphasis") or [])}</footer>'


LAYOUT_RENDERERS = {
    "two-card": render_two_card,
    "three-card": render_three_card,
    "one-illu": render_one_illu,
    "full-image": render_full_image,
    "cover": render_cover,
    "section": render_section,
    "closing": render_closing,
    "comparison": render_comparison,
}


def render_slide(data: dict, workdir: Path) -> str:
    layout = data.get("layout", "two-card")
    illu_dir = workdir / "illustrations"
    n_cards = len(data.get("cards") or [])
    illus = []
    if layout in ("cover", "section", "closing", "one-illu", "full-image"):
        # 这些可能用同一张大图，从 cards[0] 或直接 page-level 读
        p_illu = illu_dir / f"{data['page']}_card1.png"
        if p_illu.exists():
            illus = [b64_img(p_illu)]
    else:
        for i in range(n_cards):
            p = illu_dir / f"{data['page']}_card{i+1}.png"
            illus.append(b64_img(p))

    body = LAYOUT_RENDERERS.get(layout, render_two_card)(data, illus)
    layout_class = f"layout-{layout}"
    return f'<div class="slide {layout_class}" data-page="{html.escape(data["page"])}">{body}</div>'


HTML_SHELL = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root {{
    --fg: #0a0a0a;
    --muted: #71717a;
    --line: #e4e4e7;
    --accent: #6b3fa0;
    --accent-soft: #ede9fe;
    --bg: #0a0a0c;
    --slide-bg: #fff;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin:0; padding:0; height:100%; background:var(--bg); color:#e4e4e7; font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; overflow:hidden; }}

  /* ---- 翻页舞台 ---- */
  .stage {{ position:fixed; inset:0; display:flex; align-items:center; justify-content:center; padding:0; overflow:hidden; }}
  .slide-wrap {{ width:1280px; height:720px; transform-origin: center center; transform: scale(var(--scale, 1)); }}
  .slide {{
    width: 1280px; height: 720px;
    background: var(--slide-bg); color: var(--fg);
    border-radius: 14px; box-shadow: 0 30px 80px -20px rgba(0,0,0,.6);
    padding: 40px 56px 28px;
    display: grid; grid-template-rows: auto 1fr auto;
    overflow: hidden;
  }}
  .slide.layout-cover, .slide.layout-section, .slide.layout-closing, .slide.layout-full-image {{
    grid-template-rows: 1fr;
  }}
  .slide.layout-full-image {{ padding: 0; }}

  /* ---- 通用头部 ---- */
  .head {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 14px; margin-bottom: 18px; }}
  .tag {{ font-size:12px; font-weight:600; letter-spacing:2px; color:var(--accent); text-transform:uppercase; padding:4px 12px; background:var(--accent-soft); border-radius:999px; }}
  .head h1 {{ margin:0; font-size:28px; font-weight:700; letter-spacing:0.5px; line-height:1.3; }}

  /* ---- 卡片网格 ---- */
  .grid {{ display: grid; gap: 24px; min-height: 0; }}
  .grid-2 {{ grid-template-columns: 1fr 1fr; }}
  .grid-3 {{ grid-template-columns: 1fr 1fr 1fr; }}
  .card {{
    border:1px solid var(--line); border-radius:10px; padding:18px 22px;
    display:flex; flex-direction:column; background:#fff; overflow:hidden; min-height:0;
  }}
  .card.featured {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }}
  .card .ckey {{ font-size:11px; font-weight:700; letter-spacing:2px; color:var(--muted); text-transform:uppercase; }}
  .card.featured .ckey {{ color: var(--accent); }}
  .card h2 {{ margin:4px 0 4px; font-size:21px; font-weight:700; }}
  .card .desc {{ font-size:13px; color:var(--muted); line-height:1.55; margin-bottom:6px; }}
  .card .illu {{ flex:1; display:flex; align-items:center; justify-content:center; min-height:0; padding-top:6px; }}
  .card .illu img {{ max-width:100%; max-height:100%; object-fit:contain; }}

  /* ---- 单大图布局 ---- */
  .one-illu {{ display:flex; flex-direction:column; gap:12px; min-height:0; }}
  .illu-big {{ flex:1; display:flex; align-items:center; justify-content:center; min-height:0; border:1px solid var(--line); border-radius:8px; padding:12px; background:#fff; }}
  .illu-big img {{ max-width:100%; max-height:100%; object-fit:contain; }}
  .caption {{ font-size:14px; color:var(--muted); text-align:center; line-height:1.5; }}
  .full-image {{ width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#fff; overflow:hidden; }}
  .full-image img {{ width:100%; height:100%; object-fit:cover; display:block; }}

  /* ---- 封面 ---- */
  .cover {{ display:grid; grid-template-columns: 1fr 1fr; align-items:center; gap:32px; height:100%; padding: 8px 0; }}
  .cover-tag {{ display:inline-block; font-size:13px; letter-spacing:3px; color:var(--accent); text-transform:uppercase; padding:5px 14px; background:var(--accent-soft); border-radius:999px; margin-bottom:18px; }}
  .cover-title {{ font-size:54px; font-weight:800; letter-spacing:1px; line-height:1.18; margin:0 0 18px; }}
  .cover-sub {{ font-size:18px; color:var(--muted); line-height:1.6; }}
  .cover-illu {{ display:flex; align-items:center; justify-content:center; height:100%; }}
  .cover-illu img {{ max-width:100%; max-height:100%; object-fit:contain; }}

  /* ---- 章节分隔页 ---- */
  .section-divider {{ display:flex; flex-direction:column; align-items:center; justify-content:center; gap:18px; height:100%; text-align:center; }}
  .section-tag-big {{ font-size:18px; letter-spacing:6px; color:var(--accent); text-transform:uppercase; padding:6px 18px; border:1px solid var(--accent); border-radius:999px; }}
  .section-title {{ font-size:48px; font-weight:800; line-height:1.2; margin:0; }}
  .section-sub {{ font-size:17px; color:var(--muted); max-width:720px; line-height:1.6; }}

  /* ---- 收尾页 ---- */
  .closing {{ display:flex; flex-direction:column; align-items:center; justify-content:center; gap:24px; height:100%; text-align:center; padding: 8px; }}
  .closing-illu {{ max-height: 60%; display:flex; align-items:center; justify-content:center; }}
  .closing-illu img {{ max-width:100%; max-height:100%; object-fit:contain; }}
  .closing-quote {{ font-size:24px; font-weight:600; line-height:1.5; max-width:920px; }}

  /* ---- 底部 quote ---- */
  .quote {{
    margin-top: 18px;
    background: linear-gradient(90deg, var(--accent-soft), #fff);
    border-left: 4px solid var(--accent);
    padding: 12px 22px;
    font-size: 15px; line-height: 1.6;
    border-radius: 0 8px 8px 0;
  }}
  .quote .em, .cover-sub .em, .section-sub .em, .closing-quote .em {{ color: var(--accent); font-weight: 600; }}

  /* ---- 翻页控件 ---- */
  .progress {{ position:fixed; top:0; left:0; height:3px; background:var(--accent); transition:width .25s ease; z-index:20; }}
  header.bar {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 10;
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px; pointer-events: none;
  }}
  header.bar h1 {{ margin:0; font-size:13px; font-weight:600; color:#e4e4e7; pointer-events:auto; }}
  header.bar h1 small {{ color: #71717a; font-weight: 400; margin-left: 8px; }}
  .nav {{
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    display: flex; align-items: center; gap: 12px;
    background: #18181b; padding: 6px 14px; border-radius: 999px;
    box-shadow: 0 8px 32px rgba(0,0,0,.4); user-select: none;
  }}
  .nav button {{ background:transparent; border:0; color:#e4e4e7; width:30px; height:30px; border-radius:50%; cursor:pointer; font-size:16px; display:inline-flex; align-items:center; justify-content:center; }}
  .nav button:hover {{ background: rgba(255,255,255,.08); }}
  .nav .counter {{ font-size:13px; color:#71717a; min-width:60px; text-align:center; font-variant-numeric:tabular-nums; }}
  .nav input[type=range] {{ width:90px; accent-color:var(--accent); }}
  .nav .zoom-lbl {{ font-size:11px; color:#71717a; min-width:36px; text-align:right; font-variant-numeric:tabular-nums; }}
  .hint {{ position:fixed; bottom:8px; right:16px; font-size:11px; color:#71717a; }}

  /* 网格预览 */
  body.grid-mode .stage, body.grid-mode .nav {{ display:none; }}
  .grid-view {{ display:none; padding:64px 32px 32px; overflow-y:auto; height:100vh; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:16px; background:var(--bg); }}
  body.grid-mode .grid-view {{ display:grid; }}
  .thumb {{ background:#fff; border-radius:6px; aspect-ratio:16/9; overflow:hidden; cursor:pointer; transition:transform .15s; position:relative; }}
  .thumb:hover {{ transform: translateY(-2px); }}
  .thumb iframe {{ width:1280px; height:720px; border:0; transform-origin: top left; transform: scale(.234); pointer-events:none; }}
  .thumb .lbl {{ position:absolute; bottom:4px; left:8px; font-size:11px; color:#71717a; }}

  @media print {{
    header.bar, .nav, .hint, .progress, .grid-view {{ display:none !important; }}
    .stage {{ position:relative; padding:0; page-break-after:always; }}
    .slide {{ box-shadow:none; border-radius:0; }}
  }}
</style>
</head>
<body>
  <div class="progress" id="progress"></div>
  <header class="bar"><h1>{title}<small>{subtitle}</small></h1></header>

  <div class="stage" id="stage"><div class="slide-wrap" id="slideWrap"></div></div>

  <div class="grid-view" id="gridView"></div>

  <nav class="nav">
    <button id="prev" title="← 上一页">‹</button>
    <span class="counter" id="counter">1 / {n}</span>
    <button id="next" title="→ 下一页">›</button>
    <button id="toggle" title="G 网格">⊞</button>
    <input type="range" id="zoom" min="60" max="140" value="100" title="缩放">
    <span class="zoom-lbl" id="zoomLbl">100%</span>
  </nav>
  <div class="hint">← → 翻页 · G 网格 · F 全屏 · +/- 缩放</div>

<script>
const slides = {slides_json};
let idx = 0;
const stage = document.getElementById('stage');
const slideWrap = document.getElementById('slideWrap');
const counter = document.getElementById('counter');
const progress = document.getElementById('progress');
const gridView = document.getElementById('gridView');
const zoomInput = document.getElementById('zoom');
const zoomLbl = document.getElementById('zoomLbl');

let userZoom = parseFloat(localStorage.getItem('slideZoom') || '1') || 1;
zoomInput.value = Math.round(userZoom*100);

function fitScale() {{
  const W = window.innerWidth, H = window.innerHeight;
  const fit = Math.min((W-20)/1280, (H-20)/720);
  const scale = fit * userZoom;
  document.documentElement.style.setProperty('--scale', scale);
  zoomLbl.textContent = Math.round(userZoom*100) + '%';
}}
window.addEventListener('resize', fitScale);
document.addEventListener('fullscreenchange', () => setTimeout(fitScale, 50));
zoomInput.addEventListener('input', () => {{
  userZoom = parseInt(zoomInput.value)/100;
  localStorage.setItem('slideZoom', userZoom);
  fitScale();
}});

function show(i) {{
  idx = (i + slides.length) % slides.length;
  slideWrap.innerHTML = slides[idx];
  counter.textContent = (idx+1) + ' / ' + slides.length;
  progress.style.width = ((idx+1)/slides.length*100) + '%';
  fitScale();
}}
function buildGrid() {{
  gridView.innerHTML = slides.map((html, i) => `
    <div class="thumb" data-i="${{i}}">
      <iframe srcdoc='<!doctype html><html><head><meta charset=utf-8><style>body{{margin:0;background:#fff;}}</style></head><body>${{html.replace(/'/g, "&#39;").replace(/"/g, "&quot;")}}</body></html>'></iframe>
      <div class="lbl">${{i+1}}</div>
    </div>`).join('');
  gridView.querySelectorAll('.thumb').forEach(el => {{
    el.onclick = () => {{ document.body.classList.remove('grid-mode'); show(parseInt(el.dataset.i)); }};
  }});
}}
document.getElementById('prev').onclick = () => show(idx-1);
document.getElementById('next').onclick = () => show(idx+1);
document.getElementById('toggle').onclick = () => {{ if(!gridView.children.length) buildGrid(); document.body.classList.toggle('grid-mode'); }};
document.addEventListener('keydown', (e) => {{
  if (['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)) {{ show(idx+1); e.preventDefault(); }}
  else if (['ArrowLeft','ArrowUp','PageUp'].includes(e.key)) {{ show(idx-1); e.preventDefault(); }}
  else if (e.key === 'Home') show(0);
  else if (e.key === 'End') show(slides.length-1);
  else if (e.key.toLowerCase() === 'g') {{ if(!gridView.children.length) buildGrid(); document.body.classList.toggle('grid-mode'); }}
  else if (e.key.toLowerCase() === 'f') {{ if(!document.fullscreenElement) document.documentElement.requestFullscreen(); else document.exitFullscreen(); }}
  else if (e.key === '+' || e.key === '=') {{ zoomInput.value = Math.min(140, parseInt(zoomInput.value)+5); zoomInput.dispatchEvent(new Event('input')); }}
  else if (e.key === '-' || e.key === '_') {{ zoomInput.value = Math.max(60, parseInt(zoomInput.value)-5); zoomInput.dispatchEvent(new Event('input')); }}
  else if (e.key === '0') {{ zoomInput.value = 100; zoomInput.dispatchEvent(new Event('input')); }}
}});
show(0);
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--title", default=None)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("-o", "--output", default="slideshow_v2.html")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    cdir = workdir / "content"
    if not cdir.is_dir():
        print(f"未找到 {cdir}")
        return 1
    files = sorted(cdir.glob("*.json"), key=lambda p: page_num(p.stem))
    if not files:
        print("没有 content JSON")
        return 1

    slides_html = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        slides_html.append(render_slide(data, workdir))

    title = args.title or workdir.name
    out_path = workdir / args.output
    html_text = HTML_SHELL.format(
        title=html.escape(title),
        subtitle=html.escape(args.subtitle),
        n=len(slides_html),
        slides_json=json.dumps(slides_html, ensure_ascii=False),
    )
    out_path.write_text(html_text, encoding="utf-8")
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"site -> {out_path}  ({len(slides_html)} 张, {size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
