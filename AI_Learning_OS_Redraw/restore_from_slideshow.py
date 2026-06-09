"""一次性救援脚本：从备份 slideshow HTML 里抽出指定页的 base64 PNG。

支持两种来源：
- `--mode pages`（默认）：解析 build_slideshow.py 生成的 slideshow.html，
  里面每页是一张大整图，回写到 <workdir>/output/<page>.png 并重跑 crop。
- `--mode cards`：解析 build_site.py 生成的 slideshow_v2.html，
  里面每页是渲染好的 div，包含多张 <img> data:image/png;base64,...，
  按出现顺序回写到 <workdir>/illustrations/<page>_card<i>.png。

用法：
    python restore_from_slideshow.py --workdir AI_Learning_OS p007_x54 p013_x60
    python restore_from_slideshow.py --workdir AI_Learning_OS --mode cards --html slideshow_v2.html p007_x54 p013_x60
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from pathlib import Path


SLIDES_RE = re.compile(r"const slides = (\[.*?\]);", re.DOTALL)


def extract_slideshow_pages(html_path: Path) -> dict[str, bytes]:
    """从 build_slideshow.py 生成的 HTML 里取每页整图。"""
    text = html_path.read_text(encoding="utf-8")
    m = SLIDES_RE.search(text)
    if not m:
        raise SystemExit(f"在 {html_path} 里没找到 `const slides = [...]`")
    slides = json.loads(m.group(1))
    out: dict[str, bytes] = {}
    for s in slides:
        name = s.get("name") or ""
        src = s.get("src") or ""
        prefix = "data:image/png;base64,"
        if not src.startswith(prefix):
            continue
        out[name] = base64.b64decode(src[len(prefix):])
    return out


def extract_site_cards(html_path: Path) -> dict[str, list[bytes]]:
    """从 build_site.py 生成的 HTML 里按 data-page 拆出每页所有 <img> data URL。"""
    text = html_path.read_text(encoding="utf-8")
    m = SLIDES_RE.search(text)
    if not m:
        raise SystemExit(f"在 {html_path} 里没找到 `const slides = [...]`")
    # slides 是一个字符串数组，每个元素是一段 HTML（含转义字符）
    slides = json.loads(m.group(1))
    page_re = re.compile(r'data-page=\\?"([^"\\]+)\\?"|data-page="([^"]+)"')
    img_re = re.compile(r'data:image/png;base64,([A-Za-z0-9+/=]+)')
    out: dict[str, list[bytes]] = {}
    for chunk in slides:
        # chunk 已经是反转义后的 HTML 字符串（json.loads 已处理 \\")
        m2 = re.search(r'data-page="([^"]+)"', chunk)
        if not m2:
            continue
        page = m2.group(1)
        imgs = [base64.b64decode(b64) for b64 in img_re.findall(chunk)]
        if imgs:
            out[page] = imgs
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--mode", choices=["pages", "cards"], default="pages",
                    help="pages=从 slideshow.html 取整页图回写 output/；cards=从 slideshow_v2.html 取卡片图回写 illustrations/")
    ap.add_argument("--html", default=None,
                    help="工作目录下的 HTML 文件名（默认 pages 用 slideshow.html，cards 用 slideshow_v2.html）")
    ap.add_argument("pages", nargs="+", help="要还原的页 stem，如 p007_x54 p013_x60")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    html_name = args.html or ("slideshow.html" if args.mode == "pages" else "slideshow_v2.html")
    html_path = workdir / html_name
    if not html_path.exists():
        raise SystemExit(f"找不到 {html_path}")

    if args.mode == "pages":
        slides = extract_slideshow_pages(html_path)
        print(f"从 {html_path.name} 解析出 {len(slides)} 张整页图")
        out_dir = workdir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        restored = []
        for page in args.pages:
            if page not in slides:
                print(f"  ! 跳过 {page}：HTML 里没有")
                continue
            dst = out_dir / f"{page}.png"
            dst.write_bytes(slides[page])
            print(f"  ✓ 还原 {dst} ({len(slides[page])/1024:.1f} KB)")
            restored.append(page)
        if restored:
            print("\n重跑 crop_illustrations.py ...")
            subprocess.check_call(
                [sys.executable, "crop_illustrations.py", "--workdir", str(workdir)],
                cwd=str(Path(__file__).resolve().parent),
            )
    else:  # cards
        cards = extract_site_cards(html_path)
        print(f"从 {html_path.name} 解析出 {len(cards)} 个 page，共 {sum(len(v) for v in cards.values())} 张卡片图")
        illu_dir = workdir / "illustrations"
        illu_dir.mkdir(parents=True, exist_ok=True)
        for page in args.pages:
            if page not in cards:
                print(f"  ! 跳过 {page}：HTML 里没有")
                continue
            for i, data in enumerate(cards[page], 1):
                dst = illu_dir / f"{page}_card{i}.png"
                dst.write_bytes(data)
                print(f"  ✓ 还原 {dst} ({len(data)/1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
