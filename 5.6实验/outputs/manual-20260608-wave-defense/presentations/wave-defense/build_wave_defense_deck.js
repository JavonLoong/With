const path = require("path");
const pptxgen = require("pptxgenjs");
const sizeOf = require("image-size");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.subject = "水波波速与水深关系探究答辩版";
pptx.title = "水波波速与水深关系探究";
pptx.company = "Tsinghua University";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei UI",
  bodyFontFace: "Microsoft YaHei UI",
  lang: "zh-CN",
};
pptx.margin = 0;

const W = 13.333;
const H = 7.5;
const assets = "D:/Users/15410/AppData/Local/Temp/wave_review_latest/final_assets";
const outDir = "D:/虚拟C盘/学习/outputs/manual-20260608-wave-defense/presentations/wave-defense/output";
const outPptx = path.join(outDir, "水波波速与水深关系探究_答辩高分版.pptx");

const C = {
  purple: "6F1D8F",
  purple2: "7A2A9E",
  deep: "24152E",
  deep2: "2A1636",
  ink: "1C1722",
  mute: "625B6B",
  line: "D8C6E1",
  bg: "FAF8FC",
  lavender: "F1E8F6",
  lavender2: "E8D8EF",
  rose: "9F3E76",
  roseLight: "F5E8F0",
  plum: "A75BA8",
  white: "FFFFFF",
  black: "000000",
};

const FONT = "Microsoft YaHei UI";

function img(name) {
  return path.join(assets, name);
}

function addBg(slide, opts = {}) {
  slide.background = { color: opts.color || C.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: 0.16,
    fill: { color: C.purple },
    line: { color: C.purple },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: H - 0.08,
    w: W,
    h: 0.08,
    fill: { color: C.purple },
    line: { color: C.purple },
  });
}

function addLogo(slide, color = "purple") {
  const logo = color === "white" ? img("tsinghua_logo_white.png") : img("tsinghua_logo.png");
  slide.addImage({
    path: logo,
    x: 11.25,
    y: 0.35,
    w: 1.55,
    h: 0.56,
    transparency: color === "white" ? 0 : 0,
  });
}

function title(slide, kicker, main, sub, n) {
  addBg(slide);
  addLogo(slide);
  slide.addText(kicker, {
    x: 0.68,
    y: 0.43,
    w: 2.2,
    h: 0.28,
    fontFace: FONT,
    fontSize: 9,
    bold: true,
    color: C.purple,
    charSpace: 1.2,
    margin: 0,
  });
  slide.addText(main, {
    x: 0.68,
    y: 0.82,
    w: 10.1,
    h: 0.64,
    fontFace: FONT,
    fontSize: 27,
    bold: true,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 0.68,
    y: 1.72,
    w: 2.65,
    h: 0,
    line: { color: C.purple2, width: 2.1 },
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 3.42,
    y: 1.72,
    w: 9.05,
    h: 0,
    line: { color: C.line, width: 1.1 },
  });
  slide.addText(String(n).padStart(2, "0"), {
    x: 12.27,
    y: 6.82,
    w: 0.48,
    h: 0.25,
    fontFace: FONT,
    fontSize: 8.5,
    color: C.mute,
    align: "right",
    margin: 0,
  });
}

function tag(slide, text, x, y, color = C.purple, bg = C.lavender) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w: text.length * 0.16 + 0.55,
    h: 0.32,
    rectRadius: 0.06,
    fill: { color: bg },
    line: { color: bg },
  });
  slide.addText(text, {
    x: x + 0.16,
    y: y + 0.07,
    w: text.length * 0.16 + 0.2,
    h: 0.16,
    fontFace: FONT,
    fontSize: 8,
    bold: true,
    color,
    margin: 0,
    breakLine: false,
  });
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: opts.fill || C.white },
    line: { color: opts.line || C.line, width: opts.lineWidth || 1 },
    shadow: opts.shadow === false ? undefined : { type: "outer", color: "D8D0E1", opacity: 0.18, blur: 1, angle: 45, distance: 1 },
  });
}

