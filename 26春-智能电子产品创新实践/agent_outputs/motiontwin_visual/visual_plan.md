# MotionTwin 视觉规划文档

项目主题：`MotionTwin：XR 动作影分身训练`

角色定位：视觉/绘图 agent。本文只负责每页图像规划、生成提示词、构图建议、避错清单和可复用流程图建议。PPT 中所有文字由主 agent 以可编辑文本重排，位图中尽量不生成文字。

## 总体视觉方向

- 主视觉符号：真实训练者 + 半透明蓝色 XR 动作影分身。蓝色影分身既可以与真人并排，也可以与真人局部重叠。
- 辅助视觉符号：蓝色标准骨架、橙红误差骨架、关节热力图、姿态评分仪表形状、训练闭环箭头。
- 课程技术映射：混元3D/3D打印用于训练道具与可穿戴支架；讯飞智能体用于语音反馈；XR 用于影分身叠加；BrainCo/可穿戴用于生理和动作采集。
- 图像风格：明亮、干净、未来感适中、产品概念渲染。不要做成重赛博朋克、医疗恐怖、游戏海报或科幻机器人。
- 字体策略：生成图里不要出现文字、数字、logo、伪 UI 标签。主 agent 后期在 PPT 中覆盖可编辑标题、五段式正文和评分数值。

## 建议页序

### 第 1 页：封面 / 产品设想

页面目标：第一眼让老师明白 MotionTwin 是“动作影分身训练”。

需要的图：真实训练者与蓝色 XR 影分身并排/半重叠训练的主视觉。

构图建议：

- 16:9 横图。
- 真人在左侧或中左，蓝色影分身在右侧或与真人身体半重叠。
- 右上方或左上方保留干净负空间，放 PPT 标题。
- 影分身用蓝色发光骨架、透明体积和轨迹线，不要像实体机器人。

可用提示词：见 `image_gen_prompts.md` 的 `01 真实人与蓝色 XR 影分身并排/重叠训练`。

要避免：

- 画面出现英文标题、乱码、UI 字符。
- 影分身过于实体化，导致不像 XR。
- 真人姿势模糊或肢体畸形。
- 背景过暗，像游戏宣传图。

### 第 2 页：背景

页面目标：说明动作训练正在从“经验指导”走向“实时数字反馈”。

需要的图：运动、康复、舞蹈或校园训练的拼贴背景，中央有一条从现实训练到 XR 训练的视觉过渡。

构图建议：

- 左侧为传统训练场景：教练观察、学生练习、普通镜子。
- 右侧为 XR 增强训练：蓝色影分身、骨架轨迹、可穿戴传感器光点。
- 中间用渐变光带或空间网格表达技术升级。
- 不要放任何图中文字，标题和背景说明后期加。

中文提示词：

16:9 横版现代训练空间概念图，左侧表现传统动作训练场景，一名训练者在普通运动教室中练习，右侧过渡到 XR 增强训练场景，同一名训练者旁边出现半透明蓝色动作影分身和蓝色运动轨迹。画面中间用柔和光带和空间网格表现从经验训练到数字化实时反馈的升级。明亮、干净、真实摄影质感，适合大学课程 PPT 背景。不要任何文字、数字、logo、界面标签或水印。

English prompt:

A 16:9 landscape concept image showing the transition from traditional movement training to XR-enhanced digital feedback. On the left, a trainee practices in a normal training room with a coach-like observation feeling and a simple mirror. On the right, the same training context becomes XR-enhanced, with a translucent blue motion twin, glowing motion trails, and subtle wearable sensor light points. Use a soft light band and spatial grid in the middle to show the upgrade from experience-based coaching to real-time digital feedback. Bright, clean, realistic camera feel, suitable for a university presentation background. No text, no numbers, no logos, no UI labels, no watermark.

要避免：

- 不要让“教练”成为画面主角，重点应是训练方式升级。
- 不要出现可读海报、墙面字、设备品牌。
- 不要把 XR 做成沉重 VR 头盔展示；MotionTwin 的核心是动作影分身反馈。

### 第 3 页：问题

页面目标：表现传统动作训练中的三类痛点：看不见误差、反馈不及时、训练不可量化。

需要的图：一个训练者做动作，身上有若隐若现的错位骨架和模糊误差区域；旁边可有空白评分面板形状，但无文字。

构图建议：

- 画面中心是训练者动作。
- 真实身体轮廓上叠加一条灰色标准线和一条橙红偏差线。
- 关节错误处用轻微橙红热区显示。
- 可在右侧留一块空面板，后期写“反馈滞后”等问题。

