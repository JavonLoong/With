"""
生成 review.html，原图 vs 重画图 左右对照，
便于人工筛选哪些保留、哪些丢弃。

用法:
    python build_review.py --workdir AI_Learning_OS            # 对比 input/ 与 output/
    python build_review.py --workdir AI_Learning_OS --pages    # 对比 pages/ 与 output_pages/
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CSS = """
body{font-family:-apple-system,Segoe UI,sans-serif;margin:0;background:#f6f6f7;color:#222}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid #e5e5e7;padding:14px 22px;z-index:9}
header h1{margin:0;font-size:16px;font-weight:600}
header .meta{font-size:12px;color:#666;margin-top:4px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px 22px;border-bottom:1px solid #ececef;align-items:start}
.row .name{grid-column:1/3;font:600 13px/1.4 ui-monospace,Consolas,monospace;color:#444;margin-bottom:6px}
.box{background:#fff;border:1px solid #e5e5e7;border-radius:10px;padding:8px;display:flex;flex-direction:column;align-items:center}
.box img{max-width:100%;height:auto;border-radius:6px}
.box .tag{font-size:11px;color:#888;margin-bottom:6px}
.missing{display:flex;align-items:center;justify-content:center;color:#bbb;font-size:13px;height:200px;background:#fafafa;border-radius:6px;width:100%}
"""


def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(src_dir: Path, dst_dir: Path, out_html: Path, title: str) -> None:
    if not src_dir.exists():
        print(f"src_dir not found: {src_dir}")
        return
    src_files = sorted(p for p in src_dir.iterdir() if p.is_file())
    rows = []
    for src in src_files:
        if src.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        out = dst_dir / (src.stem + ".png")
        # 使用相对 out_html 的路径（同 workdir）
        base = out_html.parent
        src_rel = src.relative_to(base).as_posix()
        out_rel = out.relative_to(base).as_posix() if out.exists() else None
        right_html = (
            f'<img src="{out_rel}" loading="lazy">'
            if out_rel
            else '<div class="missing">尚未生成</div>'
        )
        rows.append(
            f'<section class="row"><div class="name">{html_escape(src.name)}</div>'
            f'<div class="box"><div class="tag">原图</div><img src="{src_rel}" loading="lazy"></div>'
            f'<div class="box"><div class="tag">重画</div>{right_html}</div></section>'
        )
    html = (
        f'<!doctype html><html lang="zh"><head><meta charset="utf-8">'
        f"<title>{html_escape(title)}</title><style>{CSS}</style></head><body>"
        f'<header><h1>{html_escape(title)}</h1>'
        f'<div class="meta">共 {len(rows)} 张 — 原图来自 <code>{src_dir.name}/</code>，重画存于 <code>{dst_dir.name}/</code></div>'
        f"</header>" + "".join(rows) + "</body></html>"
    )
    out_html.write_text(html, encoding="utf-8")
    print(f"review -> {out_html}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--pages", action="store_true")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    name = workdir.name
    if args.pages:
        build(
            workdir / "pages",
            workdir / "output_pages",
            workdir / "review_pages.html",
            f"{name} — 整页重画对比",
        )
    else:
        build(
            workdir / "input",
            workdir / "output",
            workdir / "review.html",
            f"{name} — 嵌入图片重画对比",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
