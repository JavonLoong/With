"""
fix_p007.py
Use the v1_flash version of p007 (the good one with connecting arrows),
crop out the title area, and save as the one-illu card1 image.
Then rebuild the slideshow.
"""
from pathlib import Path
from PIL import Image
import subprocess, sys

WORKDIR = Path("d:/虚拟C盘/AI_Learning_OS_Redraw/AI_Learning_OS")

# v1_flash is the good version with proper arrows
src = Image.open(WORKDIR / "output_v1_flash" / "p007_x54.png")
w, h = src.size
print(f"source: {w}x{h}")

# Crop out the top title ("03_错题手术: 深度归因解剖") and bottom margin
# Title takes roughly top 8%, bottom margin ~2%
top = int(h * 0.17)
bot = int(h * 0.98)
cropped = src.crop((0, top, w, bot))
print(f"cropped: {cropped.size[0]}x{cropped.size[1]}")

# Save as card1 for one-illu layout
dst = WORKDIR / "illustrations" / "p007_x54_card1.png"
cropped.save(dst, "PNG", optimize=True)
print(f"[OK] saved {dst.name} ({dst.stat().st_size/1024:.0f} KB)")

# Also update the output directory so crop_illustrations won't break it later
import shutil
shutil.copy(WORKDIR / "output_v1_flash" / "p007_x54.png", WORKDIR / "output" / "p007_x54.png")
print("[OK] restored output/p007_x54.png from v1_flash")

# Rebuild slideshow
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
