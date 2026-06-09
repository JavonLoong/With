"""调用 nano-banana-pro / gemini-3-pro-image-preview 做"局部箭头替换"图编辑。

输入：
  --src   被编辑图（中间是杂乱剖面线小箭头）
  --ref   参考图（中间已经是干净蓝图风格箭头）
  --out   输出 PNG 路径

核心 prompt：仅替换中间箭头，其余像素严格保留。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import requests


DEFAULT_API_KEY = "AIzaSyCU06SHHsQRDz9AVJttMeeVjAE4PcwxYeo"
DEFAULT_MODEL = "nano-banana-pro-preview"
FALLBACK_MODELS = ["gemini-3-pro-image-preview", "gemini-2.5-flash-image"]
MAX_RETRIES = 3
RETRY_SLEEP = 6


PROMPT = """你将看到两张相关的图。第一张【待编辑图】是要被修改的源，第二张【参考图】只用来抄它中间那只箭头的视觉风格。

【唯一允许动的区域】
第一张图的"水平正中央、左右两个卡片之间的那一段空白带"——也就是连接左侧"表面现象"白板和右侧"解剖与归因卡"表格的中间过渡区。这块区域里目前画着两到三个杂乱的、剖面线乱画的、像 X 形交叉的小箭头，必须把这一组小箭头整体擦干净，换成下面描述的单只大箭头。

【中间箭头的目标样式（严格照第二张图重现）】
- 一只【单独的】右指箭头：左边是矩形箭杆，右边是等腰三角箭头部分，整体外轮廓粗黑实线
- 箭头内部白底，矩形杆和三角部分各填一组等距斜剖面线（约 45° hatching）
- 箭头四周散布若干淡淡的水平/竖直虚线（dashed construction lines）作为蓝图辅助线
- 大小占满原杂乱箭头所在的中间通道，水平居中
- 不要给箭头任何彩色、阴影、渐变；只允许黑白

【其它一切都必须像素级原样保留 — 这是最高优先级】
1. 左侧"表面现象"白板/翻折屏幕：
   - 顶部"表面现象"四个深色粗体字，位置、字号、字距 1:1 不变
   - 屏幕里手写体三行：
     "题目: 求 f(x) = x² 在 x = 3 处的导数"
     "错解: f(3) = 9, 所以导数为 9"
     "(混淆了函数值与导数概念)"
     ——一字不改，不许新增、不许丢字、不许换标点
   - 屏幕右下角那个**剖面线 X 叉号**必须保留，位置、大小、剖面线方向都不变
   - 屏幕外边的翻折立体感、卷角、辅助线都不动
2. 右侧"解剖与归因卡"5 段堆叠表格：
   - 顶部"解剖与归因卡"标题不变
   - 五段从上到下依次是：
     第 1 段：[题目表面信息]: 表面呈现的错题体征
     第 2 段：[真正考点与错误步骤]: 定位发生断裂的认知环节
     第 3 段：[错误根因剖析]: 缺失边界条件 / 模型判断失误   ← **紫色 #6B3FA0 高亮的就是这一行，不许飘到第 4 行**
     第 4 段：[下次触发条件]: 预判同类错误的变体场景
     第 5 段：[手术处方]: 生成对抗变式题与设定复测时间轴
   - 每个汉字、每个方括号、每个冒号都必须逐字一致；任何一个字写错都算失败
3. 底部"错题本不应是题目的堆积，而应是认知动作不稳定的精确记录。"文字框完全不动
4. 整张图配色严格只允许：纯白底 / 纯黑线 / 紫色 #6B3FA0（仅给那一行紫高亮）
   - 禁止出现任何蓝色、青色、红色、橙色、灰色块、米色背景、网格底纹
5. 线条粗细、手绘质感、画面留白、各对象的位置和大小，全部跟第一张图保持一致

【交付前自检清单】
- [ ] 中间杂乱小箭头已删除，替换为单只蓝图风格大箭头
- [ ] 左侧 X 叉号仍在原位
- [ ] 右侧紫色高亮在第 3 行（错误根因剖析）
- [ ] 五行括号标签和后面的中文一字不差
- [ ] 屏幕里三行手写文字一字不差
- [ ] 没有任何蓝/青/红/灰色出现
全部勾上才输出，否则重画。直接输出最终图，不要附文字说明。"""


def to_part(p: Path) -> dict:
    mime = "image/png"
    if p.suffix.lower() in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    return {
        "inline_data": {
            "mime_type": mime,
            "data": base64.b64encode(p.read_bytes()).decode("ascii"),
        }
    }


def call(model: str, src: Path, ref: Path, api_key: str, size: str | None) -> bytes | None:
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    gen_config: dict = {"responseModalities": ["IMAGE"]}
    if size:
        gen_config["imageConfig"] = {"imageSize": size}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": "【待编辑图】（第一张）"},
                    to_part(src),
                    {"text": "【参考图】（第二张，仅看中间箭头风格）"},
                    to_part(ref),
                    {"text": PROMPT},
                ],
            }
        ],
        "generationConfig": gen_config,
    }
    url = f"{endpoint}?key={api_key}"
    last_err = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=300,
            )
        except requests.RequestException as e:
            last_err = f"request error: {e}"
            time.sleep(RETRY_SLEEP)
            continue
        if r.status_code != 200:
            last_err = f"HTTP {r.status_code}: {r.text[:600]}"
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(RETRY_SLEEP * attempt)
                continue
            break
        data = r.json()
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                inline = part.get("inline_data") or part.get("inlineData")
                if inline and inline.get("data"):
                    return base64.b64decode(inline["data"])
        last_err = f"no inline_data: {json.dumps(data)[:600]}"
        time.sleep(RETRY_SLEEP)
    print(f"  [{model}] failed after {MAX_RETRIES}: {last_err}")
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--size", default="2K", choices=[None, "1K", "2K", "4K"])
    ap.add_argument("--no-fallback", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
    src = Path(args.src).resolve()
    ref = Path(args.ref).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    models_to_try = [args.model] + ([] if args.no_fallback else FALLBACK_MODELS)
    seen = set()
    for m in models_to_try:
        if m in seen:
            continue
        seen.add(m)
        print(f"[try] model={m} size={args.size}")
        result = call(m, src, ref, api_key, args.size)
        if result is not None:
            out.write_bytes(result)
            print(f"  ✓ 写入 {out} ({len(result)/1024:.1f} KB)")
            return 0
    print("全部模型都失败")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
