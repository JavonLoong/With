const path = require("path");
const pptxgen = require("pptxgenjs");
const sizeOf = require("image-size");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "纪文龙 白子恒 秦健淞 丘洪源 杨天皓";
pptx.subject = "水波波速与水深关系探究答辩版";
pptx.title = "水波波速与水深关系探究";
pptx.company = "Tsinghua University";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei UI",
  bodyFontFace: "Microsoft YaHei UI",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const FONT = "Microsoft YaHei UI";
const MATH = "Cambria Math";
const assets = "D:/Users/15410/AppData/Local/Temp/wave_review_latest/final_assets";
const outDir = "D:/虚拟C盘/学习/outputs/manual-20260608-wave-defense/presentations/wave-defense/output";
const outPptx = path.join(outDir, "水波波速与水深关系探究_答辩高分版.pptx");

const C = {
  purple: "6F1D8F",
  purpleLine: "7A2A9E",
  deep: "24152E",
  deep2: "2A1636",
  plum: "9F3E76",
  plum2: "A75BA8",
  bg: "FAF8FC",
  lavender: "F1E8F6",
  lavender2: "E8D8EF",
  line: "D8C6E1",
  ink: "1C1722",
  mute: "625B6B",
  white: "FFFFFF",
};

function img(name) {
  return path.join(assets, name);
}

function containImage(imagePath, x, y, w, h) {
  const dim = sizeOf(imagePath);
  const imgRatio = dim.width / dim.height;
  const boxRatio = w / h;
  let ww = w;
  let hh = h;
  if (imgRatio > boxRatio) hh = w / imgRatio;
  else ww = h * imgRatio;
  return { x: x + (w - ww) / 2, y: y + (h - hh) / 2, w: ww, h: hh };
}

function bg(slide, color = C.bg) {
  slide.background = { color };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: 0.12,
    fill: { color: C.purple },
    line: { color: C.purple },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: H - 0.07,
    w: W,
    h: 0.07,
    fill: { color: C.purple },
    line: { color: C.purple },
  });
}

function logo(slide, white = false, x = 11.25, y = 0.34, w = 1.55, h = 0.56) {
  slide.addImage({ path: white ? img("tsinghua_logo_white.png") : img("tsinghua_logo_purple_transparent.png"), x, y, w, h });
}

function header(slide, kicker, main, n) {
  bg(slide);
  logo(slide);
  slide.addText(kicker, {
    x: 0.68,
    y: 0.42,
    w: 2.4,
    h: 0.24,
    fontFace: "Aptos",
    fontSize: 8.2,
    bold: true,
    color: C.purple,
    charSpace: 1.2,
    margin: 0,
  });
  slide.addText(main, {
    x: 0.68,
    y: 0.82,
    w: 10.25,
    h: 0.64,
    fontFace: FONT,
    fontSize: 26.2,
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
    line: { color: C.purpleLine, width: 2.1 },
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 3.42,
    y: 1.72,
    w: 9.05,
    h: 0,
    line: { color: C.line, width: 1.1 },
  });
  slide.addText(String(n).padStart(2, "0"), {
    x: 12.18,
    y: 6.86,
    w: 0.55,
    h: 0.22,
    fontFace: "Aptos",
    fontSize: 8.4,
    color: C.mute,
    align: "right",
    margin: 0,
  });
}

function card(slide, x, y, w, h, fill = C.white, line = C.line) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.06,
    fill: { color: fill },
    line: { color: line, width: 1 },
    shadow: { type: "outer", color: "D8D0E1", opacity: 0.12, blur: 1, angle: 45, distance: 0.8 },
  });
}

function imageCard(slide, imagePath, x, y, w, h, caption) {
  card(slide, x, y, w, h);
  const box = containImage(imagePath, x + 0.15, y + 0.13, w - 0.3, h - (caption ? 0.5 : 0.26));
  slide.addImage({ path: imagePath, ...box });
  if (caption) {
    slide.addText(caption, {
      x: x + 0.2,
      y: y + h - 0.31,
      w: w - 0.4,
      h: 0.18,
      fontFace: FONT,
      fontSize: 7.6,
      color: C.mute,
      align: "center",
      margin: 0,
    });
  }
}

