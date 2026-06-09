"""
最小化用例：用一张测试图测 nano-banana API key 是否可用。
会在脚本目录下生成 test_input.png 和 test_output.png。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from redraw import DEFAULT_API_KEY, call_gemini, load_prompt  # noqa: E402


def make_test_png(p: Path) -> None:
    img = Image.new("RGB", (640, 400), "white")
    d = ImageDraw.Draw(img)
    # 一个最简单的"流程图三方框 + 箭头"
    boxes = [(40, 160, 200, 240), (240, 160, 400, 240), (440, 160, 600, 240)]
    for x0, y0, x1, y1 in boxes:
        d.rectangle((x0, y0, x1, y1), outline="black", width=3)
    for x in (200, 400):
        d.line((x, 200, x + 40, 200), fill="black", width=3)
        d.polygon(
            [(x + 40, 200), (x + 32, 196), (x + 32, 204)], fill="black"
        )
    d.text((90, 190), "Input", fill="black")
    d.text((290, 190), "Process", fill="black")
    d.text((490, 190), "Output", fill="black")
    img.save(p)


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
    test_in = ROOT / "test_input.png"
    test_out = ROOT / "test_output.png"
    make_test_png(test_in)
    print(f"prompt = {len(load_prompt())} chars")
    print("calling gemini ...")
    data = call_gemini(load_prompt(), test_in, api_key)
    if not data:
        print("FAILED")
        return 1
    test_out.write_bytes(data)
    print(f"OK -> {test_out} ({len(data)/1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
