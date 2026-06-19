# MotionTwin Visual Agent Output

本目录为 `MotionTwin：XR 动作影分身训练` 的视觉规划交付物，只包含视觉/绘图 agent 输出，未修改其他 agent 目录。

## 文件索引

- `visual_plan.md`：逐页视觉规划，包含每页需要的图、构图、生成提示词、要避免的问题，以及流程图建议。
- `image_gen_prompts.md`：可直接复制到 image_gen 的 3 组关键图中英提示词。
- `reusable_flowcharts.mmd`：可复用 Mermaid 流程图草案，供主 agent 转成 PPT 中的可编辑流程图。
- `motiontwin_hero_xr_shadow.png`：真实训练者与蓝色 XR 影分身主视觉。
- `motiontwin_pose_heatmap_score.png`：动作误差热力图与姿态评分占位视觉。
- `motiontwin_application_matrix.png`：六宫格多场景应用矩阵视觉。

## 使用原则

- 位图生成图中不要放任何文字、数字、UI 标签或品牌标志。
- PPT 中所有标题、参数、评分、说明文字由主 agent 使用可编辑文本重排。
- 生成图优先保留右侧或上方负空间，便于后期排版。
- 蓝色 XR 影分身作为 MotionTwin 的主视觉识别符号，建议全稿统一使用。
