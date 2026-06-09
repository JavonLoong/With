"""
merge_p007.py
把 p007_x54_card1.png 和 p007_x54_card2.png 左右拼合，
中间加一个粗箭头（黑色描边 + 白色填充），输出为
AI_Learning_OS/illustrations/p007_x54_merged.png
然后把 JSON 改成 one-illu 指向该图，最后重 build。
"""

from pathlib import Path
from PIL import Image, ImageDraw
import json, subprocess, sys

WORKDIR  = Path("d:/虚拟C盘/AI_Learning_OS_Redraw/AI_Learning_OS")
ILLU_DIR = WORKDIR / "illustrations"
CONTENT  = WORKDIR / "content" / "p007_x54.json"

card1 = Image.open(ILLU_DIR / "p007_x54_card1.png").convert("RGBA")
card2 = Image.open(ILLU_DIR / "p007_x54_card2.png").convert("RGBA")

# ---------- 高度统一（以较高者为准，另一张居中填白）----------
H = max(card1.height, card2.height)
def pad_height(img, H):
    if img.height == H:
        return img
    canvas = Image.new("RGBA", (img.width, H), (255, 255, 255, 255))
    canvas.paste(img, (0, (H - img.height) // 2))
    return canvas

card1 = pad_height(card1, H)
card2 = pad_height(card2, H)

# ---------- 箭头区域宽度 ----------
ARROW_W = max(120, int(H * 0.10))   # 相对于高度的 10%，最少 120px
W_TOTAL = card1.width + ARROW_W + card2.width

canvas = Image.new("RGBA", (W_TOTAL, H), (255, 255, 255, 255))
canvas.paste(card1, (0, 0))
canvas.paste(card2, (card1.width + ARROW_W, 0))

# ---------- 画箭头 ----------
draw = ImageDraw.Draw(canvas)

arrow_cx = card1.width + ARROW_W // 2
arrow_cy = H // 2

# 箭头主体（横向，从左到右）
shaft_h  = max(14, int(H * 0.018))   # 轴高
head_w   = int(ARROW_W * 0.42)       # 箭头头部宽
head_h   = max(36, int(H * 0.05))    # 箭头头部高（半高）

x0 = card1.width + 8                 # 从 card1 右边缘稍右开始
x1 = card1.width + ARROW_W - 8       # 到 card2 左边缘稍左结束

# 轴矩形
shaft_top    = arrow_cy - shaft_h // 2
shaft_bottom = arrow_cy + shaft_h // 2
shaft_right  = x1 - head_w           # 轴截止到箭头头部开始位置

FILL    = (40, 40, 40)
OUTLINE = (40, 40, 40)

# 整体箭头多边形（←轴→箭头尖）
arrow_poly = [
    (x0,           shaft_top),
    (shaft_right,  shaft_top),
    (shaft_right,  arrow_cy - head_h),
    (x1,           arrow_cy),
    (shaft_right,  arrow_cy + head_h),
    (shaft_right,  shaft_bottom),
    (x0,           shaft_bottom),
]
draw.polygon(arrow_poly, fill=FILL, outline=OUTLINE)

# ---------- 保存 ----------
out_path = ILLU_DIR / "p007_x54_merged.png"
canvas = canvas.convert("RGB")
canvas.save(out_path, "PNG", optimize=True)
print(f"[OK] merged -> {out_path}  ({out_path.stat().st_size/1024:.0f} KB)")
print(f"     size: {W_TOTAL} x {H}")

import shutil
shutil.copy(out_path, ILLU_DIR / "p007_x54_card1.png")
print("[OK] copied merged -> p007_x54_card1.png")

data = json.loads(CONTENT.read_text(encoding="utf-8"))
data["layout"] = "one-illu"
data["cards"] = [
    {
        "key":          "错题手术",
        "title":        "传统堆积 → 解剖归因卡",
        "desc":         "传统做法：题错了 → 抄一遍正确解 → 刷下一题，错题本沦为题目的堆积。AI 处方：表面信息 / 真正考点 / 错误根因 / 下次触发条件 / 手术处方 — 五段式还原认知断点。",
        "featured":     True,
        "illu_bbox_pct": [0.0, 0.0, 1.0, 1.0]
    }
]
CONTENT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] {CONTENT.name} -> one-illu")

print("\n-> rebuild slideshow...")
ret = subprocess.run(
    ["python", "build_site.py", "--workdir", "AI_Learning_OS"],
    cwd="d:/虚拟C盘/AI_Learning_OS_Redraw"
)
if ret.returncode == 0:
    print("[OK] slideshow_v2.html rebuilt")
else:
    print("[FAIL] build error")
    sys.exit(1)