function bulletList(slide, bullets, x, y, w, opts = {}) {
  const fs = opts.fontSize || 13;
  const gap = opts.gap || 0.5;
  bullets.forEach((b, i) => {
    const yy = y + i * gap;
    slide.addShape(pptx.ShapeType.ellipse, {
      x,
      y: yy + 0.1,
      w: 0.12,
      h: 0.12,
      fill: { color: opts.dot || C.purple },
      line: { color: opts.dot || C.purple },
    });
    slide.addText(b, {
      x: x + 0.25,
      y: yy,
      w,
      h: gap,
      fontFace: FONT,
      fontSize: fs,
      color: opts.color || C.ink,
      margin: 0,
      fit: "shrink",
      breakLine: false,
      valign: "mid",
    });
  });
}

function metric(slide, value, label, x, y, w, color = C.purple) {
  card(slide, x, y, w, 1.05, { fill: C.white, line: "E6DEE9" });
  slide.addText(value, {
    x: x + 0.22,
    y: y + 0.18,
    w: w - 0.44,
    h: 0.36,
    fontFace: FONT,
    fontSize: 20,
    bold: true,
    color,
    margin: 0,
    fit: "shrink",
  });
  slide.addText(label, {
    x: x + 0.22,
    y: y + 0.62,
    w: w - 0.44,
    h: 0.26,
    fontFace: FONT,
    fontSize: 9.5,
    color: C.mute,
    margin: 0,
    fit: "shrink",
  });
}

function metricRich(slide, runs, label, x, y, w, color = C.purple) {
  card(slide, x, y, w, 1.05, { fill: C.white, line: "E6DEE9" });
  slide.addText(runs.map((r) => ({
    text: r.text,
    options: {
      fontFace: r.fontFace || "Aptos",
      fontSize: r.fontSize || 20,
      bold: r.bold !== false,
      color: r.color || color,
      italic: r.italic || false,
      subscript: r.subscript || false,
      baseline: r.baseline,
    },
  })), {
    x: x + 0.22,
    y: y + 0.16,
    w: w - 0.44,
    h: 0.42,
    margin: 0,
    fit: "shrink",
  });
  slide.addText(label, {
    x: x + 0.22,
    y: y + 0.62,
    w: w - 0.44,
    h: 0.26,
    fontFace: FONT,
    fontSize: 9.5,
    color: C.mute,
    margin: 0,
    fit: "shrink",
  });
}

function formulaText(slide, runs, x, y, w, h, opts = {}) {
  slide.addText(runs.map((r) => ({
    text: r.text,
    options: {
      fontFace: r.fontFace || "Aptos",
      fontSize: r.fontSize || opts.fontSize || 22,
      bold: r.bold || false,
      italic: r.italic || false,
      color: r.color || opts.color || C.ink,
      subscript: r.subscript || false,
      superscript: r.superscript || false,
      baseline: r.baseline,
    },
  })), {
    x,
    y,
    w,
    h,
    margin: 0,
    fit: "shrink",
  });
}

function addImageCard(slide, imagePath, x, y, w, h, caption) {
  card(slide, x, y, w, h, { fill: C.white, line: "E9E2EE" });
  const box = containImage(imagePath, x + 0.15, y + 0.15, w - 0.3, h - (caption ? 0.55 : 0.3));
  slide.addImage({ path: imagePath, ...box });
  if (caption) {
    slide.addText(caption, {
      x: x + 0.22,
      y: y + h - 0.36,
      w: w - 0.44,
      h: 0.18,
      fontFace: FONT,
      fontSize: 7.8,
      color: C.mute,
      align: "center",
      margin: 0,
    });
  }
}

function containImage(imagePath, x, y, w, h) {
  const dim = sizeOf(imagePath);
  const imgRatio = dim.width / dim.height;
  const boxRatio = w / h;
  let ww = w;
  let hh = h;
  if (imgRatio > boxRatio) {
    hh = w / imgRatio;
  } else {
    ww = h * imgRatio;
  }
  return {
    x: x + (w - ww) / 2,
    y: y + (h - hh) / 2,
    w: ww,
    h: hh,
  };
}

