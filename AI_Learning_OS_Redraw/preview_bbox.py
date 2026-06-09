"""
preview_bbox.py
在每张 2K 重画图上把 JSON 里的 illu_bbox_pct 框出来，
生成 preview/ 目录下的预览图，方便逐页审核。
用法: python preview_bbox.py --workdir AI_Learning_OS
"""
import argparse, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

COLORS = ["#FF4444", "#FF8800", "#22CC44"]  # card1 / card2 / card3

def draw_page(workdir: Path, json_path: Path, out_dir: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    page = data["page"]
    img_path = workdir / "output" / f"{page}.png"
    if not img_path.exists():
        print(f"  [skip] {page}: 找不到 {img_path}")
        return

    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img, "RGBA")

    cards = data.get("cards", [])
    for i, card in enumerate(cards):
        bbox_pct = card.get("illu_bbox_pct")
        if not bbox_pct:
            continue
        x0, y0, x1, y1 = (
            int(bbox_pct[0] * w),
            int(bbox_pct[1] * h),
            int(bbox_pct[2] * w),
            int(bbox_pct[3] * h),
        )
        color = COLORS[i % len(COLORS)]
        # 半透明填充
        draw.rectangle([x0, y0, x1, y1], fill=color + "44", outline=color, width=6)
        # 标注 y% 值
        label = f"card{i+1}  y0={bbox_pct[1]:.3f}  y1={bbox_pct[3]:.3f}  ({y0}px–{y1}px / {h}px)"
        draw.rectangle([x0, y0, x0 + len(label)*14 + 10, y0 + 36], fill=color + "CC")
        draw.text((x0 + 5, y0 + 5), label, fill="white")

    out_path = out_dir / f"{page}_preview.jpg"
    img.save(out_path, quality=82)
    print(f"  {page}: {len(cards)} 框 → {out_path.name}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="AI_Learning_OS")
    args = ap.parse_args()

    workdir = Path(args.workdir)
    content_dir = workdir / "content"
    out_dir = workdir / "preview_bbox"
    out_dir.mkdir(exist_ok=True)

    jsons = sorted(content_dir.glob("*.json"))
    print(f"处理 {len(jsons)} 页…")
    for jp in jsons:
        draw_page(workdir, jp, out_dir)
    print(f"\n预览图已保存到: {out_dir.resolve()}")

if __name__ == "__main__":
    raise SystemExit(main())
