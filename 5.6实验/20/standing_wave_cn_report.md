# 数据组 20 水波驻波/反射分析报告

## 处理概况

- 输入视频：`ff6a1e97ef837bbe07835f23e14b277f.mp4`
- 逐帧读取：完整读取 121 帧，帧率 29.000 fps，视频时长 4.172 s，分辨率 1280×720 px；其中有效水面分析帧为 120 帧，剔除无效黑屏帧：120。
- 直尺标定：背景直尺刻度清楚可见，采用 210--160 cm 十厘米标号线性校验，并用 1 cm 刻度周期 FFT/自相关作独立诊断；标定结果为 **23.265 px/cm**。未使用替代标定。
- 水线提取：对 120 个有效水面帧逐帧提取水面轮廓，生成 `eta(x,t)`；黑屏帧无可用水线，未纳入 FFT/峰距统计；`eta` 为相对时均水线的竖向位移，单位 cm。
- 方向分析：对 `eta(x,t)` 做 2D FFT，按频率-波数符号分离入射波与反射波；全帧 FFT 主峰只作为诊断值。

## 主要结果

| 项目 | 数值 |
|---|---:|
| 低反射稳定窗口 | 2.28--3.00 s |
| 稳定窗口反射/入射能量比中位数 | 0.090 |
| 直接峰距中位数 | 28.24 cm |
| 直接峰距样本数 | 21 |
| 分离后入射剖面峰距中位数 | 29.79 cm |
| 入射峰距样本数 | 27 |
| 直接剖面自相关主周期 | 29.36 cm |
| 入射剖面自相关主周期 | 29.59 cm |
| 全帧 2D FFT 入射主峰诊断波长 | 39.12 cm |
| 直接-入射差值 | -1.55 cm |
| 相对差异 | 5.2% |

## 判断

**反射影响中等，建议把方向分离结果纳入不确定度。窗口反射/入射能量比中位数为 0.090，直接峰距与入射峰距相差 1.55 cm（5.2%）。**

本组视频约 4.17 s，横向有效视场约 49.0 cm；可用于峰距统计的完整波数有限。因此最终判断优先参考低反射窗口内的直接峰距与方向分离后的入射剖面峰距；全帧 2D FFT 的 39.12 cm 保留为方向分离/主频主波数诊断，不把它单独作为高精度最终波长。

## 质量与问题

- 直尺刻度可见，标定诊断图见 `ruler_calibration_diagnostic.png`；没有启用替代标定。
- 水线整体连续，但上方固定结构、局部反光和容器边缘会影响局部边缘响应；脚本用跨 x 中值滤波、异常点替换和 Savitzky-Golay 平滑处理。
- 原始剖面存在局部短峰；最终峰距统计先用低反射窗口自相关主尺度（约 29.48 cm）筛选宽峰，局部短峰保留在 `peak_measurements.csv` 中但不作为最终波长。
- 直接峰距样本数为 21，入射分量峰距样本数为 27；短视频和有限视场是主要不确定性来源。
- 反射分量并非全程可忽略；若使用全时段原始峰距，应考虑驻波/反射或继续采用方向分离。

## 输出文件

- `standing_wave_cn_report.md`
- `standing_wave_summary_cn.csv`
- `standing_wave_judgement_cn.png`
- `wave_peak_measurement.png`
- `xt_raw_incident_reflected_panels.png`
- `reflection_strength.png`
- `ruler_calibration_diagnostic.png`
- `waterline_extraction_check.png`
- `eta_xt_surface_cm.csv`
- `reflection_time_series.csv`
- `peak_measurements.csv`
- `spatial_autocorr_periods.csv`
- `ruler_calibration.csv`
- `standing_wave_analysis_data.npz`
- `run_standing_wave_analysis.py`