function slide1() {
  const s = pptx.addSlide();
  s.background = { color: C.deep };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.deep }, line: { color: C.deep } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.purple, transparency: 12 }, line: { transparency: 100 } });
  s.addShape(pptx.ShapeType.arc, { x: 7.1, y: -1.2, w: 5.7, h: 5.7, line: { color: "B64ACB", transparency: 35, width: 3 }, adjustPoint: 0.3 });
  s.addImage({ path: img("setup_water.png"), ...containImage(img("setup_water.png"), 7.05, 3.75, 5.15, 2.32), transparency: 20 });
  s.addImage({ path: img("tsinghua_logo.png"), x: 0.68, y: 0.55, w: 1.92, h: 0.7 });
  s.addText("水波波速与水深关系探究", {
    x: 0.82,
    y: 1.65,
    w: 8.7,
    h: 0.65,
    fontFace: FONT,
    fontSize: 31,
    bold: true,
    color: C.white,
    margin: 0,
    fit: "shrink",
  });
  s.addText("基于视频波场重建的平均波长与表观波速诊断", {
    x: 0.84,
    y: 2.4,
    w: 7.5,
    h: 0.36,
    fontFace: FONT,
    fontSize: 15.2,
    color: "E8DDF0",
    margin: 0,
  });
  s.addShape(pptx.ShapeType.line, { x: 0.84, y: 3.1, w: 6.4, h: 0, line: { color: "C7A4D5", width: 1.2 } });
  s.addText("答辩重点：不把表观速度包装成相速度，而是解释数据为什么偏离理想模型", {
    x: 0.86,
    y: 3.45,
    w: 6.4,
    h: 0.64,
    fontFace: FONT,
    fontSize: 15.5,
    bold: true,
    color: C.white,
    margin: 0,
    fit: "shrink",
  });
  s.addText("纪文龙  白子恒  秦健淞  丘洪源  杨天皓", {
    x: 0.88,
    y: 6.3,
    w: 5.5,
    h: 0.25,
    fontFace: FONT,
    fontSize: 10.8,
    color: "EADAF0",
    margin: 0,
  });
  s.addText("2026.5", {
    x: 0.88,
    y: 6.68,
    w: 1.2,
    h: 0.2,
    fontFace: FONT,
    fontSize: 9,
    color: "CDB4D7",
    margin: 0,
  });
}

