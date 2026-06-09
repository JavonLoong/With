"""把 AI 重画版 p002 裁成两块结构插图，去掉列标题和底部 quote。"""
from pathlib import Path
from PIL import Image

SRC = Path(__file__).resolve().parents[1] / "AI_Learning_OS" / "output" / "p002_x49.png"
OUT = Path(__file__).resolve().parent / "assets"
OUT.mkdir(exist_ok=True)

im = Image.open(SRC)
w, h = im.size
print(f"src size: {w}x{h}")

# 估算: 顶部列标题 ~14%, 底部 quote ~14%, 中间分界线在中点
top = int(h * 0.14)
bot = int(h * 0.86)
midx = w // 2

left = im.crop((40, top, midx - 20, bot))
right = im.crop((midx + 20, top, w - 40, bot))

left.save(OUT / "p002_left_loop.png", optimize=True)
right.save(OUT / "p002_right_iso.png", optimize=True)
print(f"left:  {left.size}  -> {OUT / 'p002_left_loop.png'}")
print(f"right: {right.size}  -> {OUT / 'p002_right_iso.png'}")
