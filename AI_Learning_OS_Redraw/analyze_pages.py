"""用 Gemini 视觉模型分析每页 PPT，输出结构化 JSON 给 HTML 模板用。

输入：<workdir>/input/*.jpeg （或 *.png）
输出：<workdir>/content/<stem>.json

每页 JSON 形如：
{
  "page": "p002_x49",
  "layout": "two-card",            // cover | section | one-illu | two-card | three-card | comparison | closing
  "section_tag": "02 · 问题诊断",
  "page_title": "为什么\"刷题感觉对了\"，考试还是失分？",
  "cards": [
    {
      "key": "现象侧",
      "title": "\"能力错觉\"循环",
      "desc": "看答案能懂...一闭环就是认知陷阱。",
      "featured": false,
      "illu_bbox_pct": [0.04, 0.13, 0.49, 0.86]   // 在原图百分比坐标 (x1,y1,x2,y2)
    },
    ...
  ],
  "quote": "传统学习聚焦...的断裂。"
}
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from tqdm import tqdm

DEFAULT_API_KEY = "AIzaSyCU06SHHsQRDz9AVJttMeeVjAE4PcwxYeo"
MODEL = "gemini-2.5-flash"  # 用文本+视觉理解模型即可
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
SUPPORTED = {".png", ".jpg", ".jpeg", ".webp"}

PROMPT = """你是一名信息设计师。请分析这张 PPT 单页，把它**重构**为一个统一的现代模板格式（卡片化 + 紫色焦点 + 黑白线稿）。

输出 **纯 JSON**（不要 markdown 代码块、不要任何解释），结构如下：

{
  "layout": "cover | section | one-illu | two-card | three-card | comparison | closing",
  "section_tag": "短小章节号或主题，如 \\"02 · 问题诊断\\" 或 \\"\\"（无）",
  "page_title": "本页主问题/主题（一句话，最长 24 字）",
  "cards": [
    {
      "key": "短分类标签，如 \\"现象侧\\" \\"本质侧\\" \\"现状\\" \\"优化\\" 等（≤4 字）",
      "title": "卡片小标题（≤12 字）",
      "desc": "卡片描述（一句话，≤40 字）",
      "featured": false,
      "illu_bbox_pct": [0.04, 0.13, 0.49, 0.86]
    }
  ],
  "quote": "底部 quote（如有，≤40 字）",
  "notes": "你看到的页面整体含义（≤30 字）"
}

**关键规则**：
1. **layout 选择**：
   - 只有标题和大背景图 → cover
   - 章节过渡页（章节号大字） → section
   - 一张大示意图占主体 → one-illu (cards 数组只放 1 个)
   - 左右双列 / 双卡片对比 → two-card
   - 三列 / 三卡片 / 三步骤 → three-card
   - 表格对比 → comparison
   - 收尾 / 总结 / 仅一句话 → closing
2. **illu_bbox_pct** 是百分比坐标 (x1, y1, x2, y2)，0~1 之间，表示这张卡片对应的**结构插图**在原图中的位置。
   - 选**只包含图形**的区域，**避开**列标题、quote、章节号
   - cover/section/closing 通常不需要 bbox，写 null
3. **cards 数量**和 layout 匹配：cover/section/closing→0~1 个；one-illu→1；two-card→2；three-card→3；comparison→2-4
4. **featured**：原图中视觉焦点（紫色/红色/加粗框）的卡片为 true，其它 false
5. **缺失字段**用空字符串 "" 或 null
6. 所有文字必须是**中文**，字数严格控制在限制内

只输出 JSON。
"""


def load_existing(out_dir: Path, stem: str) -> Optional[dict]:
    p = out_dir / f"{stem}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def call_gemini(img_path: Path, api_key: str) -> Optional[dict]:
    mime = "image/jpeg" if img_path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    if img_path.suffix.lower() == ".webp":
        mime = "image/webp"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": PROMPT},
                    {"inline_data": {
                        "mime_type": mime,
                        "data": base64.b64encode(img_path.read_bytes()).decode("ascii"),
                    }},
                ],
            }
        ],
        "generationConfig": {"responseModalities": ["TEXT"], "temperature": 0.3},
    }
    url = f"{ENDPOINT}?key={api_key}"
    for attempt in range(1, 4):
        try:
            r = requests.post(url, headers={"Content-Type": "application/json"},
                              data=json.dumps(payload), timeout=120)
        except requests.RequestException as e:
            print(f"  ! req error: {e}")
            time.sleep(5)
            continue
        if r.status_code != 200:
            print(f"  ! HTTP {r.status_code}: {r.text[:200]}")
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(5 * attempt)
                continue
            return None
        try:
            data = r.json()
            text = ""
            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if part.get("text"):
                        text += part["text"]
            text = text.strip()
            # 去掉 markdown 代码块
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            return json.loads(text)
        except Exception as e:
            print(f"  ! parse error: {e}; raw[:300]={text[:300] if 'text' in locals() else ''}")
            time.sleep(3)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    in_dir = workdir / "input"
    out_dir = workdir / "content"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = []
    if args.files:
        for name in args.files:
            p = in_dir / name
            if p.exists():
                files.append(p)
    else:
        files = [p for p in sorted(in_dir.iterdir()) if p.suffix.lower() in SUPPORTED]

    api_key = os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
    print(f"待分析: {len(files)} 张 -> {out_dir}")

    ok = fail = skip = 0
    for p in tqdm(files, ncols=88):
        out_path = out_dir / f"{p.stem}.json"
        if out_path.exists() and not args.overwrite:
            skip += 1
            continue
        result = call_gemini(p, api_key)
        if result is None:
            fail += 1
            continue
        result["page"] = p.stem
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        ok += 1
    print(f"\n完成: 新生成 {ok} / 跳过 {skip} / 失败 {fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