中文提示词：

16:9 横版训练分析概念图，一名训练者正在做动作，身体上叠加半透明灰色标准姿态线和橙红色偏差姿态线，膝盖、肩膀、腰部附近有柔和橙红热区，表达动作误差难以被肉眼及时发现。右侧有极简空白数据面板形状和几条无文字占位线，但不能出现任何真实文字、数字、字母、logo 或水印。背景干净、浅灰训练室，专业、克制、易读。

English prompt:

A 16:9 landscape training analysis concept image. A trainee is performing a movement, with a semi-transparent gray reference pose line and a warm orange-red deviation pose line over the body. Soft orange-red heat zones appear around the knees, shoulders, and waist to show motion errors that are hard to see in time. On the right, include a minimal empty data panel shape and a few abstract placeholder lines only, with no real text, no numbers, no letters, no logos, and no watermark. Clean light-gray training room background, professional and readable.

要避免：

- 不要将错误热区画成伤口或医疗影像。
- 不要出现实际分数和文字。
- 不要用过多红色导致页面显得危险或压迫。

### 第 4 页：技术方案总览

页面目标：一页讲清 MotionTwin 的技术闭环。

需要的图：系统架构流程图，建议用 PPT 可编辑图形，不建议生成位图文字。

构图建议：

- 左到右流程：动作采集 -> 姿态识别 -> XR 影分身 -> 误差分析 -> 讯飞智能体反馈 -> 下一轮训练。
- 每个节点用一个图标或简短中文文本，均由主 agent 在 PPT 中编辑。
- 背景可以使用淡色蓝色空间网格。

可复用流程图：`reusable_flowcharts.mmd` 的第一个 Mermaid 图。

可选背景图提示词：

抽象 16:9 横版科技背景，浅灰训练空间叠加淡蓝空间网格、传感器光点和环形数据流线，画面干净，中央留出大片空白用于后期绘制可编辑流程图。不要任何文字、数字、logo、界面标签或水印。

English prompt:

An abstract 16:9 landscape technology background for a system architecture slide. Light gray training-space atmosphere with subtle blue spatial grid, sensor light points, and circular data-flow lines. Keep the center clean and open for editable flowchart shapes added later in PowerPoint. No text, no numbers, no logos, no UI labels, no watermark.

要避免：

- 不要让生成图自带流程图文字。
- 不要用复杂电路板背景抢走主流程。
- 不要把课程技术堆成无法看懂的大仪表盘。

### 第 5 页：课程技术如何落地

页面目标：把老师要求的课程技术与产品实现一一对应。

需要的图：四象限或放射状技术拼图，建议 PPT 可编辑绘制；背景可用四种无字小场景图。

构图建议：

- 中心放 MotionTwin 产品原型。
- 四周分别是：混元3D/3D打印、讯飞智能体、XR、BrainCo/可穿戴。
- 每个模块配一个视觉符号：3D模型/打印件、语音波纹、XR眼镜或空间叠加、腕带/头戴传感器。
- 模块文字由主 agent 后加。

中文提示词：

16:9 横版科技产品拼图视觉，画面中心是一个抽象的 MotionTwin 训练系统核心光环，四周分布四类无文字技术场景：3D 建模和 3D 打印训练道具、语音智能体的声波反馈、XR 空间中的蓝色影分身、可穿戴传感器采集动作与生理信号。每个区域只用图像表达，不出现文字、数字、logo、界面标签或水印。风格统一，明亮现代，蓝色为主但加入少量橙色和绿色点缀。

English prompt:

A 16:9 landscape technology collage for a product concept. In the center, show an abstract glowing core for the MotionTwin training system. Around it, show four no-text technology scenes: 3D modeling and 3D-printed training props, voice-agent soundwave feedback, a blue XR motion twin in spatial overlay, and wearable sensors collecting movement and physiological signals. Use imagery only, no text, no numbers, no logos, no UI labels, no watermark. Unified bright modern style, mostly blue with small orange and green accents.

要避免：

- 不要出现真实品牌 logo。
- 不要在图里写“XR”“AI”等字。
- 不要让 3D 打印和可穿戴看起来像无关硬件堆砌。

### 第 6 页：核心交互 - XR 动作影分身训练

页面目标：重点展示“真实人和蓝色 XR 影分身并排/重叠训练”。

需要的图：与第 1 页相似，但更强调交互过程：影分身显示标准姿态，真人跟练并调整。

构图建议：

- 使用近景或中景，让姿态更清楚。
- 影分身可以在真人前方半透明叠加，体现“跟着影子练”。
- 增加轻量箭头轨迹线，但不要文字。

