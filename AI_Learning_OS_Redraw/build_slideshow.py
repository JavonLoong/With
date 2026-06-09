"""
把 <workdir>/output/ 下的重画图打包成一个**独立可分享**的 HTML 幻灯片：
- 所有图以 base64 内嵌，单文件即可发出去
- 默认翻页模式（PPT 风格），按 ← → / ↑ ↓ / Space 翻页
- 按 G 切换网格预览（缩略图全览）
- 顶部进度条 + 计数器

用法：
    python build_slideshow.py --workdir AI_Learning_OS
    python build_slideshow.py --workdir AI_Learning_OS_Blueprint --title "AI_Learning_OS 蓝图"

输出：<workdir>/slideshow.html
"""
from __future__ import annotations

import argparse
import base64
import html
import re
from pathlib import Path

PAGE_RE = re.compile(r"p(\d+)")


def page_num(name: str) -> int:
    m = PAGE_RE.match(name)
    return int(m.group(1)) if m else 9999


HTML_TEMPLATE = """<!doctype html>
<html lang=\"zh-CN\">
<head>
<meta charset=\"utf-8\">
<title>{title}</title>
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<style>
  :root {{
    --bg: #0e0e10;
    --panel: #18181b;
    --fg: #e4e4e7;
    --muted: #71717a;
    --accent: #6b3fa0;
  }}
  * {{ box-sizing: border-box; }}
  html,body {{ margin:0; padding:0; background:var(--bg); color:var(--fg); font-family:-apple-system,\"Segoe UI\",\"PingFang SC\",\"Microsoft YaHei\",sans-serif; height:100%; overflow:hidden; }}
  header {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 10;
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px; background: linear-gradient(180deg, rgba(14,14,16,.95), rgba(14,14,16,0));
    pointer-events: none;
  }}
  header h1 {{ margin:0; font-size:14px; font-weight:600; color:var(--fg); pointer-events:auto; }}
  header h1 small {{ color:var(--muted); font-weight:400; margin-left:8px; }}
  .progress {{
    position: fixed; top: 0; left: 0; height: 3px; background: var(--accent);
    transition: width .25s ease; z-index: 20;
  }}
  .stage {{
    position: fixed; inset: 0; display: flex; align-items: center; justify-content: center;
    padding: 60px 80px;
  }}
  .stage img {{
    max-width: 100%; max-height: 100%;
    width: auto; height: auto;
    border-radius: 4px; background: #fff;
    box-shadow: 0 30px 60px -20px rgba(0,0,0,.6), 0 0 0 1px rgba(255,255,255,.04);
    transform: scale(var(--zoom, 1));
    transform-origin: center center;
  }}
  .nav {{
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    display: flex; align-items: center; gap: 16px;
    background: var(--panel); padding: 8px 16px; border-radius: 999px;
    box-shadow: 0 8px 32px rgba(0,0,0,.4);
    user-select: none;
  }}
  .nav button {{
    background: transparent; border: 0; color: var(--fg);
    width: 32px; height: 32px; border-radius: 50%; cursor: pointer;
    font-size: 16px; display: inline-flex; align-items: center; justify-content: center;
    transition: background .15s;
  }}
  .nav button:hover {{ background: rgba(255,255,255,.08); }}
  .nav .counter {{ font-size:13px; color:var(--muted); min-width:64px; text-align:center; font-variant-numeric: tabular-nums; }}
  .nav input[type=range] {{ width:90px; accent-color:var(--accent); }}
  .nav .zoom-lbl {{ font-size:11px; color:var(--muted); min-width:36px; text-align:right; font-variant-numeric:tabular-nums; }}
  .hint {{
    position: fixed; bottom: 8px; right: 16px; font-size: 11px; color: var(--muted);
  }}
  /* 网格预览 */
  .grid {{
    display: none; position: fixed; inset: 0; padding: 64px 32px 32px; overflow-y: auto;
    background: var(--bg);
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;
    z-index: 5;
  }}
  body.grid-mode .stage,
  body.grid-mode .nav {{ display: none; }}
  body.grid-mode .grid {{ display: grid; }}
  .grid figure {{ margin:0; cursor:pointer; transition: transform .15s; }}
  .grid figure:hover {{ transform: translateY(-2px); }}
  .grid img {{ width:100%; display:block; border-radius:4px; background:#fff; }}
  .grid figcaption {{ font-size:11px; color:var(--muted); padding:4px 2px; }}
  @media print {{
    header, .nav, .hint, .progress {{ display:none !important; }}
    .stage {{ position:relative; padding:0; page-break-after:always; }}
    .stage img {{ max-height:none; box-shadow:none; }}
  }}
</style>
</head>
<body>
  <div class=\"progress\" id=\"progress\"></div>
  <header><h1>{title}<small>{subtitle}</small></h1></header>

  <section class=\"stage\" id=\"stage\">
    <img id=\"slide\" alt=\"slide\">
  </section>

  <section class=\"grid\" id=\"grid\">
    {grid_items}
  </section>

  <nav class=\"nav\">
    <button id=\"prev\" title=\"上一页 (←)\">‹</button>
    <span class=\"counter\" id=\"counter\">1 / {n}</span>
    <button id=\"next\" title=\"下一页 (→)\">›</button>
    <button id=\"toggle\" title=\"网格预览 (G)\">⊞</button>
    <input type=\"range\" id=\"zoom\" min=\"60\" max=\"140\" value=\"100\" title=\"zoom\">
    <span class=\"zoom-lbl\" id=\"zoomLbl\">100%</span>
  </nav>

  <div class=\"hint\">← → 翻页 · G 网格 · F 全屏 · +/- 缩放</div>

<script>
const slides = {slides_json};
let idx = 0;
const slide = document.getElementById('slide');
const counter = document.getElementById('counter');
const progress = document.getElementById('progress');
const zoomInput = document.getElementById('zoom');
const zoomLbl = document.getElementById('zoomLbl');
let userZoom = parseFloat(localStorage.getItem('slideZoomV3') || '1') || 1;
zoomInput.value = Math.round(userZoom * 100);
function setZoom(value) {{
  userZoom = Math.max(0.6, Math.min(1.4, value));
  document.documentElement.style.setProperty('--zoom', userZoom);
  zoomInput.value = Math.round(userZoom * 100);
  zoomLbl.textContent = Math.round(userZoom * 100) + '%';
  localStorage.setItem('slideZoomV3', userZoom);
}}
zoomInput.addEventListener('input', () => setZoom(parseInt(zoomInput.value, 10) / 100));
function show(i) {{
  idx = (i + slides.length) % slides.length;
  slide.src = slides[idx].src;
  slide.alt = slides[idx].name;
  counter.textContent = (idx+1) + ' / ' + slides.length;
  progress.style.width = ((idx+1)/slides.length*100) + '%';
}}
document.getElementById('prev').onclick = () => show(idx-1);
document.getElementById('next').onclick = () => show(idx+1);
document.getElementById('toggle').onclick = () => document.body.classList.toggle('grid-mode');
document.querySelectorAll('.grid figure').forEach((el, i) => {{
  el.onclick = () => {{ document.body.classList.remove('grid-mode'); show(i); }};
}});
document.addEventListener('keydown', (e) => {{
  if (['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)) {{ show(idx+1); e.preventDefault(); }}
  else if (['ArrowLeft','ArrowUp','PageUp'].includes(e.key)) {{ show(idx-1); e.preventDefault(); }}
  else if (e.key === 'Home') show(0);
  else if (e.key === 'End') show(slides.length-1);
  else if (e.key.toLowerCase() === 'g') document.body.classList.toggle('grid-mode');
  else if (e.key.toLowerCase() === 'f') {{
    if (!document.fullscreenElement) document.documentElement.requestFullscreen();
    else document.exitFullscreen();
  }}
  else if (e.key === '+' || e.key === '=') setZoom(userZoom + 0.05);
  else if (e.key === '-' || e.key === '_') setZoom(userZoom - 0.05);
  else if (e.key === '0') setZoom(1);
}});
setZoom(userZoom);
show(0);
</script>
</body>
</html>
"""


