# AI_Learning_OS — 风格重画流水线

把一份 NotebookLM 导出的 PPT/PDF 中所有"有结构的部分"用
**极简线条结构主义 (Minimalist Structuralism)** + **高级商务/学术手绘感**
风格重画，使用 Google Gemini `nano-banana` (gemini-2.5-flash-image)。

## 文件结构
```
AI_Learning_OS_Redraw/
├── style_prompt.txt        # 风格 prompt（重画指令）
├── extract_images.py       # 从 PDF 抽取嵌入图 + 整页渲染
├── redraw.py               # 调用 Gemini API 重画
├── build_review.py         # 生成左右对照 HTML
├── test_api.py             # 测 API key 是否可用
├── requirements.txt
├── input/                  # 抽取出的嵌入图（自动生成）
├── pages/                  # 整页渲染图（自动生成）
├── output/                 # 重画后的嵌入图
└── output_pages/           # 重画后的整页图
```

## 快速使用

```powershell
# 1. 装依赖
pip install -r requirements.txt

# 2. 测 API key 是否可用
python test_api.py

# 3. 把 PDF 放到当前目录，抽图（每个 PDF 自动建独立子目录）
python extract_images.py .\AI_Learning_OS.pdf
python extract_images.py .\AI_Learning_OS_Blueprint.pdf

# 4. OCR 抽取每张图的精确中文文字（喂给重画做约束，大幅降低中文字符幻觉）
python ocr_extract.py --workdir AI_Learning_OS
python ocr_extract.py --workdir AI_Learning_OS_Blueprint

# 5. 重画 — 推荐用 nano-banana-pro-preview，中文质量明显更好
python redraw.py --workdir AI_Learning_OS              --model nano-banana-pro-preview
python redraw.py --workdir AI_Learning_OS_Blueprint    --model nano-banana-pro-preview

# 6. 生成对照 HTML
python build_review.py --workdir AI_Learning_OS
python build_review.py --workdir AI_Learning_OS_Blueprint
# 浏览器打开 ./<workdir>/review.html
```

## 模型对比
| 模型                          | 速度    | 中文质量          | 风格转换    |
|------------------------------|--------|------------------|------------|
| `gemini-2.5-flash-image`     | 快 ~13s | ~50% 中文乱码    | 偶尔保留原色 |
| `nano-banana-pro-preview`    | 慢 ~30s | **~95% 中文准确** | **基本完全转换** |

实测 30 张图：用 pro 模型，约 27/30 一次出图即可，剩下 3 张可单独重跑。

## API key
脚本内置默认 key，或通过环境变量覆盖：
```powershell
$env:GEMINI_API_KEY = "你的 key"
```

## 风格定制
直接编辑 `style_prompt.txt`，无需改代码。