function bullets(slide, lines, x, y, w, opts = {}) {
  const dot = opts.dot || C.purple;
  const fs = opts.fontSize || 12;
  const gap = opts.gap || 0.5;
  lines.forEach((text, i) => {
    const yy = y + i * gap;
    slide.addShape(pptx.ShapeType.ellipse, {
      x,
      y: yy + 0.1,
      w: 0.12,
      h: 0.12,
      fill: { color: dot },
      line: { color: dot },
    });
    slide.addText(text, {
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
    });
  });
}

function rich(slide, runs, x, y, w, h, opts = {}) {
  slide.addText(runs.map((r) => ({
    text: r.text,
    options: {
      fontFace: r.fontFace || "Aptos",
      fontSize: r.fontSize || opts.fontSize || 20,
      bold: r.bold ?? opts.bold ?? true,
      italic: r.italic || false,
      color: r.color || opts.color || C.purple,
      subscript: r.subscript || false,
      superscript: r.superscript || false,
      baseline: r.baseline,
    },
  })), { x, y, w, h, margin: 0, fit: "shrink", align: opts.align || "left" });
}

const rLambdaRec = (color = C.purple, size = 20) => [
  { text: "λ", color, fontSize: size, fontFace: MATH, italic: true },
  { text: "rec", color, fontSize: size - 4, subscript: true, fontFace: "Aptos" },
];
const rCp = (color = C.purple, size = 20) => [
  { text: "c", color, fontSize: size, fontFace: MATH, italic: true },
  { text: "p", color, fontSize: size - 4, subscript: true, fontFace: "Aptos" },
];
const rCapp = (color = C.plum, size = 20) => [
  { text: "c", color, fontSize: size, fontFace: MATH, italic: true },
  { text: "app", color, fontSize: size - 5, subscript: true, fontFace: "Aptos" },
];
const rKh = (color = C.purple, size = 20) => [
  { text: "k", color, fontSize: size, italic: true, fontFace: MATH },
  { text: " h", color, fontSize: size, italic: true, fontFace: MATH },
];
const rEta = (color = C.ink, size = 16) => [
  { text: "η", color, fontSize: size, italic: true, fontFace: MATH },
  { text: "(", color, fontSize: size, fontFace: MATH },
  { text: "x", color, fontSize: size, italic: true, fontFace: MATH },
  { text: ", ", color, fontSize: size, fontFace: MATH },
  { text: "t", color, fontSize: size, italic: true, fontFace: MATH },
  { text: ")", color, fontSize: size, fontFace: MATH },
];
const rSpeedUnit = (color = C.purple, size = 20) => [
  { text: " cm s", color, fontSize: size, fontFace: "Aptos" },
  { text: "-1", color, fontSize: size - 6, superscript: true, fontFace: "Aptos" },
];

function metric(slide, runs, label, x, y, w, color = C.purple) {
  card(slide, x, y, w, 1.05);
  rich(slide, runs, x + 0.22, y + 0.16, w - 0.44, 0.42, { color, fontSize: 20 });
  if (Array.isArray(label)) {
    rich(slide, label, x + 0.22, y + 0.62, w - 0.44, 0.26, { fontSize: 9.4, color: C.mute, bold: false });
  } else {
    slide.addText(label, {
      x: x + 0.22,
      y: y + 0.62,
      w: w - 0.44,
      h: 0.26,
      fontFace: FONT,
      fontSize: 9.4,
      color: C.mute,
      margin: 0,
      fit: "shrink",
    });
  }
}

function lineArrow(slide, x, y, w, color = "BDA8C9", width = 2) {
  slide.addShape(pptx.ShapeType.line, {
    x,
    y,
    w,
    h: 0,
    line: { color, width, endArrowType: "triangle" },
  });
}

function tag(slide, text, x, y, bgColor = C.purple) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w: text.length * 0.16 + 0.55,
    h: 0.32,
    rectRadius: 0.05,
    fill: { color: bgColor },
    line: { color: bgColor },
  });
  slide.addText(text, {
    x: x + 0.16,
    y: y + 0.065,
    w: text.length * 0.16 + 0.24,
    h: 0.16,
    fontFace: FONT,
    fontSize: 8,
    bold: true,
    color: C.white,
    margin: 0,
    breakLine: false,
  });
}