def build(
    workdir: Path,
    title: str,
    subtitle: str = "",
    output: str = "slideshow.html",
    linked: bool = False,
) -> Path:
    out_dir = workdir / "output"
    pngs = sorted(out_dir.glob("*.png"), key=lambda p: page_num(p.stem))
    if not pngs:
        raise SystemExit(f"没有在 {out_dir} 找到图片")

    slides = []
    for p in pngs:
        if linked:
            src = f"output/{p.name}"
        else:
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            src = f"data:image/png;base64,{b64}"
        slides.append(
            {"name": p.stem, "src": src}
        )

    grid_items = "\n    ".join(
        f'<figure><img src="{s["src"]}" alt="{html.escape(s["name"])}"><figcaption>{html.escape(s["name"])}</figcaption></figure>'
        for s in slides
    )

    import json

    html_text = HTML_TEMPLATE.format(
        title=html.escape(title),
        subtitle=html.escape(subtitle),
        n=len(slides),
        slides_json=json.dumps(slides, ensure_ascii=False),
        grid_items=grid_items,
    )
    out = workdir / output
    out.write_text(html_text, encoding="utf-8")
    mode = "linked" if linked else "embedded"
    print(f"slideshow -> {out}  ({len(slides)} \u5f20, {out.stat().st_size/1024/1024:.1f} MB, {mode})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--title", default=None, help="\u9876\u90e8\u6807\u9898")
    ap.add_argument("--subtitle", default="", help="\u6807\u9898\u53f3\u4fa7\u526f\u8bf4\u660e")
    ap.add_argument("-o", "--output", default="slideshow.html", help="\u8f93\u51fa HTML \u6587\u4ef6\u540d")
    ap.add_argument("--linked", action="store_true", help="\u76f4\u63a5\u5f15\u7528 output/*.png\uff0c\u4e0d\u5185\u5d4c base64")
    args = ap.parse_args()
    workdir = Path(args.workdir).resolve()
    title = args.title or workdir.name
    build(workdir, title, args.subtitle, args.output, args.linked)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
