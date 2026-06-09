from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


PAGE_RE = re.compile(r"p(\d+)")


def page_num(name: str) -> int:
    match = PAGE_RE.match(name)
    return int(match.group(1)) if match else 9999


def load_meta(workdir: Path, stem: str) -> dict:
    path = workdir / "content" / f"{stem}.json"
    if not path.exists():
        return {"page_title": stem, "section_tag": "", "quote": ""}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "page_title": data.get("page_title") or stem,
        "section_tag": data.get("section_tag") or "",
        "quote": data.get("quote") or "",
    }


def render_slide(png: Path, workdir: Path, image_dir: str) -> str:
    meta = load_meta(workdir, png.stem)
    src = f"{image_dir}/{png.name}"
    tag = meta["section_tag"]
    title = meta["page_title"]
    quote = meta["quote"]
    tag_html = f'<span class="tag">{html.escape(tag)}</span>' if tag else ""
    quote_html = f'<footer class="quote">{html.escape(quote)}</footer>' if quote else ""
    return f"""
<div class="slide" data-page="{html.escape(png.stem)}">
  <header class="head">
    {tag_html}
    <h1>{html.escape(title)}</h1>
  </header>
  <section class="image-frame">
    <img src="{html.escape(src)}" alt="{html.escape(png.stem)}">
  </section>
  {quote_html}
</div>"""