function slide1() {
  const s = pptx.addSlide();
  s.background = { color: C.deep };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.deep }, line: { color: C.deep } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.purple, transparency: 18 }, line: { transparency: 100 } });
  s.addImage({ path: img("cover_wave_tint.png"), x: 7.0, y: 0.75, w: 5.65, h: 4.3, transparency: 18 });
  s.addShape(pptx.ShapeType.line, { x: 0.84, y: 3.05, w: 5.75, h: 0, line: { color: "C7A4D5", width: 1.2 } });
  logo(s, true, 0.78, 0.55, 1.65, 0.6);
  s.addText("水波波速与水深关系探究", {
    x: 0.84,
    y: 1.58,
    w: 7.5,
    h: 0.62,
    fontFace: FONT,
    fontSize: 31,
    bold: true,
    color: C.white,
    margin: 0,
    fit: "shrink",
  });
  s.addText("区分表观波速与理论相速度", {
    x: 0.86,
    y: 2.36,
    w: 5.8,
    h: 0.36,
    fontFace: FONT,
    fontSize: 17,
    bold: true,
    color: "EFE2F4",
    margin: 0,
  });
  s.addText("基于视频波场重建的实验测量与误差诊断", {
    x: 0.86,
    y: 3.45,
    w: 6.2,
    h: 0.34,
    fontFace: FONT,
    fontSize: 14.2,
    color: "E5CDEA",
    margin: 0,
  });
  s.addText("纪文龙  白子恒  秦健淞  丘洪源  杨天皓", {
    x: 0.88,
    y: 6.25,
    w: 5.6,
    h: 0.24,
    fontFace: FONT,
    fontSize: 10.6,
    color: "EADAF0",
    margin: 0,
  });
  s.addText("2026.5", { x: 0.88, y: 6.62, w: 1.0, h: 0.2, fontFace: "Aptos", fontSize: 9, color: "CDB4D7", margin: 0 });
}