中文提示词：

16:9 横版 XR 动作训练交互场景，一名训练者正在跟随半透明蓝色动作影分身调整姿态。蓝色影分身与真人身体部分重叠，显示标准动作轨迹；真人动作略有偏差但正在向影分身对齐。加入少量蓝色轨迹线、关节点光点和空间定位网格，体现实时跟练。室内训练场景明亮干净，产品概念渲染质感。不要任何文字、数字、logo、界面标签或水印。

English prompt:

A 16:9 landscape XR movement-training interaction scene. A trainee is adjusting their body posture by following a translucent blue motion twin. The blue twin partially overlaps the real body and shows the reference motion trajectory. The real movement is slightly offset but visibly aligning toward the twin. Add subtle blue motion trails, joint light points, and spatial tracking grid to suggest real-time practice. Bright clean indoor training environment, high-quality product concept render. No text, no numbers, no logos, no UI labels, no watermark.

要避免：

- 不要让影分身与真人距离太远，否则不像实时纠错。
- 不要把轨迹线做得太乱。
- 不要让真人佩戴过于笨重的头显，除非主 agent 明确需要。

### 第 7 页：动作误差热力图 / 姿态评分

页面目标：展示 MotionTwin 的可量化反馈能力。

需要的图：动作误差热力图 + 姿态评分视觉。

构图建议：

- 中央人体骨架叠加蓝色标准动作和橙色偏差动作。
- 右侧预留仪表盘占位，但不要实际文字和数字。
- 可让主 agent 在 PPT 上添加“膝关节偏移 12°”“姿态评分 86”等可编辑文本。

可用提示词：见 `image_gen_prompts.md` 的 `02 动作误差热力图 / 姿态评分视觉`。

要避免：

- 不要让生成模型写分数，容易出现错字或乱码。
- 不要用真实医疗诊断风格，课程产品应更像训练反馈。
- 不要让骨架线遮住人体太多，影响理解。

### 第 8 页：讯飞智能体反馈

页面目标：表现“看见错误 + 听到指导”的多模态反馈。

需要的图：训练者旁边出现抽象语音波纹和蓝色影分身提示动作修正。

构图建议：

- 真人与影分身位于左侧或中间。
- 右侧用声波环、对话气泡轮廓、发光提示线表达语音智能体，但不要文字。
- 可在 PPT 中后期加“把膝盖向外打开一点”等可编辑语句。

中文提示词：

16:9 横版智能训练反馈场景，一名训练者正在做动作，旁边有半透明蓝色 XR 影分身进行姿态对齐提示。画面右侧出现抽象语音波纹、发光声波环和无文字对话气泡轮廓，表达智能体正在给出语音反馈。整体明亮、现代、干净，训练空间真实，科技感适中。不要任何文字、数字、字母、logo、界面标签或水印。

English prompt:

A 16:9 landscape intelligent training feedback scene. A trainee is performing a movement while a translucent blue XR motion twin gives posture alignment guidance. On the right side, show abstract voice waveforms, glowing sound rings, and empty speech-bubble silhouettes with no text, representing an AI voice agent giving feedback. Bright, modern, clean real training space with moderate tech feeling. No text, no numbers, no letters, no logos, no UI labels, no watermark.

要避免：

- 不要生成对话框文字。
- 不要把智能体拟人化成单独机器人或虚拟人，重点是训练反馈。
- 不要出现真实讯飞 logo，品牌名由 PPT 文本说明即可。

### 第 9 页：多场景应用矩阵

页面目标：展示 MotionTwin 能用于体育、舞蹈、康复、校园、工业、居家等多场景。

需要的图：2x3 应用场景矩阵。

构图建议：

- 六个格子：体育训练、舞蹈练习、康复训练、校园体育课、工业安全动作训练、居家健身。
- 每格都有统一蓝色影分身，建立品牌一致性。
- 每格保留上方小空间，主 agent 添加可编辑标题。

可用提示词：见 `image_gen_prompts.md` 的 `03 多场景应用矩阵`。

要避免：

- 不要让每格风格不一致。
- 不要生成场景标题文字。
- 不要把康复场景画得过度医疗化。
- 不要在工业场景中出现危险事故画面，表达安全训练即可。

### 第 10 页：预期成效

页面目标：展示 MotionTwin 让训练更快纠错、更可量化、更个性化。

需要的图：前后对比式视觉。左侧为动作偏差热区较多，右侧为与蓝色影分身更贴合；中间有进步箭头。

构图建议：

