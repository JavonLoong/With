# 4.4 视频逐帧波峰间距分析

## 结论

- 最合理平均波峰间距：**16.041 cm**
- 用于该平均值的帧数：41 / 136 帧
- 对应用于平均的逐帧离散度：标准差 2.257 cm，MAD 1.956 cm
- 仅直接相邻波峰检测得到的加权平均：16.041 cm
- 直接相邻波峰间距样本：88 个，样本中位数 16.065 cm

## 方法

1. 使用 ffmpeg 解码 `6.mp4` 的全部 136 帧，帧率 29.000000 fps。
2. 用背景直尺估计比例尺：30.158 px/cm，即 0.033158 cm/px。
3. 每帧提取水线，转为相对水面位移曲线 `eta(x,t)`。
4. 每帧先找相邻波峰并计算直接峰距；若当帧可见波峰不足，则用同一帧空间自相关作为 fallback。
5. 最终平均值优先采用逐帧直接相邻波峰的质量加权稳健截尾均值；只有直接波峰帧不足时才使用自相关 fallback。

## 输出文件

- `frame_peak_spacing_timeseries.csv`：逐帧完整时间序列。
- `direct_peak_interval_samples.csv`：每一对相邻波峰的间距样本。
- `summary_cn.csv` / `summary.json`：汇总统计。
- `peak_spacing_vs_time.png`：波峰间距随时间变化图。
- `waterline_and_peaks_contact_sheet.png`：抽样帧水线和波峰叠加复核图。
- `profile_peak_diagnostics.png`：抽样帧水线剖面与峰点复核图。
- `ruler_calibration_diagnostic.png`：直尺标定复核图。