function slide2() {
  const s = pptx.addSlide();
  header(s, "CORE RESULTS", "波长约 8 cm；表观波速离散更大", 2);
  s.addText("多数水深接近深水近似，速度受反射叠加影响", {
    x: 0.78,
    y: 2.28,
    w: 9.6,
    h: 0.42,
    fontFace: FONT,
    fontSize: 19,
    bold: true,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
  metric(s, [...rLambdaRec(C.purple, 21), { text: " ≈ 8 cm", color: C.purple, fontSize: 21 }], "波长基本稳定", 0.78, 3.55, 3.6);
  metric(s, [{ text: "|", color: C.plum, fontSize: 21 }, ...rCapp(C.plum, 21), { text: "| = 5.7–30.7", color: C.plum, fontSize: 19 }, ...rSpeedUnit(C.plum, 19)], "表观波速离散明显", 4.72, 3.55, 3.95, C.plum);
  metric(s, [...rKh(C.purpleLine, 21), { text: " = 1.98–15.71", color: C.purpleLine, fontSize: 21 }], "有限水深判据；未进浅水长波区", 9.0, 3.55, 3.45, C.purpleLine);
  tag(s, "测量边界", 0.82, 5.65);
  s.addText("本实验报告波长、表观波速与水深判据，不将表观波速等同于纯相速度。", {
    x: 2.25,
    y: 5.69,
    w: 8.4,
    h: 0.25,
    fontFace: FONT,
    fontSize: 12.2,
    color: C.ink,
    margin: 0,
  });
}

function slide3() {
  const s = pptx.addSlide();
  header(s, "QUESTION", "水深影响的是哪一种“速度”？", 3);
  card(s, 0.75, 2.35, 5.65, 3.75);
  s.addText("理论量", { x: 1.1, y: 2.7, w: 1.4, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  s.addImage({ path: img("dispersion_formula.png"), x: 1.04, y: 3.08, w: 4.45, h: 0.94 });
  rich(s, [...rCp(C.purple, 16), { text: " = ω/k = λ f", color: C.purple, fontSize: 16, fontFace: MATH }], 1.1, 4.24, 4.6, 0.3, { fontSize: 16 });
  bullets(s, ["单一行进波的相速度", "需要同步获得主频 f", "可与色散关系直接比较"], 1.12, 4.78, 4.6, { fontSize: 11.6, gap: 0.43 });
  card(s, 6.95, 2.35, 5.65, 3.75, C.lavender, C.line);
  s.addText("测量量", { x: 7.3, y: 2.7, w: 1.4, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.plum, margin: 0 });
  rich(s, [{ text: "|", color: C.plum, fontSize: 24 }, ...rCapp(C.plum, 24), { text: "| = Δx", color: C.plum, fontSize: 24, fontFace: MATH }, { text: "peak", color: C.plum, fontSize: 18, subscript: true }, { text: "/Δt", color: C.plum, fontSize: 24, fontFace: MATH }], 7.28, 3.22, 3.8, 0.42, { fontSize: 24 });
  bullets(s, ["来自 x–t 图上的波峰轨迹", "受入射波/反射波叠加影响", "适合作为实验诊断量"], 7.3, 4.58, 4.72, { fontSize: 11.6, gap: 0.43, dot: C.plum });
}

function slide4() {
  const s = pptx.addSlide();
  header(s, "SETUP", "实验装置与变量", 4);
  imageCard(s, img("setup_water.png"), 0.75, 2.12, 7.6, 4.65, "水槽侧向成像与液面识别示意");
  card(s, 8.65, 2.12, 3.85, 4.65);
  s.addText("实验配置", { x: 8.98, y: 2.48, w: 1.7, h: 0.25, fontFace: FONT, fontSize: 12.6, bold: true, color: C.purple, margin: 0 });
  bullets(s, ["透明水槽 + LED 背光", "2 Hz 活塞电机驱动推板", "侧向摄像提取水面边界", "水深 14 组：2.2–20.0 cm"], 8.98, 2.98, 2.9, { fontSize: 11.2, gap: 0.48 });
  tag(s, "频率说明", 8.98, 5.58, C.purpleLine);
  s.addText("2 Hz 为驱动频率；主频 f 仍需由视频波场提取。", { x: 8.98, y: 5.98, w: 2.85, h: 0.38, fontFace: FONT, fontSize: 10.8, color: C.ink, margin: 0, fit: "shrink" });
}

function slide5() {
  const s = pptx.addSlide();
  header(s, "WORKFLOW", "数据处理流程", 5);
  const steps = [
    ["视频帧", "RGB 图像"],
    ["液面识别", "绿色通道 + 梯度"],
    ["波场重建", "η(x, t) 位移图"],
    ["方向分离", "二维 Fourier"],
    ["统计输出", "波长 / 表观速度"],
  ];
  steps.forEach((st, i) => {
    const x = 0.75 + i * 2.48;
    card(s, x, 2.68, 2.05, 1.95, i === 4 ? C.lavender : C.white, i === 4 ? C.purpleLine : C.line);
    s.addText(String(i + 1).padStart(2, "0"), { x: x + 0.18, y: 2.95, w: 0.5, h: 0.28, fontFace: "Aptos", fontSize: 14, bold: true, color: C.purple, margin: 0 });
    s.addText(st[0], { x: x + 0.2, y: 3.36, w: 1.62, h: 0.28, fontFace: FONT, fontSize: 13.5, bold: true, color: C.ink, margin: 0, align: "center" });
    if (i === 2) {
      rich(s, [...rEta(C.mute, 9.2), { text: " 位移图", color: C.mute, fontSize: 9.2, fontFace: FONT, bold: false }], x + 0.18, 3.82, 1.66, 0.25, { fontSize: 9.2, color: C.mute, align: "center", bold: false });
    } else {
      s.addText(st[1], { x: x + 0.18, y: 3.82, w: 1.66, h: 0.25, fontFace: FONT, fontSize: 9.2, color: C.mute, margin: 0, align: "center", fit: "shrink" });
    }
    if (i < steps.length - 1) {
      lineArrow(s, x + 2.08, 3.62, 0.36, "BDA8C9", 2);
    }
  });
  s.addText("稳定阶段取中位数，降低异常帧与断裂轨迹影响。", {
    x: 0.95,
    y: 5.58,
    w: 11.0,
    h: 0.38,
    fontFace: FONT,
    fontSize: 15.2,
    bold: true,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
}

function slide6() {
  const s = pptx.addSlide();
  header(s, "EVIDENCE", "x–t 波场：入射波与反射波可分辨", 6);
  imageCard(s, img("xt_direction.png"), 0.74, 2.08, 8.35, 4.9, "h = 12 cm 的原始位移场与 Fourier 方向分离");
  card(s, 9.25, 2.08, 3.35, 4.9);
  s.addText("关键观察", { x: 9.55, y: 2.48, w: 1.6, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  bullets(s, ["斜纹代表波峰随时间移动", "入射与反射方向相反", "反射会改变峰线斜率", "后续报告表观速度，不称相速度"], 9.55, 3.02, 2.45, { fontSize: 11.1, gap: 0.53 });
}

function slide7() {
  const s = pptx.addSlide();
  header(s, "METHOD", "波长提取：稳定阶段取中位峰距", 7);
  card(s, 0.78, 2.16, 5.65, 4.7);
  s.addText("统计定义", { x: 1.1, y: 2.54, w: 1.3, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  rich(s, [...rLambdaRec(C.purple, 22), { text: " = median(逐帧平均峰距)", color: C.ink, fontSize: 19 }], 1.08, 3.15, 4.95, 0.45, { fontSize: 22 });
  bullets(s, ["去除大尺度趋势", "检测局部波峰坐标", "相邻峰距换算为实际长度", "用中位数降低异常帧影响"], 1.12, 4.05, 4.5, { fontSize: 11.5, gap: 0.46 });
  card(s, 6.85, 2.16, 5.3, 4.7);
  s.addImage({ path: img("data_table.png"), ...containImage(img("data_table.png"), 7.1, 2.5, 4.85, 2.05) });
  tag(s, "稳健性处理", 7.1, 5.08);
  s.addText("低水深和强反射时误检更多，中位数可减弱少数异常峰的影响。", { x: 7.1, y: 5.48, w: 4.75, h: 0.45, fontFace: FONT, fontSize: 11.2, color: C.ink, margin: 0, fit: "shrink" });
}

function slide8() {
  const s = pptx.addSlide();
  header(s, "RESULT 1", "波长主要集中在 8 cm 附近", 8);
  imageCard(s, img("chart_wavelength.png"), 0.75, 2.05, 8.55, 4.55, "推荐波长随水深变化");
  card(s, 9.55, 2.05, 3.05, 4.55);
  s.addText("关键观察", { x: 9.85, y: 2.42, w: 1.5, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  bullets(s, ["h = 2.2 cm 明显偏低", "其余点集中在 8 cm 附近", "斜率约 −0.001 cm/cm，r≈−0.01"], 9.85, 2.95, 2.25, { fontSize: 10.7, gap: 0.54 });
  metric(s, [{ text: "8.07 ± 0.77 cm", color: C.purple, fontSize: 20 }], "推荐波长均值与离散", 9.82, 5.08, 2.35);
}

function slide9() {
  const s = pptx.addSlide();
  header(s, "RESULT 2", "表观波速离散明显", 9);
  imageCard(s, img("chart_speed.png"), 0.75, 2.08, 7.85, 4.45, "表观波速随水深变化");
  card(s, 8.85, 2.08, 3.75, 4.45);
  s.addText("关键观察", { x: 9.15, y: 2.44, w: 1.5, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.plum, margin: 0 });
  bullets(s, ["速度的离散明显大于波长", "低水深 2.2、2.6 cm 异常偏低", "3.2–14 cm 与理论速度量级接近", "追踪到的是叠加波场里的表观传播"], 9.15, 2.95, 2.95, { fontSize: 10.6, gap: 0.45, dot: C.plum });
  metric(s, [{ text: "5.7–30.7 cm s⁻¹", color: C.plum, fontSize: 19 }], "各组中位表观波速范围", 9.15, 5.35, 2.95, C.plum);
}

function slide10() {
  const s = pptx.addSlide();
  header(s, "THEORY CHECK", "大多数工况接近深水区", 10);
  imageCard(s, img("theory_depth.png"), 0.72, 2.0, 8.55, 4.55, "按 k h 判断水深区间与有限水深修正");
  card(s, 9.55, 2.0, 3.05, 4.55);
  s.addText("判据结果", { x: 9.85, y: 2.35, w: 1.5, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  bullets(s, ["波长约 8 cm", "k h 最小约 1.98", "h = 4.4–20 cm 接近深水", "有限水深修正约 1.9%"], 9.85, 2.82, 2.25, { fontSize: 10.7, gap: 0.48 });
  tag(s, "结论", 9.85, 5.43, C.purpleLine);
  s.addText("未观察到强单调关系，与深水近似判断一致。", { x: 9.85, y: 5.82, w: 2.35, h: 0.32, fontFace: FONT, fontSize: 10.2, color: C.ink, margin: 0, fit: "shrink" });
}

function slide11() {
  const s = pptx.addSlide();
  header(s, "INTERPRETATION", "表观波速不能直接等同理论相速度", 11);
  card(s, 0.8, 2.25, 5.6, 3.85);
  s.addText("理论相速度", { x: 1.13, y: 2.6, w: 2.4, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.purple, margin: 0 });
  rich(s, [...rCp(C.purple, 25), { text: " = λ f", color: C.purple, fontSize: 25, fontFace: MATH }], 1.12, 3.2, 2.1, 0.45, { fontSize: 25 });
  bullets(s, ["要求单一行进波", "需要同步获得主频 f", "可与色散关系直接比较"], 1.16, 4.12, 4.5, { fontSize: 12, gap: 0.5 });
  card(s, 6.98, 2.25, 5.6, 3.85, C.lavender);
  s.addText("表观速度", { x: 7.31, y: 2.6, w: 2.0, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.plum, margin: 0 });
  rich(s, [{ text: "|", color: C.plum, fontSize: 25 }, ...rCapp(C.plum, 25), { text: "| = Δx", color: C.plum, fontSize: 25, fontFace: MATH }, { text: "peak", color: C.plum, fontSize: 19, subscript: true }, { text: "/Δt", color: C.plum, fontSize: 25, fontFace: MATH }], 7.3, 3.2, 3.7, 0.45, { fontSize: 25 });
  bullets(s, ["来自波峰轨迹追踪", "入射/反射叠加会改变峰纹", "适合作为实验诊断量"], 7.35, 4.12, 4.5, { fontSize: 12, gap: 0.5, dot: C.plum });
  lineArrow(s, 6.42, 4.08, 0.52, "C9B5D3", 2.2);
  rich(s, [{ text: "主频 ", color: C.ink, fontFace: FONT, fontSize: 14.2, bold: true }, { text: "f", color: C.ink, fontFace: MATH, fontSize: 14.2, italic: true, bold: true }, { text: " 提取后，可用 ", color: C.ink, fontFace: FONT, fontSize: 14.2, bold: true }, ...rCp(C.ink, 14.2), { text: " = λ f 进行相速度验证。", color: C.ink, fontFace: MATH, fontSize: 14.2, bold: true }], 1.25, 6.55, 10.7, 0.3, { align: "center" });
}

function slide12() {
  const s = pptx.addSlide();
  header(s, "DIAGNOSTIC", "h = 12 cm 的速度分布较宽", 12);
  imageCard(s, img("speed_diagnostic.png"), 0.72, 2.0, 8.2, 4.9, "h = 12 cm 的波峰轨迹、逐段速度和速度分布");
  card(s, 9.05, 2.0, 3.5, 4.9);
  s.addText("诊断指标", { x: 9.38, y: 2.35, w: 1.5, h: 0.25, fontFace: FONT, fontSize: 12.5, bold: true, color: C.purple, margin: 0 });
  metric(s, [{ text: "24.6 cm s⁻¹", color: C.purple, fontSize: 19 }], "中位表观波速", 9.38, 2.92, 2.65);
  metric(s, [{ text: "7.6–42.5 cm s⁻¹", color: C.plum, fontSize: 18.5 }], "四分位范围", 9.38, 4.15, 2.65, C.plum);
  s.addText("反射叠加与峰纹断裂扩大速度分布。", { x: 9.38, y: 5.58, w: 2.75, h: 0.45, fontFace: FONT, fontSize: 10.4, color: C.ink, margin: 0, fit: "shrink" });
}

function slide13() {
  const s = pptx.addSlide();
  header(s, "NEXT STEPS", "改进方向：从表观速度到相速度验证", 13);
  const items = [
    ["提取主频 f", "从波场频谱获得 f"],
    ["削弱反射", "消波材料或延长水槽"],
    ["重复采样", "每个水深报告不确定度"],
    ["进入浅水区", "更长波长或更小水深"],
  ];
  items.forEach((it, i) => {
    const x = 0.82 + i * 3.05;
    const y = 2.62;
    card(s, x, y, 2.72, 2.12, i === 3 ? C.lavender : C.white, i === 3 ? C.purpleLine : C.line);
    s.addText(String(i + 1), { x: x + 0.23, y: y + 0.26, w: 0.38, h: 0.26, fontFace: "Aptos", fontSize: 13.2, bold: true, color: C.purple, margin: 0 });
    s.addText(it[0], { x: x + 0.23, y: y + 0.72, w: 2.2, h: 0.3, fontFace: FONT, fontSize: 13.2, bold: true, color: C.ink, margin: 0, align: "center", fit: "shrink" });
    s.addText(it[1], { x: x + 0.25, y: y + 1.25, w: 2.18, h: 0.42, fontFace: FONT, fontSize: 10.1, color: C.mute, margin: 0, align: "center", fit: "shrink" });
    if (i < items.length - 1) lineArrow(s, x + 2.76, y + 1.06, 0.27, "C9B5D3", 1.8);
  });
  tag(s, "目标", 2.05, 5.72);
  s.addText("获得可与色散公式直接比较的相速度。", { x: 2.92, y: 5.75, w: 5.0, h: 0.23, fontFace: FONT, fontSize: 12.2, bold: true, color: C.ink, margin: 0 });
}

function slide14() {
  const s = pptx.addSlide();
  s.background = { color: C.deep };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.deep }, line: { color: C.deep } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.purple, transparency: 18 }, line: { transparency: 100 } });
  s.addImage({ path: img("cover_wave_tint.png"), x: 7.45, y: 0.82, w: 5.05, h: 3.82, transparency: 20 });
  logo(s, true, 0.82, 0.62, 1.55, 0.56);
  s.addText("结论", { x: 0.88, y: 1.68, w: 2.2, h: 0.42, fontFace: FONT, fontSize: 24, bold: true, color: C.white, margin: 0 });
  const lines = ["视频重建得到平均波长与表观波速。", "推荐波长约 8 cm，多数水深接近深水近似。", "表观波速受反射和峰纹追踪影响，不能直接等同理论相速度。"];
  lines.forEach((t, i) => {
    const y = 2.55 + i * 0.78;
    s.addShape(pptx.ShapeType.ellipse, { x: 0.95, y: y + 0.05, w: 0.17, h: 0.17, fill: { color: i === 1 ? C.plum2 : "E3B6EE" }, line: { color: i === 1 ? C.plum2 : "E3B6EE" } });
    s.addText(t, { x: 1.35, y, w: 6.35, h: 0.42, fontFace: FONT, fontSize: 14.2, bold: i === 2, color: C.white, margin: 0, fit: "shrink" });
  });
  s.addShape(pptx.ShapeType.line, { x: 0.92, y: 5.35, w: 5.7, h: 0, line: { color: "B98BCC", width: 1.2 } });
  s.addText("谢谢聆听", { x: 0.9, y: 5.72, w: 2.5, h: 0.36, fontFace: FONT, fontSize: 20, bold: true, color: C.white, margin: 0 });
  s.addText("欢迎老师提问", { x: 0.92, y: 6.18, w: 2.5, h: 0.22, fontFace: FONT, fontSize: 11, color: "E3C7EC", margin: 0 });
}

[
  slide1, slide2, slide3, slide4, slide5, slide6, slide7,
  slide8, slide9, slide10, slide11, slide12, slide13, slide14,
].forEach((fn) => fn());

pptx.writeFile({ fileName: outPptx }).then(() => console.log(outPptx));