- 左侧人体有橙红热区，右侧人体与蓝色影分身几乎重合。
- 中间可用无文字箭头或光带表达提升。
- 下方留空间放三项可编辑指标。

中文提示词：

16:9 横版训练成效对比图，左侧是一名训练者动作偏差较明显，身体周围有少量橙红误差热区和偏移骨架；右侧是同一训练者动作改进后与半透明蓝色 XR 影分身高度对齐，热区减少，蓝色轨迹更稳定。中间用简洁发光箭头或光带表示从训练前到训练后的提升。画面专业、明亮、干净，不出现任何文字、数字、logo、界面标签或水印。

English prompt:

A 16:9 landscape training outcome comparison visual. On the left, a trainee shows noticeable movement deviation with a few orange-red error heat zones and an offset skeleton. On the right, the same trainee after improvement is highly aligned with a translucent blue XR motion twin, with fewer heat zones and more stable blue motion trails. Use a clean glowing arrow or light band in the center to suggest improvement from before to after. Professional, bright, clean. No text, no numbers, no logos, no UI labels, no watermark.

要避免：

- 不要生成“Before/After”字样。
- 不要在右侧加真实分数数字。
- 不要把左侧错误画得过度夸张，保持可信。

### 第 11 页：课程收获

页面目标：把课程技术学习转化为产品创新能力。

需要的图：从课堂技术模块到 MotionTwin 原型的成长路径图，建议用 PPT 可编辑流程图。

构图建议：

- 左侧四个课程技术模块，右侧汇聚成 MotionTwin。
- 底部可以用“观察需求 -> 设计系统 -> 做原型 -> 评估迭代”的流程。
- 视觉上使用干净线框图和少量图标，不要依赖位图文字。

可复用流程图：`reusable_flowcharts.mmd` 的第二个 Mermaid 图。

可选背景图提示词：

16:9 横版清爽课堂创新背景，桌面上有 3D 打印小道具、可穿戴传感器原型、XR 眼镜轮廓和训练动作草图，远处有柔和蓝色空间网格。画面像课程项目展示，不出现任何文字、数字、logo、界面标签或水印。上方和右侧保留大片空白，用于 PPT 添加课程收获文字。

English prompt:

A clean 16:9 landscape classroom innovation background. On a desk, show small 3D-printed training props, a wearable sensor prototype, an XR glasses silhouette, and motion-training sketches. In the distance, add a soft blue spatial grid. The image should feel like a university course project showcase. No text, no numbers, no logos, no UI labels, no watermark. Leave large clean space on the top and right for editable slide text.

要避免：

- 不要让画面变成普通实验室堆物。
- 不要出现黑板字、纸张字或品牌 logo。
- 不要让课程收获页看起来像商业广告页。

## 精简五页版建议

如果主 agent 只做严格五段式，可以压缩为：

1. 背景：传统训练到 XR 训练升级图。
2. 问题：动作偏差热区和不可量化痛点图。
3. 技术方案：真人 + 蓝色 XR 影分身主视觉，配可编辑技术闭环。
4. 预期成效：训练前后对比 + 姿态评分占位图。
5. 课程收获：课程技术模块汇聚到 MotionTwin 的可编辑流程图。

## 统一负面提示词

建议每次生成图都追加：

中文：

不要任何文字、数字、字母、乱码、logo、水印、品牌标志、真实 UI 标签；不要肢体畸形、多人拥挤、阴暗赛博朋克、恐怖医疗感、过度卡通、过度复杂仪表盘。

English:

No text, no numbers, no letters, no gibberish, no logos, no watermark, no brand marks, no readable UI labels; no distorted limbs, no crowded groups, no dark cyberpunk mood, no scary medical feeling, no cartoon style, no overly complex dashboard.

## 给主 agent 的流程图建议

- 技术闭环图：使用 `reusable_flowcharts.mmd` 第一个图，适合第 4 页。
- 课程技术映射图：使用 `reusable_flowcharts.mmd` 第二个图，适合第 5 或第 11 页。
- 实时纠错逻辑图：使用 `reusable_flowcharts.mmd` 第三个图，适合补充技术方案页。
- 应用矩阵结构：使用 `reusable_flowcharts.mmd` 第四个图，适合第 9 页的文字骨架。

## 已生成关键图文件

本目录已按以下文件名保存 3 张关键位图，可直接供 PPT 选用：

- `motiontwin_hero_xr_shadow.png`
- `motiontwin_pose_heatmap_score.png`
- `motiontwin_application_matrix.png`

对应源提示词保留在 `image_gen_prompts.md`，便于复现和迭代。
