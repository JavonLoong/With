# 8.5 水波视频驻波/反射分析报告

## 数据与标定

- 输入视频：`eb84ad233085c38dae1687a33b4dc52f.mp4`
- 完整逐帧读取：98 帧，29.000 fps，时长 3.379 s。
- 直尺标定：28.8000 ± 0.2275 px/cm。直尺刻度清晰可见，本次使用直尺 1 mm 刻度网格估计 cm 标定，没有采用替代比例。
- 水面线 ROI：x=5:1275 px，y=129:400 px。`surface_waterline_check.png` 给出了逐帧抽样覆盖检查。

## x-t 与方向分离

- 2D FFT 方向能量判断的入射方向：向右。
- 全局 FFT 反向/入射能量比：0.0288，对应幅值比约 0.170。
- 低反射稳定窗口：frame 25-53，t=0.862-1.828 s。
- 窗口内反射/入射幅值比：0.1809；能量比：0.0315。

短视频只有 3.38 s，空间视场约 44.10 cm；因此全帧 2D FFT 的波长值只作为方向与主尺度诊断，不作为唯一高精度最终波长。

## 峰距/波长对照

| 项目 | 结果 |
|---|---:|
| 低反射窗口直接宽峰距 | 22.01 ± 1.59 cm（n=12，median=21.93 cm） |
| 分离后入射分量宽峰距 | 22.14 ± 2.51 cm（n=38，median=21.53 cm） |
| 直接局部峰距 | 11.36 ± 2.62 cm（n=9，median=11.25 cm） |
| 入射 FFT 波长（诊断） | 22.05 cm |
| 入射 FFT 次级尺度（诊断） | 11.02 cm |

直接宽峰距与入射分量剖面峰距互相接近，且反射能量较低。局部峰距反映表面剖面中的次级短尺度起伏，不建议把它直接替代主入射波长。

## 判断

不需要把强驻波/强反射作为主模型；以低反射窗口直接宽峰距和入射分量峰距为主。

本批次最终建议：主波长优先采用低反射稳定窗口中的直接宽峰距与分离后入射剖面峰距交叉约束；FFT 波长在报告中标为诊断值，用于验证方向、反射强度和主尺度是否一致。

## 输出文件

- `analyze_standing_wave_8_5.py`
- `standing_wave_cn_report.md`
- `standing_wave_summary_cn.csv`
- `standing_wave_judgement_cn.png`
- `wave_peak_measurement.png`
- `xt_raw_incident_reflected_panels.png`
- `reflection_strength.png`
- `ruler_calibration_diagnostic.png`
- `surface_waterline_check.png`
- `frame_inspection_contact.png`
- `waterline_eta_xt.csv`
- `waterline_eta_xt.npz`
- `ruler_calibration_samples.csv`
- `fft_directional_summary.csv`
- `reflection_window_metrics.csv`
- `peak_measurements.csv`
- `analysis_manifest.csv`

## 注意事项

- 视频时长短、样本数少，视场内完整波数有限。
- 水面线在局部反光/边界处有轻微噪声，已通过抽样覆盖图和峰距图人工复核。
- 未写入或删除旧的 `水波分析结果` 子目录。
