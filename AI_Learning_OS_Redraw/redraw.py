"""
调用 Gemini 2.5 Flash Image (nano-banana) 对图片进行风格重画。

用法：
    python redraw.py --workdir AI_Learning_OS                       # 重画 input/
    python redraw.py --workdir AI_Learning_OS --pages               # 重画 pages/
    python redraw.py --workdir AI_Learning_OS p001_x12.png ...      # 仅重画指定文件

API key 通过环境变量 GEMINI_API_KEY 传入；如果未设置，则回退到脚本顶部的常量。
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
from tqdm import tqdm


# ---- 配置 ---------------------------------------------------------------
DEFAULT_API_KEY = "AIzaSyCU06SHHsQRDz9AVJttMeeVjAE4PcwxYeo"
DEFAULT_MODEL = "gemini-2.5-flash-image"  # 可选: nano-banana-pro-preview / gemini-3-pro-image-preview / gemini-3.1-flash-image-preview
ROOT = Path(__file__).resolve().parent
PROMPT_FILE = ROOT / "style_prompt.txt"

MAX_RETRIES = 3
RETRY_SLEEP = 5  # 秒
SUPPORTED_INPUT = {".png", ".jpg", ".jpeg", ".webp"}
# ------------------------------------------------------------------------


def load_prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8").strip()


def build_prompt_for(img_path: Path, base_prompt: str, workdir: Path) -> str:
    """如果 workdir/ocr/<stem>.json 存在，则在 prompt 后追加“必须使用这些中文”的硬约束。"""
    ocr_file = workdir / "ocr" / (img_path.stem + ".json")
    if not ocr_file.exists():
        return base_prompt
    try:
        meta = json.loads(ocr_file.read_text(encoding="utf-8"))
    except Exception:
        return base_prompt
    parts = [base_prompt, "\n\n【本图中必须逐字出现且仅允许出现这些文字（不准增、不准减、不准改字）】"]
    title = (meta.get("title") or "").strip()
    subtitle = (meta.get("subtitle") or "").strip()
    if title:
        parts.append(f"主标题: {title}")
    if subtitle:
        parts.append(f"副标题: {subtitle}")
    labels = [s for s in (meta.get("labels") or []) if isinstance(s, str) and s.strip()]
    if labels:
        parts.append("标签列表（按阅读顺序）:")
        for i, lb in enumerate(labels, 1):
            parts.append(f"  {i}. {lb}")
    eng = [s for s in (meta.get("decorative_codes") or meta.get("english_to_remove") or []) if isinstance(s, str) and s.strip()]
    # 过滤掉品牌名等不该删的
    keep = {"AI_Learning_OS", "OS_Core", "AI"}
    eng = [e for e in eng if e.strip() not in keep]
    if eng:
        parts.append("【请在重画中完全删除这些装饰性英文/伪代码】")
        parts.append("  " + " / ".join(eng))
    structure = (meta.get("structure") or "").strip()
    if structure:
        parts.append(f"【原图逻辑结构】 {structure}")
    return "\n".join(parts)


def to_data_part(img_path: Path) -> dict:
    mime = "image/png"
    if img_path.suffix.lower() in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif img_path.suffix.lower() == ".webp":
        mime = "image/webp"
    return {
        "inline_data": {
            "mime_type": mime,
            "data": base64.b64encode(img_path.read_bytes()).decode("ascii"),
        }
    }


def call_gemini(
    prompt: str,
    img_path: Path,
    api_key: str,
    model: str = DEFAULT_MODEL,
    image_size: str | None = None,
) -> bytes | None:
    """返回重画后的图片二进制；失败返回 None。

    image_size: "1K" / "2K" / "4K"（仅 nano-banana-pro / gemini-3-pro-image 等新模型支持）。
    """
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    gen_config: dict = {"responseModalities": ["IMAGE"]}
    if image_size:
        gen_config["imageConfig"] = {"imageSize": image_size}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    to_data_part(img_path),
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
                timeout=180,
            )
        except requests.RequestException as e:
            last_err = f"request error: {e}"
            time.sleep(RETRY_SLEEP)
            continue
        if r.status_code != 200:
            last_err = f"HTTP {r.status_code}: {r.text[:500]}"
            # 速率/暂时性问题重试，4xx 永久错误直接停
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(RETRY_SLEEP * attempt)
                continue
            break
        data = r.json()
        # 解析 inline_data
        try:
            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    inline = part.get("inline_data") or part.get("inlineData")
                    if inline and inline.get("data"):
                        return base64.b64decode(inline["data"])
            last_err = f"no inline_data in response: {json.dumps(data)[:500]}"
        except Exception as e:
            last_err = f"parse error: {e}"
        time.sleep(RETRY_SLEEP)
    print(f"  ! failed after {MAX_RETRIES} retries: {last_err}")
    return None


def gather_targets(args) -> list[tuple[Path, Path]]:
    """返回 [(input_path, output_path), ...]"""
    workdir = Path(args.workdir).resolve()
    targets: list[tuple[Path, Path]] = []
    if args.pages:
        src_dir = workdir / "pages"
        dst_dir = workdir / "output_pages"
    else:
        src_dir = workdir / "input"
        dst_dir = workdir / "output"
    dst_dir.mkdir(parents=True, exist_ok=True)

    if args.files:
        for name in args.files:
            p = src_dir / name
            if not p.exists():
                print(f"  skip (not found): {p}")
                continue
            targets.append((p, dst_dir / (p.stem + ".png")))
    else:
        if not src_dir.exists():
            print(f"source dir not found: {src_dir}")
            return targets
        for p in sorted(src_dir.iterdir()):
            if p.suffix.lower() in SUPPORTED_INPUT:
                targets.append((p, dst_dir / (p.stem + ".png")))
    return targets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--workdir",
        required=True,
        help="PDF 抽取生成的子目录（包含 input/ pages/）",
    )
    ap.add_argument(
        "--pages",
        action="store_true",
        help="重画 pages/ 下整页渲染图（默认重画 input/ 下嵌入图片）",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="即使输出文件已存在也重新生成",
    )
    ap.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"图像生成模型名（默认 {DEFAULT_MODEL}）。可试: nano-banana-pro-preview / gemini-3-pro-image-preview",
    )
    ap.add_argument(
        "--size",
        default=None,
        choices=[None, "1K", "2K", "4K"],
        help="输出分辨率（仅 nano-banana-pro / gemini-3-pro-image 等新模型支持）",
    )
    ap.add_argument("files", nargs="*", help="可选：指定要处理的文件名")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
    if not api_key:
        print("ERROR: 未提供 GEMINI_API_KEY")
        return 1

    prompt = load_prompt()
    targets = gather_targets(args)
    if not targets:
        print("没有待处理的图片。")
        return 0

    workdir = Path(args.workdir).resolve()
    print(f"待重画: {len(targets)} 张  ->  model: {args.model}  ->  base prompt: {len(prompt)} 字符")
    ok, fail = 0, 0
    for src, dst in tqdm(targets, ncols=88):
        if dst.exists() and not args.overwrite:
            ok += 1
            continue
        full_prompt = build_prompt_for(src, prompt, workdir)
        result = call_gemini(full_prompt, src, api_key, model=args.model, image_size=args.size)
        if result is None:
            fail += 1
            continue
        dst.write_bytes(result)
        ok += 1
    print(f"\n完成: 成功 {ok} / 失败 {fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
