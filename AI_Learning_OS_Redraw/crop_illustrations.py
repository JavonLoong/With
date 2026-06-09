"""按 <workdir>/content/*.json 中的 illu_bbox_pct，从 <workdir>/output/*.png 裁出插图。

输出到 <workdir>/illustrations/<page>_card<i>.png
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image


def crop_one(workdir: Path, page_json: Path) -> int:
    data = json.loads(page_json.read_text(encoding="utf-8"))
    page = data.get("page") or page_json.stem
    src_path = workdir / "output" / f"{page}.png"
    if not src_path.exists():
        print(f"  ! 缺少底图: {src_path}")
        return 0
    out_dir = workdir / "illustrations"
    out_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(src_path)
    W, H = im.size
    n = 0
    for i, card in enumerate(data.get("cards") or []):
        bbox = card.get("illu_bbox_pct")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = bbox
        box = (int(x1 * W), int(y1 * H), int(x2 * W), int(y2 * H))
        out_path = out_dir / f"{page}_card{i+1}.png"
        im.crop(box).save(out_path, optimize=True)
        n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    args = ap.parse_args()
    workdir = Path(args.workdir).resolve()
    cdir = workdir / "content"
    if not cdir.is_dir():
        print(f"未找到 content 目录: {cdir}")
        return 1
    files = sorted(cdir.glob("*.json"))
    total = 0
    for f in files:
        n = crop_one(workdir, f)
        total += n
        print(f"  {f.stem}: 裁出 {n} 张插图")
    print(f"完成: 共 {total} 张")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
