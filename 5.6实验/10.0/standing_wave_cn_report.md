# 10.0 水波视频驻波/反射分析报告

## 数据与标定
- 输入视频：`8b5f4cdec73a03c1e7ed911633b86d5b.mp4`。
- 完整逐帧读取：168 帧，fps=30.000，时长 5.60 s，画面 1280x720 px。
- 直尺标定：底部背景直尺刻度可见，使用刻度投影自相关估计，px/cm = 29.964 ± 0.064（n=12 个抽样帧）。未使用替代标定。
- x-t 分析视场：x=40..1219 px，宽度约 39.38 cm；eta(x,t) 由上方水面暗/亮界面逐列梯度提取并转成 cm。

## 方向分离与反射强度
- 2D FFT 方向判定：主入射方向为 `right`。
- 全片反射/入射能量比：0.524；对应幅值比 sqrt(E_ref/E_inc)≈0.724。
- 低反射稳定窗口：1.60--3.57 s，反射/入射能量比 0.030，幅值比≈0.174。

## 波长/峰距
- 低反射窗口直接宽峰距：24.00 ± 4.68 cm（n=6）。
- 直接局部峰距候选：10.49 ± 1.79 cm（n=18），用于提示局部纹理/次级峰，不单独作为最终波长。
- 分离后入射剖面峰距：23.02 ± 3.50 cm（n=9）。
- 入射分量 2D FFT 主波长：34.17 cm，周期约 0.47 s；状态：诊断值；短视频/视场有限，不作为唯一最终波长。

## 判断
- 低反射窗口内反射弱，可用于行波波长测量；全片后段反射明显，整体解释需考虑驻波/反射。
- 本视频只有约 5.6 s，且有效视场不足以稳定容纳多组长波波峰；因此不把全帧 2D FFT 峰值当作唯一高精度最终波长。更可靠的读数是低反射窗口内的直接宽峰距与分离后入射剖面峰距，两者共同约束波长范围。

## 主要输出
- `standing_wave_summary_cn.csv`：中文汇总表。
- `standing_wave_judgement_cn.png`：判断图。
- `wave_peak_measurement.png`：峰距测量图。
- `xt_raw_incident_reflected_panels.png`：原始/入射/反射 x-t 面板。
- `reflection_strength.png`：滑动窗口反射强度。
- `ruler_calibration_diagnostic.png`：直尺标定诊断。
- `surface_waterline_check.png`：surface/waterline 检查图。
- `eta_xt_core_data.npz`、`eta_xt_matrix_sampled.csv`、`wave_peak_distances.csv`、`reflection_windows.csv`：核心数据。