function slide2() {
  const s = pptx.addSlide();
  title(s, "CONCLUSION FIRST", "结论先行：这不是一个简单的“水深越大波速越大”实验", "核心贡献是把可测量量、理论量和偏差来源分清楚", 2);
  s.addText("一句话结论", { x: 0.78, y: 2.34, w: 1.4, h: 0.3, fontFace: FONT, fontSize: 10, bold: true, color: C.purple, margin: 0 });
  s.addText("多数水深下波长稳定在 8 cm 左右，表观波速离散更大；实验不能严格验证相速度公式，但能清楚说明深水近似和反射叠加的影响。", {
    x: 0.78,
    y: 2.72,
    w: 11.55,
    h: 0.62,
    fontFace: FONT,
    fontSize: 19,
    bold: true,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
  metric(s, "λrec ≈ 8 cm", "除最低水深外，波长基本稳定", 0.78, 4.0, 3.6, C.purple);
  metric(s, "|capp| = 5.7–30.7 cm/s", "表观速度离散明显，不呈单调律", 4.72, 4.0, 3.8, C.orange);
  metric(s, "kh = 1.98–15.71", "没有真正进入浅水长波区", 8.88, 4.0, 3.6, C.teal);
  tag(s, "答辩口径", 0.78, 5.75, C.white, C.purple);
  s.addText("我们验证的是“视频测量与理论判据是否一致”，不是强行宣称测到了纯相速度。", {
    x: 2.2,
    y: 5.78,
    w: 8.8,
    h: 0.28,
    fontFace: FONT,
    fontSize: 12,
    color: C.ink,
    margin: 0,
  });
}

function slide3() {
  const s = pptx.addSlide();
  title(s, "QUESTION", "先把问题问准：水深影响的是哪一个“速度”？", "理论相速度需要主频；视频追踪得到的是表观波峰速度", 3);
  card(s, 0.75, 2.35, 5.65, 3.75, { fill: C.white });
  s.addText("理论里想比较的量", { x: 1.1, y: 2.7, w: 2.4, h: 0.25, fontFace: FONT, fontSize: 12, bold: true, color: C.purple, margin: 0 });
  s.addImage({ path: img("dispersion_formula.png"), x: 1.04, y: 3.1, w: 4.45, h: 0.94 });
  bulletList(s, [
    "相速度 cp = ω/k = λf",
    "水深影响通过 tanh(kh) 进入",
    "只有进入浅水或过渡区，水深效应才容易被看出来",
  ], 1.08, 4.35, 4.72, { fontSize: 12, gap: 0.46, dot: C.purple });
  card(s, 6.95, 2.35, 5.65, 3.75, { fill: C.white });
  s.addText("视频里实际得到的量", { x: 7.3, y: 2.7, w: 2.8, h: 0.25, fontFace: FONT, fontSize: 12, bold: true, color: C.orange, margin: 0 });
  s.addText("|capp| = dX峰 / dt", { x: 7.28, y: 3.22, w: 3.2, h: 0.42, fontFace: "Aptos", fontSize: 24, bold: true, color: C.orange, margin: 0 });
  bulletList(s, [
    "来自 x–t 图上的波峰轨迹",
    "会受到入射波/反射波叠加影响",
    "可用于诊断波场，但不能直接等同 cp",
  ], 7.3, 4.35, 4.72, { fontSize: 12, gap: 0.46, dot: C.orange });
}

function slide4() {
  const s = pptx.addSlide();
  title(s, "SETUP", "实验装置：用侧向视频把水面运动变成可量化数据", "变量是静水深 h；观测对象是连续波列的液面位移 η(x,t)", 4);
  addImageCard(s, img("setup_water.png"), 0.75, 2.22, 7.25, 4.55, "水槽侧向成像与液面识别示意");
  card(s, 8.35, 2.22, 4.15, 4.55, { fill: C.white });
  s.addText("实验配置", { x: 8.72, y: 2.58, w: 2.0, h: 0.28, fontFace: FONT, fontSize: 13, bold: true, color: C.purple, margin: 0 });
  bulletList(s, [
    "透明亚克力水槽 + LED 背光",
    "2 Hz 活塞电机驱动 3D 打印推板",
    "固定侧向摄像，逐帧提取水面边界",
    "水深 14 组：2.2–20.0 cm",
  ], 8.72, 3.1, 3.2, { fontSize: 11.3, gap: 0.48 });
  tag(s, "答辩提醒", 8.72, 5.55, C.white, C.orange);
  s.addText("2 Hz 是驱动频率，不应直接当作最终主频；严格相速度还需要从视频中提取 f。", {
    x: 8.72,
    y: 5.95,
    w: 3.45,
    h: 0.55,
    fontFace: FONT,
    fontSize: 10.7,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
}

function slide5() {
  const s = pptx.addSlide();
  title(s, "WORKFLOW", "数据处理流程：先重建波场，再统计波长与表观速度", "这页用于说明数据不是肉眼读出来的，而是有可复现的处理链", 5);
  const steps = [
    ["视频帧", "RGB 图像"],
    ["液面识别", "绿色通道 + 梯度"],
    ["波场重建", "η(x,t) 位移图"],
    ["方向分离", "二维 Fourier"],
    ["统计输出", "λrec 与 |capp|"],
  ];
  steps.forEach((st, i) => {
    const x = 0.75 + i * 2.48;
    card(s, x, 2.72, 2.05, 1.95, { fill: i === 4 ? C.cyan : C.white, line: i === 4 ? C.teal : C.line });
    s.addText(String(i + 1).padStart(2, "0"), { x: x + 0.18, y: 2.95, w: 0.5, h: 0.28, fontFace: "Aptos", fontSize: 14, bold: true, color: i === 4 ? C.teal : C.purple, margin: 0 });
    s.addText(st[0], { x: x + 0.2, y: 3.38, w: 1.62, h: 0.28, fontFace: FONT, fontSize: 13.5, bold: true, color: C.ink, margin: 0, align: "center" });
    s.addText(st[1], { x: x + 0.18, y: 3.82, w: 1.66, h: 0.25, fontFace: FONT, fontSize: 9.2, color: C.mute, margin: 0, align: "center", fit: "shrink" });
    if (i < steps.length - 1) {
      s.addShape(pptx.ShapeType.chevron, { x: x + 2.06, y: 3.45, w: 0.33, h: 0.35, fill: { color: "D7CADF" }, line: { color: "D7CADF" } });
    }
  });
  s.addText("关键设计：用中位数而不是普通均值，降低异常帧、误检波峰和轨迹断裂对结果的影响。", {
    x: 0.95,
    y: 5.55,
    w: 11.45,
    h: 0.42,
    fontFace: FONT,
    fontSize: 16,
    bold: true,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
}

function slide6() {
  const s = pptx.addSlide();
  title(s, "EVIDENCE 1", "波场证据：x–t 图里能分出入射波和反射波", "这说明测量对象是连续传播波列，但也提示速度会被叠加波场影响", 6);
  addImageCard(s, img("xt_direction.png"), 0.74, 2.18, 8.0, 4.82, "h = 12 cm 的原始位移场与 Fourier 方向分离");
  card(s, 9.05, 2.18, 3.55, 4.82, { fill: C.white });
  s.addText("读图方法", { x: 9.38, y: 2.55, w: 1.5, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  bulletList(s, [
    "斜纹代表波峰随时间移动",
    "入射与反射方向相反",
    "反射存在，所以不能只追一条峰线就叫相速度",
    "后续报告 |capp|，而不是 cp",
  ], 9.38, 3.02, 2.7, { fontSize: 11.2, gap: 0.52, dot: C.teal });
}

function slide7() {
  const s = pptx.addSlide();
  title(s, "METHOD", "波长提取：每一帧找波峰，稳定阶段取中位数", "目标不是追求单帧漂亮，而是让统计量对误检不敏感", 7);
  card(s, 0.78, 2.24, 5.85, 4.6, { fill: C.white });
  s.addText("统计定义", { x: 1.1, y: 2.58, w: 1.4, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  s.addText("λrec = median(逐帧平均峰距)", {
    x: 1.08,
    y: 3.15,
    w: 4.95,
    h: 0.45,
    fontFace: "Aptos",
    fontSize: 22,
    bold: true,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
  bulletList(s, [
    "先去除大尺度趋势",
    "检测局部波峰坐标 xi,j",
    "相邻峰距换算成实际长度",
    "稳定阶段取中位数，降低异常帧影响",
  ], 1.12, 4.05, 4.75, { fontSize: 11.8, gap: 0.47 });
  addImageCard(s, img("data_table.png"), 7.05, 2.24, 5.0, 2.35, "各水深下的推荐波长与中位表观波速");
  tag(s, "为什么这样做", 7.1, 5.05, C.white, C.teal);
  s.addText("水面识别会有误检，尤其在低水深和反射明显时。中位数能把少数错误波峰的影响压下去。", {
    x: 7.1,
    y: 5.45,
    w: 4.85,
    h: 0.55,
    fontFace: FONT,
    fontSize: 11.8,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
}

function slide8() {
  const s = pptx.addSlide();
  title(s, "RESULT 1", "结果一：波长基本围绕 8 cm，水深不是主导变量", "这与“多数工况接近深水近似”的理论判断一致", 8);
  addImageCard(s, img("chart_wavelength.png"), 0.75, 2.1, 8.25, 4.1, "推荐波长随水深变化");
  card(s, 9.35, 2.1, 3.25, 4.1, { fill: C.white });
  s.addText("图上最重要的三件事", { x: 9.65, y: 2.45, w: 2.3, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  bulletList(s, [
    "h = 2.2 cm 明显偏低",
    "其余点主要集中在 8 cm 附近",
    "线性斜率约 −0.001 cm/cm，r≈−0.01",
  ], 9.65, 2.96, 2.5, { fontSize: 11.3, gap: 0.58 });
  metric(s, "8.07 ± 0.77 cm", "推荐波长均值与离散", 9.63, 5.1, 2.55, C.purple);
}

function slide9() {
  const s = pptx.addSlide();
  title(s, "RESULT 2", "结果二：表观波速更离散，不能讲成简单单调律", "这页是答辩的风险点，也可以变成亮点：我们承认并解释了偏差", 9);
  addImageCard(s, img("chart_speed.png"), 0.75, 2.1, 7.05, 4.0, "表观波速随水深变化");
  card(s, 8.25, 2.1, 4.35, 4.0, { fill: C.white });
  s.addText("为什么这不是失败？", { x: 8.62, y: 2.44, w: 2.4, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: C.orange, margin: 0 });
  bulletList(s, [
    "速度的离散明显大于波长",
    "低水深 2.2、2.6 cm 异常偏低",
    "3.2–14 cm 与理论速度量级接近",
    "说明追踪到的是叠加波场里的表观传播",
  ], 8.62, 2.97, 3.25, { fontSize: 11.2, gap: 0.49, dot: C.orange });
  metric(s, "5.7–30.7 cm/s", "各组中位表观波速范围", 8.62, 5.45, 3.0, C.orange);
}

function slide10() {
  const s = pptx.addSlide();
  title(s, "THEORY CHECK", "理论判据：这组数据没有真正进入浅水长波区", "因此“水深影响波速”的变化本来就不容易在本实验范围内显现", 10);
  addImageCard(s, img("theory_depth.png"), 0.72, 2.0, 8.2, 4.35, "按 kh 判断水深区间与有限水深修正");
  card(s, 9.25, 2.0, 3.55, 4.35, { fill: C.white });
  s.addText("判据结论", { x: 9.58, y: 2.35, w: 1.5, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.teal, margin: 0 });
  bulletList(s, [
    "λrec 约 8 cm",
    "kh 最小也约 1.98",
    "h = 4.4–20 cm 已接近深水",
    "有限水深修正最大约 1.9%",
  ], 9.58, 2.85, 2.75, { fontSize: 11.5, gap: 0.52, dot: C.teal });
  tag(s, "答辩说法", 9.58, 5.65, C.white, C.teal);
  s.addText("没有观察到强单调关系，并不矛盾；因为实验点大多已经在水深影响很弱的区域。", {
    x: 9.58,
    y: 6.02,
    w: 2.9,
    h: 0.42,
    fontFace: FONT,
    fontSize: 10.7,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
}

function slide11() {
  const s = pptx.addSlide();
  title(s, "INTERPRETATION", "为什么不能把 |capp| 直接叫作理论相速度", "这是新版答辩稿要主动说明的地方", 11);
  card(s, 0.8, 2.25, 5.6, 3.85, { fill: C.white });
  s.addText("理论相速度 cp", { x: 1.13, y: 2.6, w: 2.4, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.purple, margin: 0 });
  s.addText("cp = λf", { x: 1.12, y: 3.22, w: 2.1, h: 0.45, fontFace: "Aptos", fontSize: 25, bold: true, color: C.purple, margin: 0 });
  bulletList(s, [
    "要求单一行进波",
    "需要同步得到主频 f",
    "可与色散公式直接比较",
  ], 1.16, 4.12, 4.5, { fontSize: 12.2, gap: 0.5, dot: C.purple });
  card(s, 6.98, 2.25, 5.6, 3.85, { fill: C.peach, line: "F2D2C0" });
  s.addText("本实验表观速度 |capp|", { x: 7.31, y: 2.6, w: 3.3, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.orange, margin: 0 });
  s.addText("|capp| = dX峰/dt", { x: 7.3, y: 3.22, w: 3.1, h: 0.45, fontFace: "Aptos", fontSize: 25, bold: true, color: C.orange, margin: 0 });
  bulletList(s, [
    "来自波峰轨迹追踪",
    "入射波/反射波叠加会改变峰纹",
    "适合作为实验诊断量",
  ], 7.35, 4.12, 4.5, { fontSize: 12.2, gap: 0.5, dot: C.orange });
  s.addShape(pptx.ShapeType.chevron, { x: 6.48, y: 3.8, w: 0.36, h: 0.42, fill: { color: "C9B5D3" }, line: { color: "C9B5D3" } });
  s.addText("严格验证相速度的下一步：从 η(x,t) 中提取主频 f，再计算 c = λf。", {
    x: 1.25,
    y: 6.55,
    w: 10.7,
    h: 0.34,
    fontFace: FONT,
    fontSize: 14.5,
    bold: true,
    color: C.ink,
    margin: 0,
    align: "center",
  });
}

function slide12() {
  const s = pptx.addSlide();
  title(s, "DIAGNOSTIC", "典型诊断：h = 12 cm 时速度分布已经很宽", "这解释了为什么单个中位数不能被过度解读", 12);
  addImageCard(s, img("speed_diagnostic.png"), 0.75, 2.0, 7.6, 4.9, "h = 12 cm 的波峰轨迹、逐段速度和速度分布");
  card(s, 8.72, 2.0, 3.85, 4.9, { fill: C.white });
  s.addText("这一页怎么讲", { x: 9.08, y: 2.35, w: 2.0, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  metric(s, "24.6 cm/s", "中位表观波速", 9.08, 2.92, 2.65, C.purple);
  metric(s, "7.6–42.5 cm/s", "四分位范围", 9.08, 4.15, 2.65, C.orange);
  s.addText("轨迹断裂、反射叠加和局部峰纹消失都会扩大速度分布。这里不是避开误差，而是把误差来源变成分析对象。", {
    x: 9.08,
    y: 5.55,
    w: 2.9,
    h: 0.72,
    fontFace: FONT,
    fontSize: 10.7,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
}

function slide13() {
  const s = pptx.addSlide();
  title(s, "LIMITATIONS", "局限与改进：如果要真正验证相速度公式，下一版这样做", "主动指出不足，比强行包装结论更容易获得认可", 13);
  const items = [
    ["提取主频 f", "对 η(x,t) 做时域/频域分析，计算 c = λf"],
    ["削弱反射", "加消波材料或延长水槽，减少入射/反射叠加"],
    ["重复实验", "每个水深多次采样，报告不确定度而非单值"],
    ["扩大浅水区", "使用更长波长或更小水深，让 h/λ 真正进入浅水范围"],
  ];
  items.forEach((it, i) => {
    const x = 0.8 + (i % 2) * 6.1;
    const y = 2.35 + Math.floor(i / 2) * 2.15;
    card(s, x, y, 5.45, 1.55, { fill: i % 2 === 0 ? C.white : C.cyan, line: i % 2 === 0 ? C.line : "C9E7EA" });
    s.addText(String(i + 1), { x: x + 0.25, y: y + 0.28, w: 0.42, h: 0.32, fontFace: "Aptos", fontSize: 16, bold: true, color: i % 2 === 0 ? C.purple : C.teal, margin: 0 });
    s.addText(it[0], { x: x + 0.82, y: y + 0.25, w: 2.8, h: 0.3, fontFace: FONT, fontSize: 13.5, bold: true, color: C.ink, margin: 0 });
    s.addText(it[1], { x: x + 0.82, y: y + 0.73, w: 4.25, h: 0.32, fontFace: FONT, fontSize: 10.7, color: C.mute, margin: 0, fit: "shrink" });
  });
  tag(s, "改进后的目标", 0.9, 6.55, C.white, C.purple);
  s.addText("把“表观速度诊断”升级为“相速度色散关系验证”。", { x: 2.35, y: 6.58, w: 6.6, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.ink, margin: 0 });
}

function slide14() {
  const s = pptx.addSlide();
  s.background = { color: C.deep };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.deep }, line: { color: C.deep } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.purple, transparency: 16 }, line: { transparency: 100 } });
  s.addImage({ path: img("xt_direction.png"), ...containImage(img("xt_direction.png"), 8.0, 0.78, 4.75, 4.05), transparency: 34 });
  s.addImage({ path: img("tsinghua_logo.png"), x: 0.82, y: 0.58, w: 1.75, h: 0.64 });
  s.addText("最终结论", { x: 0.88, y: 1.65, w: 3.0, h: 0.48, fontFace: FONT, fontSize: 25, bold: true, color: C.white, margin: 0 });
  const conclusions = [
    "我们用视频波场重建获得了平均波长和表观波速。",
    "在本实验范围内，波长约 8 cm，多数水深已接近深水近似，水深修正较弱。",
    "表观波速受反射与峰纹追踪影响明显，因此不能直接等同理论相速度。",
  ];
  conclusions.forEach((t, i) => {
    const y = 2.55 + i * 0.82;
    s.addShape(pptx.ShapeType.ellipse, { x: 0.95, y: y + 0.05, w: 0.18, h: 0.18, fill: { color: i === 1 ? C.teal : "E3B6EE" }, line: { color: i === 1 ? C.teal : "E3B6EE" } });
    s.addText(t, { x: 1.35, y, w: 5.95, h: 0.46, fontFace: FONT, fontSize: 14.2, bold: i === 2, color: C.white, margin: 0, fit: "shrink" });
  });
  s.addShape(pptx.ShapeType.line, { x: 0.92, y: 5.48, w: 5.7, h: 0, line: { color: "B98BCC", width: 1.2 } });
  s.addText("谢谢聆听", { x: 0.9, y: 5.85, w: 2.5, h: 0.38, fontFace: FONT, fontSize: 20, bold: true, color: C.white, margin: 0 });
  s.addText("欢迎老师提问", { x: 0.92, y: 6.35, w: 2.5, h: 0.24, fontFace: FONT, fontSize: 11, color: "E3C7EC", margin: 0 });
}

[
  slide1,
  slide2,
  slide3,
  slide4,
  slide5,
  slide6,
  slide7,
  slide8,
  slide9,
  slide10,
  slide11,
  slide12,
  slide13,
  slide14,
].forEach((fn) => fn());

pptx.writeFile({ fileName: outPptx }).then(() => {
  console.log(outPptx);
});
