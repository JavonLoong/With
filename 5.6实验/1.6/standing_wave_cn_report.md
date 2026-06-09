# 数据组 1.6 水波驻波/反射分析报告

## 处理概况

- 输入视频：`1.mp4`
- 逐帧读取：完整读取 1566 帧，帧率 30.000 fps；有效分析帧 1566 帧。
- 直尺标定：`34.179 px/cm`，使用背景直尺刻度周期诊断，未使用非直尺替代标定。
- 水面轮廓：逐帧提取水面线，生成 `eta(x,t)`，再进行入射/反射方向分离。

## 主要结果

| 项目 | 数值 |
|---|---:|
| 低反射稳定窗口 | 29.10--29.97 s |
| 稳定窗口反射/入射能量比 | 0.166 |
| 直接峰距 | 10.49 cm |
| 直接峰距样本数 | 20 |
| 分离后入射峰距 | 8.78 cm |
| 入射峰距样本数 | 43 |
| 入射自相关主周期 | 13.61 cm |
| 全帧 2D FFT 诊断波长 | 14.04 cm |
| 直接-入射差值 | 1.71 cm |
| 相对差异 | 19.5% |

## 判断

**需要考虑反射/驻波影响。**

最终口径优先参考低反射窗口内的直接峰距和方向分离后的入射峰距；全帧 2D FFT 只作为方向/频带诊断，不单独作为高精度最终波长。

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
- `ruler_calibration.csv`
- `standing_wave_analysis_data.npz`
- `run_standing_wave_analysis.py`