HTML_TEMPLATE = """<!doctype html>
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
  .stage {{ position:fixed; inset:0; display:flex; align-items:center; justify-content:center; padding:0; overflow:hidden; }}
  .slide-wrap {{ width:1280px; height:720px; transform-origin:center center; transform:scale(var(--scale, 1)); }}
  .slide {{
    width:1280px; height:720px;
    background:var(--slide-bg); color:var(--fg);
    border-radius:14px; box-shadow:0 30px 80px -20px rgba(0,0,0,.6);
    padding:40px 56px 28px;
    display:grid; grid-template-rows:auto 1fr auto;
    overflow:hidden;
  }}
  .head {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:14px; margin-bottom:18px; }}
  .tag {{ font-size:12px; font-weight:600; letter-spacing:2px; color:var(--accent); text-transform:uppercase; padding:4px 12px; background:var(--accent-soft); border-radius:999px; }}
  .head h1 {{ margin:0; font-size:28px; font-weight:700; letter-spacing:0.5px; line-height:1.3; }}
  .image-frame {{ min-height:0; border:1px solid var(--line); border-radius:8px; padding:10px; background:#fff; display:flex; align-items:center; justify-content:center; overflow:hidden; }}
  .image-frame img {{ max-width:100%; max-height:100%; width:auto; height:auto; object-fit:contain; display:block; }}
  .quote {{
    margin-top:18px;
    background:linear-gradient(90deg,var(--accent-soft),#fff);
    border-left:4px solid var(--accent);
    padding:12px 22px;
    font-size:15px; line-height:1.6;
    border-radius:0 8px 8px 0;
  }}
  .progress {{ position:fixed; top:0; left:0; height:3px; background:var(--accent); transition:width .25s ease; z-index:20; }}
  header.bar {{
    position:fixed; top:0; left:0; right:0; z-index:10;
    display:flex; align-items:center; justify-content:space-between;
    padding:12px 24px; pointer-events:none;
  }}
  header.bar h1 {{ margin:0; font-size:13px; font-weight:600; color:#e4e4e7; pointer-events:auto; }}
  header.bar h1 small {{ color:#71717a; font-weight:400; margin-left:8px; }}
  .nav {{
    position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
    display:flex; align-items:center; gap:12px;
    background:#18181b; padding:6px 14px; border-radius:999px;
    box-shadow:0 8px 32px rgba(0,0,0,.4); user-select:none;
  }}
  .nav button {{ background:transparent; border:0; color:#e4e4e7; width:30px; height:30px; border-radius:50%; cursor:pointer; font-size:16px; display:inline-flex; align-items:center; justify-content:center; }}
  .nav button:hover {{ background:rgba(255,255,255,.08); }}
  .nav .counter {{ font-size:13px; color:#71717a; min-width:60px; text-align:center; font-variant-numeric:tabular-nums; }}
  .nav input[type=range] {{ width:90px; accent-color:var(--accent); }}
  .nav .zoom-lbl {{ font-size:11px; color:#71717a; min-width:36px; text-align:right; font-variant-numeric:tabular-nums; }}
  .hint {{ position:fixed; bottom:8px; right:16px; font-size:11px; color:#71717a; }}
  body.grid-mode .stage, body.grid-mode .nav {{ display:none; }}
  .grid-view {{ display:none; padding:64px 32px 32px; overflow-y:auto; height:100vh; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:16px; background:var(--bg); }}
  body.grid-mode .grid-view {{ display:grid; }}
  .thumb {{ background:#fff; border-radius:6px; aspect-ratio:16/9; overflow:hidden; cursor:pointer; transition:transform .15s; position:relative; }}
  .thumb:hover {{ transform:translateY(-2px); }}
  .thumb iframe {{ width:1280px; height:720px; border:0; transform-origin:top left; transform:scale(.234); pointer-events:none; }}
  .thumb .lbl {{ position:absolute; bottom:4px; left:8px; font-size:11px; color:#71717a; }}
</style>
</head>
<body>
  <div class="progress" id="progress"></div>
  <header class="bar"><h1>{title}<small>{version_label}</small></h1></header>
  <div class="stage" id="stage"><div class="slide-wrap" id="slideWrap"></div></div>
  <div class="grid-view" id="gridView"></div>
  <nav class="nav">
    <button id="prev" title="previous">‹</button>
    <span class="counter" id="counter">1 / {n}</span>
    <button id="next" title="next">›</button>
    <button id="toggle" title="grid">▦</button>
    <input type="range" id="zoom" min="60" max="140" value="100" title="zoom">
    <span class="zoom-lbl" id="zoomLbl">100%</span>
  </nav>
  <div class="hint">← → 翻页 · G 网格 · F 全屏 · +/- 缩放</div>
<script>
const slides = {slides_json};
let idx = 0;
const slideWrap = document.getElementById('slideWrap');
const counter = document.getElementById('counter');
const progress = document.getElementById('progress');
const gridView = document.getElementById('gridView');
const zoomInput = document.getElementById('zoom');
const zoomLbl = document.getElementById('zoomLbl');
let userZoom = parseFloat(localStorage.getItem('slideZoomFrame:{version_label}') || '1') || 1;
zoomInput.value = Math.round(userZoom * 100);
function fitScale() {{
  const fit = Math.min((window.innerWidth - 20) / 1280, (window.innerHeight - 20) / 720);
  document.documentElement.style.setProperty('--scale', fit * userZoom);
  zoomLbl.textContent = Math.round(userZoom * 100) + '%';
}}
window.addEventListener('resize', fitScale);
document.addEventListener('fullscreenchange', () => setTimeout(fitScale, 50));
zoomInput.addEventListener('input', () => {{
  userZoom = parseInt(zoomInput.value, 10) / 100;
  localStorage.setItem('slideZoomFrame:{version_label}', userZoom);
  fitScale();
}});
function show(i) {{
  idx = (i + slides.length) % slides.length;
  slideWrap.innerHTML = slides[idx];
  counter.textContent = (idx + 1) + ' / ' + slides.length;
  progress.style.width = ((idx + 1) / slides.length * 100) + '%';
  fitScale();
}}
function buildGrid() {{
  gridView.innerHTML = slides.map((html, i) => `
    <div class="thumb" data-i="${{i}}">
      <iframe srcdoc='<!doctype html><html><head><meta charset=utf-8><style>body{{margin:0;background:#fff;}}</style></head><body>${{html.replace(/'/g, "&#39;").replace(/"/g, "&quot;")}}</body></html>'></iframe>
      <div class="lbl">${{i + 1}}</div>
    </div>`).join('');
  gridView.querySelectorAll('.thumb').forEach(el => {{
    el.onclick = () => {{ document.body.classList.remove('grid-mode'); show(parseInt(el.dataset.i, 10)); }};
  }});
}}
document.getElementById('prev').onclick = () => show(idx - 1);
document.getElementById('next').onclick = () => show(idx + 1);
document.getElementById('toggle').onclick = () => {{ if (!gridView.children.length) buildGrid(); document.body.classList.toggle('grid-mode'); }};
document.addEventListener('keydown', (e) => {{
  if (['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)) {{ show(idx + 1); e.preventDefault(); }}
  else if (['ArrowLeft','ArrowUp','PageUp'].includes(e.key)) {{ show(idx - 1); e.preventDefault(); }}
  else if (e.key === 'Home') show(0);
  else if (e.key === 'End') show(slides.length - 1);
  else if (e.key.toLowerCase() === 'g') {{ if (!gridView.children.length) buildGrid(); document.body.classList.toggle('grid-mode'); }}
  else if (e.key.toLowerCase() === 'f') {{ if (!document.fullscreenElement) document.documentElement.requestFullscreen(); else document.exitFullscreen(); }}
  else if (e.key === '+' || e.key === '=') {{ zoomInput.value = Math.min(140, parseInt(zoomInput.value, 10) + 5); zoomInput.dispatchEvent(new Event('input')); }}
  else if (e.key === '-' || e.key === '_') {{ zoomInput.value = Math.max(60, parseInt(zoomInput.value, 10) - 5); zoomInput.dispatchEvent(new Event('input')); }}
  else if (e.key === '0') {{ zoomInput.value = 100; zoomInput.dispatchEvent(new Event('input')); }}
}});
show(0);
</script>
</body>
</html>
"""


def build(workdir: Path, title: str, output: str, image_dir: str, version_label: str) -> Path:
    out_dir = workdir / image_dir
    pngs = sorted(out_dir.glob("*.png"), key=lambda p: page_num(p.stem))
    if not pngs:
        raise SystemExit(f"No PNG files found in {out_dir}")
    slides = [render_slide(p, workdir, image_dir) for p in pngs]
    out_path = workdir / output
    out_path.write_text(
        HTML_TEMPLATE.format(
            title=html.escape(title),
            version_label=html.escape(version_label),
            n=len(slides),
            slides_json=json.dumps(slides, ensure_ascii=False),
        ),
        encoding="utf-8",
    )
    print(f"{version_label} slideshow -> {out_path} ({len(slides)} slides, linked {image_dir} images)")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("-o", "--output", default="slideshow_v3.html")
    parser.add_argument("--image-dir", default="output")
    parser.add_argument("--version-label", default="V3")
    args = parser.parse_args()
    workdir = Path(args.workdir).resolve()
    build(workdir, args.title or workdir.name, args.output, args.image_dir, args.version_label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
