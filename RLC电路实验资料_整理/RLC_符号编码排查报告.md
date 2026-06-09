# RLC 正式报告符号与编码排查报告

排查时间：2026-04-25  
排查范围：

- `D:\虚拟C盘\学习\RLC电路实验资料_整理\RLC_正式报告.tex`
- `D:\虚拟C盘\学习\RLC电路实验资料_整理\RLC_正式报告.pdf`
- `D:\虚拟C盘\学习\RLC电路实验资料_整理\RLC_正式报告.log`
- `D:\虚拟C盘\学习\RLC电路实验资料_整理\RLC_正式报告_预览`

本次只记录问题与建议，未修改 `tex/pdf/log/png` 文件。

## 总体结论

1. 当前 `RLC_正式报告.tex` 中 `kΩ` 写法已经是安全写法 `\mathrm{k}\Omega`，未再发现 `\mathrm{k\Omega}` 这种会把 `\Omega` 放进 `\mathrm{...}` 的风险写法。
2. 当前 `RLC_正式报告.pdf` 文本抽取未再出现 `k�`、`□`、乱码替代符或中文乱码；`5 kΩ`、`2.5 kΩ`、`2.83 kΩ`、`1.25 kΩ`、`4.0 kΩ` 等位置均可抽取为正常欧姆符号。
3. 当前 `RLC_正式报告.log` 中 `Missing character` 计数为 0，未发现与欧姆符号、微符号、希腊字母、角度符号或中文有关的缺字警告。
4. 预览目录中 `page_03.png` 仍是旧图，时间为 `2026/4/25 16:12:22`，肉眼可见表 1 中 `2.5 k□`。其他已更新预览页如 `page_05.png`、`page_11.png`、`page_13.png` 已显示为 `kΩ`。因此当前最主要的可见残留问题是预览图混用了新旧版本。

## 关键证据

### LaTeX 源

- `\Omega` 共检出 69 个相关位置，当前千欧写法均为 `\mathrm{k}\Omega`，例如：
  - 第 122 行：`\(5\ \mathrm{k}\Omega\)`
  - 第 164 行：`\(2.5\ \mathrm{k}\Omega\)`
  - 第 207 行：`\approx 2.83\ \mathrm{k}\Omega`
  - 第 703-705 行：`1.25/2.5/4.0 \mathrm{k}\Omega`
- `\mu` 共检出 14 个相关位置，均为数学模式写法，如 `\mu\mathrm{F}`、`\mu\mathrm{s}`，未发现直接输入的 `μ/µ` 混用风险。
- 未发现源码中存在直接的 `Ω`、`μ`、`□`、`�`、明显 mojibake 中文片段。
- 希腊字母和数学符号主要使用 `\beta`、`\omega`、`\varphi`、`\Delta`、`\Sigma`、`\delta`、`\tau`、`\pi` 等 LaTeX 命令，位于数学模式内，缺字风险低。
- 角度符号使用 `^\circ`，负号在数学模式中生成，表格缺失时间使用短横线 `--` 输出的 en dash；当前 PDF/预览未见方框。

### 编译日志

- 当前日志 `Missing character`：0。
- 未检出 `Undefined control sequence`、`Unicode character`、与符号缺字相关的错误。
- `pdffonts` 显示 Times New Roman、SimSun、SimHei、Computer Modern 数学字体均已嵌入。
- 日志中仍有 fontspec 信息：
  - `Could not resolve font "KaiTi/B"`
  - `Could not resolve font "SimHei/I"`
  - `Could not resolve font "SimSun/BI"`
  这些是粗体/斜体组合字体解析信息，当前未造成 Missing character 或可见方框；若后续大量使用中文斜体、粗斜体，建议显式配置 CJK 字族的 Bold/Italic/BoldItalic。

### PDF 与预览

- 当前 PDF 文本层未检出 `k�`、`□`、`�` 或中文乱码。
- 当前 PDF 中 `kΩ` 抽取结果显示为 `kΩ`，这是 Unicode 欧姆符号形态差异，不是缺字方框。
- 已更新预览页检查结果：
  - `page_05.png`：`2.5 kΩ` 显示正常；图 1 坐标轴、图例、`\ln(V_C)`、`\mu s` 正常。
  - `page_07.png`：幅频/相频图坐标轴、图例、`\varphi`、`0^\circ`、`kHz` 正常。
  - `page_11.png`：`R_c = 2.83 kΩ` 显示正常；`\beta`、`\tau`、`s^{-1}` 正常。
  - `page_13.png`：`R_f=2.5 kΩ`、`500 Ω`、`Q` 等显示正常。
- `page_03.png` 未更新，仍显示旧版 `2.5 k□`。该图时间早于当前 PDF 和大多数新预览图，应视为陈旧预览，不应作为最终交付依据。

## 问题清单

| 严重程度 | 问题 | 影响 | 建议修复 |
| --- | --- | --- | --- |
| 高 | `RLC_正式报告_预览\page_03.png` 是旧图，仍显示 `2.5 k□` | 用户查看预览目录时仍会看到欧姆符号方框，容易误判正式 PDF 未修复 | 从当前 PDF 重新生成全部预览页，至少重生成 `page_03.png`；生成前可清空旧预览或采用原子替换，避免混版 |
| 中 | 旧版 `\mathrm{k\Omega}` 会导致 `kΩ` 中的欧姆符号缺字 | 旧 PDF/旧预览出现 `k□`，影响单位可读性 | 保持当前写法 `\mathrm{k}\Omega`；也可统一为 `\mathrm{k}\,\Omega` 或引入 `siunitx` 管理单位 |
| 低 | fontspec 提示部分 CJK 粗斜体组合无法解析 | 当前未造成缺字；未来若使用中文粗斜体可能触发字体替代或样式不稳定 | 如需严格排版，显式设置 CJK `BoldFont`、`ItalicFont`、`BoldItalicFont`；当前报告可暂不处理 |
| 低 | PDF 文本抽取中 `Ω/Ω`、`μ/µ`、`°/◦` 可能使用不同 Unicode 码位 | 不影响视觉显示，但可能影响复制粘贴后的字符一致性 | 若要求文本层严格统一，建议用 `siunitx` 或 `unicode-math` 统一单位和数学字体策略 |

## 建议的最终交付前检查

1. 重新生成 `RLC_正式报告_预览` 全部页面，确认 `page_03.png` 时间晚于当前 PDF。
2. 对新预览再次肉眼检查含 `kΩ` 的页面，重点是表 1、阻尼理论比较、实验小结、思考题表 7。
3. 重新执行一次日志检查，确认 `Missing character` 仍为 0。
4. 保持源码中千欧单位为 `\mathrm{k}\Omega`，不要退回 `\mathrm{k\Omega}`。
