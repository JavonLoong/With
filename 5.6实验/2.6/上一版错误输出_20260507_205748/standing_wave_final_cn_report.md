# 数据组 2.6 驻波/反射修正版最终报告

## 最终结果

建议把相邻主波峰距离写作：`22.8 ± 0.5 cm`。

## 修正内容

- 直尺标定修正为 `18.956 px/cm`，不再把 1 cm 周期和 2 cm 候选周期混合取中位数。
- 分析区裁掉端部，并自动清理固定竖条伪影列。
- 单帧峰值选择改为可靠峰对：允许跳过内部伪峰；若没有接近目标波长的峰对，则不输出错误测量线。

## 判断

反射影响中等，建议纳入不确定度。最终口径优先采用清理后的全帧 `x-t` 方向/频带诊断；单帧峰距和复核图只用于检查是否有明显误选。

## 复核文件

- `standing_wave_summary_cn.csv`
- `standing_wave_judgement_cn.png`
- `intermediate_wave_measurement_3/peak_overlay_diagnostics.csv`
- `intermediate_wave_measurement_3/overlay_sel_00300.png`
- `intermediate_wave_measurement_3/overlay_sel_00420.png`
- `intermediate_wave_measurement_3/overlay_sel_00480.png`
- `intermediate_wave_measurement_3/overlay_sel_00800.png`
