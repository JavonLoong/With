"""把 ref 图中"想要的箭头"原样贴到 src 图的中间空白带，文字 0 改动。

两种模式：
- composite（旧）：羽化 mask 整块覆盖。会动 mask 范围内所有像素。
- stamp（新，默认）：先把 src 中间清成白底再"邮票式"贴上 ref 裁出的箭头切片。
  纯白底 → 完全不会触碰 src 上 mask 之外的任何字符。

用法：
    python splice_arrow.py stamp --src IMG1 --ref IMG2 --out OUT \
        --src-gap 0.40 0.20 0.62 0.78 \
        --ref-arrow 0.41 0.28 0.65 0.70

    python splice_arrow.py composite --src IMG1 --ref IMG2 --out OUT \
        --manual-bbox 0.40 0.18 0.62 0.78 --feather 12
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


def auto_bbox(src: Image.Image, ref: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    """根据像素差找出显著变化的 bbox。"""
    diff = ImageChops.difference(src.convert("L"), ref.convert("L"))
    # 二值化阈值滤掉小抖动 / 抗锯齿差异
    bw = diff.point(lambda v: 255 if v > threshold else 0, mode="L")
    return bw.getbbox()


def clamp_bbox(bbox: tuple[int, int, int, int], W: int, H: int,
               xrange: tuple[float, float] | None,
               yrange: tuple[float, float] | None,
               pad: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    if xrange:
        x0 = max(x0, int(W * xrange[0]))
        x1 = min(x1, int(W * xrange[1]))
    if yrange:
        y0 = max(y0, int(H * yrange[0]))
        y1 = min(y1, int(H * yrange[1]))
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(W, x1 + pad)
    y1 = min(H, y1 + pad)
    return x0, y0, x1, y1


def make_mask(size: tuple[int, int], bbox: tuple[int, int, int, int], feather: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    # 在 bbox 内填白
    from PIL import ImageDraw
    ImageDraw.Draw(mask).rectangle(bbox, fill=255)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
    return mask


def cmd_composite(args) -> int:
    src = Image.open(args.src).convert("RGB")
    ref = Image.open(args.ref).convert("RGB")
    if ref.size != src.size:
        print(f"  ref {ref.size} -> resize 到 src {src.size}")
        ref = ref.resize(src.size, Image.LANCZOS)
    W, H = src.size

    if args.manual_bbox:
        bx0, by0, bx1, by1 = args.manual_bbox
        bbox = (int(W * bx0), int(H * by0), int(W * bx1), int(H * by1))
        print(f"  使用手动 bbox: {bbox}")
    else:
        raw_bbox = auto_bbox(src, ref, args.threshold)
        if raw_bbox is None:
            print("  ! 没找到差异区域")
            return 2
        print(f"  原始差异 bbox: {raw_bbox}")
        bbox = clamp_bbox(raw_bbox, W, H, tuple(args.xrange), tuple(args.yrange), args.pad)
        print(f"  夹紧后 bbox:   {bbox}")

    mask = make_mask(src.size, bbox, args.feather)
    out = Image.composite(ref, src, mask)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out)
    print(f"  ✓ 写入 {args.out} ({Path(args.out).stat().st_size/1024:.1f} KB)")
    return 0


def cmd_stamp(args) -> int:
    src = Image.open(args.src).convert("RGB")
    ref = Image.open(args.ref).convert("RGB")
    W, H = src.size
    rW, rH = ref.size

    sx0, sy0, sx1, sy1 = args.src_gap
    gap_box = (int(W * sx0), int(H * sy0), int(W * sx1), int(H * sy1))
    print(f"  src 中间 gap 框: {gap_box}（这个矩形会被先涂白）")

    rx0, ry0, rx1, ry1 = args.ref_arrow
    crop_box = (int(rW * rx0), int(rH * ry0), int(rW * rx1), int(rH * ry1))
    print(f"  ref 箭头裁剪框: {crop_box}")

    arrow = ref.crop(crop_box)
    target_w = gap_box[2] - gap_box[0]
    target_h = gap_box[3] - gap_box[1]
    if args.preserve_aspect:
        # 保留长宽比，等比缩放到能整体塞进 gap
        aw, ah = arrow.size
        scale = min(target_w / aw, target_h / ah)
        new_w = int(aw * scale)
        new_h = int(ah * scale)
        arrow = arrow.resize((new_w, new_h), Image.LANCZOS)
        # 居中放置在 gap 内
        paste_x = gap_box[0] + (target_w - new_w) // 2
        paste_y = gap_box[1] + (target_h - new_h) // 2
        print(f"  保留比例缩放到: ({new_w}, {new_h}), 居中贴在 ({paste_x}, {paste_y})")
    else:
        arrow = arrow.resize((target_w, target_h), Image.LANCZOS)
        paste_x, paste_y = gap_box[0], gap_box[1]
        print(f"  拉伸缩放到: ({target_w}, {target_h})")

    out = src.copy()
    # 1) 先把 gap 区域涂白
    from PIL import ImageDraw
    ImageDraw.Draw(out).rectangle(gap_box, fill=(255, 255, 255))
    # 2) 把箭头切片贴到 gap 区域
    out.paste(arrow, (paste_x, paste_y))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out)
    print(f"  ✓ 写入 {args.out} ({Path(args.out).stat().st_size/1024:.1f} KB)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("composite", help="羽化 mask 整块合成（会动 mask 内所有像素）")
    pc.add_argument("--src", required=True)
    pc.add_argument("--ref", required=True)
    pc.add_argument("--out", required=True)
    pc.add_argument("--xrange", nargs=2, type=float, default=[0.30, 0.66])
    pc.add_argument("--yrange", nargs=2, type=float, default=[0.10, 0.85])
    pc.add_argument("--feather", type=int, default=18)
    pc.add_argument("--pad", type=int, default=8)
    pc.add_argument("--threshold", type=int, default=18)
    pc.add_argument("--manual-bbox", nargs=4, type=float, default=None)

    ps = sub.add_parser("stamp", help="清白 + 邮票式贴箭头切片，src 文字 0 改动")
    ps.add_argument("--src", required=True)
    ps.add_argument("--ref", required=True)
    ps.add_argument("--out", required=True)
    ps.add_argument("--src-gap", nargs=4, type=float, required=True,
                    help="src 中要被涂白并贴箭头的矩形 [x0 y0 x1 y1]，0~1")
    ps.add_argument("--ref-arrow", nargs=4, type=float, required=True,
                    help="ref 中要裁出的箭头矩形 [x0 y0 x1 y1]，0~1")
    ps.add_argument("--preserve-aspect", action="store_true",
                    help="缩放箭头时保留长宽比（默认拉伸填满 gap）")

    args = ap.parse_args()
    if args.cmd == "composite":
        return cmd_composite(args)
    elif args.cmd == "stamp":
        return cmd_stamp(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
