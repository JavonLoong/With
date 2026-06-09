---
description: AI_Learning_OS 插画重画 → 裁切 → 渲染 → 校验 → 修复的完整工作流
---

# AI_Learning_OS 重画工作流

把 PDF 抽出的 input 图通过 Gemini 重画 → 切成卡片 → 嵌入 slideshow_v2.html，并在出问题时回滚 / 手修 / 单页重抽。

## 0. 一次性准备

- 确认 `style_prompt.txt` 顶部的两条硬约束仍在：
  - **硬约束 1（labels 必须逐字完整出现）**：禁止省略 `[Tech Stack Highlight]` 这类长说明段
  - **硬约束 2（装饰元素禁止压字）**：X 叉号 / 翻页角 / 箭头 / 吊钩 都不许遮挡任何文字
- 设环境变量 `GEMINI_API_KEY`，否则会用 `redraw.py` 顶部的 `DEFAULT_API_KEY`。

## 1. 全量重画（首次或大改 prompt 后）

```powershell
python redraw.py --workdir AI_Learning_OS --overwrite
```

- 输入：`AI_Learning_OS/input/*.jpeg`
- 输出：`AI_Learning_OS/output/*.png`（整页重画图）
- prompt：`style_prompt.txt` + `AI_Learning_OS/ocr/<page>.json` 自动拼接 labels 列表

## 2. 按 content 切卡片
// turbo
```powershell
python crop_illustrations.py --workdir AI_Learning_OS
```

- 读 `AI_Learning_OS/content/<page>.json` 里的 `illu_bbox_pct`
- 按比例从 `output/<page>.png` 切出 `illustrations/<page>_card<i>.png`
- ⚠️ **会覆盖 illustrations/，跑前确认 output 是当前想要的版本**

## 3. 渲染单文件 slideshow
// turbo
```powershell
python build_site.py --workdir AI_Learning_OS
```

- 输出：`AI_Learning_OS/slideshow_v2.html`（卡片版，base64 内嵌 illustrations/）
- 也可同时跑 `python build_slideshow.py --workdir AI_Learning_OS` 生成整页版 `slideshow.html`

## 4. 浏览器校验
// turbo
```powershell
Start-Process "d:\虚拟C盘\AI_Learning_OS_Redraw\AI_Learning_OS\slideshow_v2.html"
```

逐页检查：
- 文字是否被装饰（X / 箭头 / 翻页角）压住
- 长 labels（如 [Tech Stack Highlight]）是否完整出现
- 颜色是否只有黑 / 白 / 紫 #6B3FA0
- 中文是否有错字 / 重字

## 5. 单页重抽（局部修复）

针对个别坏页（如 `p007_x54`、`p013_x60`）：

```powershell
python redraw.py --workdir AI_Learning_OS --overwrite p007_x54.jpeg p013_x60.jpeg
python crop_illustrations.py --workdir AI_Learning_OS
python build_site.py --workdir AI_Learning_OS
```

⚠️ Gemini 抽卡随机性大，可能要重跑 2–3 次。**重跑前先备份当前 illustrations**：

```powershell
Copy-Item AI_Learning_OS/illustrations/p007_x54_card*.png AI_Learning_OS/illustrations/_backup/
```

## 6. 回滚（重抽变更糟时）

slideshow.html / slideshow_v2.html 内嵌了上一版 base64，可作为天然备份。

**从 slideshow.html 还原整页图（output/）**：

```powershell
python restore_from_slideshow.py --workdir AI_Learning_OS p007_x54 p013_x60
```

**从 slideshow_v2.html 还原卡片图（illustrations/）**：

```powershell
python restore_from_slideshow.py --workdir AI_Learning_OS --mode cards p007_x54 p013_x60
```

⚠️ 还原后**不要再跑 `crop_illustrations.py`**，否则又会被 output/ 里的旧版整页图覆盖。

## 7. 调整页面布局（不重画）

如果某页不该被切成多卡（如 p007 的两张图本质是一张），改 `content/<page>.json`：

```json
{
  "layout": "one-illu",
  "cards": [{
    "key": "...",
    "title": "...",
    "desc": "合并后的描述文字",
    "featured": true,
    "illu_bbox_pct": [0.0, 0.13, 1.0, 0.95]
  }]
}
```

支持的 layout：`two-card` / `three-card` / `one-illu` / `cover` / `section` / `closing` / `comparison`

改完跑 `crop_illustrations.py` + `build_site.py` 即可。

## 8. 手修单张插画（最后兜底）

当多次重抽都救不回来：直接 PS / GIMP 编辑 `illustrations/<page>_card<i>.png`，然后**只**跑：

```powershell
python build_site.py --workdir AI_Learning_OS
```

⚠️ 千万**不要**跑 `crop_illustrations.py`，会覆盖手修结果。

---

## 已知坑位 / 排错

| 症状 | 根因 | 处理 |
|---|---|---|
| 文字被 X / 箭头压住 | 模型违反硬约束 2 | 单页重抽 → 不行就手修 |
| 整段 [Tech Stack...] 文字消失 | 模型违反硬约束 1 | 单页重抽 → 不行就手修补文字框 |
| 中文重字 / 错字（"目目录"） | 模型抽卡随机 | 单页重抽 |
| 出现蓝 / 青 / 红色 | 配色规则被忽略 | 单页重抽 |
| illustrations 与 output 不同源 | 中途 restore 过 | 不要再跑 crop_illustrations，直接 build_site |
| 切卡片后只剩半张图 | content/*.json 的 illu_bbox_pct 不对 | 改 bbox 或换 layout 为 one-illu |

## 文件 / 目录速查

```
AI_Learning_OS/
├── input/         # 从 PDF 抽出的原始图（不动）
├── ocr/           # 每页 OCR 结果，喂给 prompt
├── content/       # 每页结构化数据（layout / cards / illu_bbox_pct / quote）
├── output/        # Gemini 重画的整页图
├── illustrations/ # 按 bbox 切出的卡片图
├── slideshow.html     # build_slideshow.py 产物（整页版）
└── slideshow_v2.html  # build_site.py 产物（卡片版，主用）
```

```
项目根/
├── redraw.py                    # 1. Gemini 重画
├── crop_illustrations.py        # 2. 按 bbox 切卡
├── build_site.py                # 3. 渲染卡片版 slideshow_v2.html
├── build_slideshow.py           # 3'. 渲染整页版 slideshow.html
├── restore_from_slideshow.py    # 6. 从 HTML 备份回滚
├── style_prompt.txt             # 风格 prompt + 硬约束
└── .windsurf/workflows/redraw-pipeline.md  # 本文件
```
