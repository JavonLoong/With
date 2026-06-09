"""
对 input/ 下的每张图调用 gemini-2.5-flash 抽取所有可见中文文字 + 结构描述，
存到同名 .json 边车文件。后续 redraw.py 会读取它，
把"必须使用的文字"显式写进 prompt，显著降低中文字符幻觉。

用法：
    python ocr_extract.py --workdir AI_Learning_OS
    python ocr_extract.py --workdir AI_Learning_OS p001_x48.jpeg
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

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from redraw import DEFAULT_API_KEY, to_data_part  # noqa: E402

OCR_MODEL = "gemini-flash-latest"  # 503 时可换 gemini-2.5-flash-lite
OCR_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{OCR_MODEL}:generateContent"
)

OCR_PROMPT = """你是高精度 OCR 助手。请扫描这张图中的所有文字，输出严格 JSON：

{
  "title": "图的主标题（如果有显眼的标题文字，逐字抄写；否则空字符串）",
  "labels": ["按从上到下、从左到右顺序，把每一段独立可见的文字逐字列出"],
  "decorative_codes": ["仅那些明显是装饰性伪代码 / 工程标注的英文片段，如 WIDTH_1200、OFFSET_50、[MODE: XXX]、[NODE: XXX]、SYSTEM_INIT: TRUE、SCALE 1:1、v1.0、HEIGHT_xxx 等。注意：品牌/产品名 (例: AI_Learning_OS、OS_Core)、出现在中文句子里的字母 (例: 'AI 将...') 不要放进这里。"],
  "structure": "1-2 句话描述图的逻辑结构（中文）"
}

铁律：
- labels 必须逐字抄写，连标点、数字、引号、空格、换行都要完整保留；不许省略、不许翻译、不许改字。
- 中英文混排的句子（例如 "AI 将教材重组为..."）整段作为一个 label，不要拆开、不要把 AI 挑出来。
- 一个独立矩形框 / 卡片 / 段落 → 一个 label。
- 同一个 label 不要重复出现两次。
- 只输出 JSON，不要 markdown 包裹、不要解释。
"""

MAX_RETRIES = 3
RETRY_SLEEP = 4


def call_ocr(img_path: Path, api_key: str) -> dict | None:
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": OCR_PROMPT}, to_data_part(img_path)],
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
        },
    }
    url = f"{OCR_ENDPOINT}?key={api_key}"
    last_err = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=120,
            )
        except requests.RequestException as e:
            last_err = f"req: {e}"
            time.sleep(RETRY_SLEEP)
            continue
        if r.status_code != 200:
            last_err = f"HTTP {r.status_code}: {r.text[:300]}"
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(RETRY_SLEEP * attempt)
                continue
            break
        data = r.json()
        try:
            text = (
                data["candidates"][0]["content"]["parts"][0]["text"].strip()
            )
            # 模型偶尔会用 ```json 包裹，去掉
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip().rstrip("`").strip()
            return json.loads(text)
        except Exception as e:
            last_err = f"parse: {e} body={r.text[:300]}"
            time.sleep(RETRY_SLEEP)
    print(f"  ! {img_path.name} ocr failed: {last_err}")
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
    workdir = Path(args.workdir).resolve()
    src_dir = workdir / "input"
    ocr_dir = workdir / "ocr"
    ocr_dir.mkdir(exist_ok=True)

    if args.files:
        srcs = [src_dir / f for f in args.files if (src_dir / f).exists()]
    else:
        srcs = sorted(
            p
            for p in src_dir.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )

    ok, fail = 0, 0
    for src in tqdm(srcs, ncols=88):
        out = ocr_dir / (src.stem + ".json")
        if out.exists() and not args.overwrite:
            ok += 1
            continue
        res = call_ocr(src, api_key)
        if res is None:
            fail += 1
            continue
        out.write_text(
            json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        ok += 1
    print(f"OCR 完成: 成功 {ok} / 失败 {fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
