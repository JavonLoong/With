# 数据组 2.6 水波驻波/反射分析报告

## 处理概况

- 输入视频：`3.mp4`
- 逐帧读取：完整读取 881 帧，帧率 30.000 fps；有效分析帧 881 帧。
- 直尺标定：`18.956 px/cm`，使用背景直尺刻度周期诊断，未使用非直尺替代标定。
- 水面轮廓：逐帧提取水面线，生成 `eta(x,t)`，再进行入射/反射方向分离。

## 主要结果

| 项目 | 数值 |
|---|---:|
| 低反射稳定窗口 | 21.50--22.37 s |
| 稳定窗口反射/入射能量比 | 0.088 |
| 直接峰距 | 21.52 cm |
| 直接峰距样本数 | 27 |
| 分离后入射峰距 | 21.00 cm |
| 入射峰距样本数 | 27 |
| 入射自相关主周期 | 21.42 cm |
| 全帧 2D FFT 诊断波长 | 22.84 cm |
| 最终建议峰距 | 22.84 ± 0.50 cm |
| 直接-入射差值 | 0.53 cm |
| 相对差异 | 2.5% |

## 判断

**反射影响中等，建议纳入不确定度。**

本次修正版不再让单帧/相邻峰自动选择单独决定最终结果；单帧峰距只作为可视化复核。最终口径优先采用清理固定竖条伪影后的全帧 `x-t` 方向/频带诊断，并用可靠峰对图检查明显误选。

## 输出文件

- `standing_wave_cn_report.md`
- `standing_wave_summary_cn.csv`
- `standing_wave_judgement_cn.png`
- `wave_peak_measurement.png`
- `xt_raw_incident_reflected_panels.png`
- `reflection_strength.png`
- `ruler_calibration_diagnostic.png`
- `waterline_extraction_check.png`
- `masked_artifact_columns.png`
- `eta_xt_surface_cm.csv`
- `reflection_time_series.csv`
- `peak_measurements.csv`
- `ruler_calibration.csv`
- `standing_wave_analysis_data.npz`
- `standing_wave_final_cn_report.md`
- `standing_wave_final_summary_cn.csv`
- `intermediate_wave_measurement_3/overlay_sel_*.png`
- `run_standing_wave_analysis.py`
