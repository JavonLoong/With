"""
从 PDF 中抽取所有"有结构"的图片。

策略：
1. 渲染每一页为高清 PNG (作为兜底)，存到 pages/
2. 抽取每一页的"嵌入图片对象"，存到 input/
3. 同时输出 manifest.json，记录每张图片来自哪一页 / 在页面上的位置 / 像素尺寸
   方便后续人工筛选 + 替换回 PPT。

用法：
    python extract_images.py <pdf_path> [out_dir]
默认输出到当前目录下的 ./<pdf_stem>/input/ 和 ./<pdf_stem>/pages/，
这样多份 PDF 不会互相覆盖。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz  # PyMuPDF


MIN_W, MIN_H = 120, 120  # 过滤过小的图标/分隔符
PAGE_DPI = 200  # 每页渲染 PNG 的 DPI


def extract(pdf_path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir = out_dir / "input"
    pages_dir = out_dir / "pages"
    img_dir.mkdir(exist_ok=True)
    pages_dir.mkdir(exist_ok=True)

    doc = fitz.open(pdf_path)
    manifest = {"pdf": str(pdf_path), "pages": []}

    for page_index, page in enumerate(doc):
        page_no = page_index + 1

        # 1) 整页渲染（兜底，用于"整页就是一张结构图"的场景）
        pix = page.get_pixmap(dpi=PAGE_DPI, alpha=False)
        page_png = pages_dir / f"page_{page_no:03d}.png"
        pix.save(page_png)

        # 2) 抽取嵌入图片
        page_imgs = []
        seen_xrefs: set[int] = set()
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                base = doc.extract_image(xref)
            except Exception as e:
                print(f"  ! page {page_no} xref {xref} extract failed: {e}")
                continue
            ext = base.get("ext", "png")
            data = base["image"]
            w = base.get("width", 0)
            h = base.get("height", 0)
            if w < MIN_W or h < MIN_H:
                continue  # 跳过太小的装饰
            name = f"p{page_no:03d}_x{xref}.{ext}"
            (img_dir / name).write_bytes(data)
            page_imgs.append(
                {
                    "file": name,
                    "xref": xref,
                    "width": w,
                    "height": h,
                }
            )

        manifest["pages"].append(
            {
                "page": page_no,
                "page_render": page_png.name,
                "embedded_images": page_imgs,
            }
        )
        print(
            f"page {page_no:>3}: rendered + {len(page_imgs)} embedded image(s) extracted"
        )

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python extract_images.py <pdf_path> [out_dir]")
        return 1
    pdf = Path(sys.argv[1]).resolve()
    if not pdf.exists():
        print(f"PDF not found: {pdf}")
        return 1
    if len(sys.argv) >= 3:
        out = Path(sys.argv[2]).resolve()
    else:
        out = (Path.cwd() / pdf.stem).resolve()
    extract(pdf, out)
    print(f"\nDone. workdir = {out}")
    print(f"  input/  = {out / 'input'}")
    print(f"  pages/  = {out / 'pages'}")
    print(f"  manifest = {out / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
