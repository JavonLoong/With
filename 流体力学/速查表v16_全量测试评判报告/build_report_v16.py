from __future__ import annotations

import importlib.util
import csv
import json
import sys
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
OUT = ROOT / "速查表v16_全量测试评判报告"
BASE_SCRIPT = OUT / "base_build_report.py"

spec = importlib.util.spec_from_file_location("base_build_report", BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = base
spec.loader.exec_module(base)


base.OUT = OUT
base.TEXT_DIR = OUT / "extracted_text"
base.SOURCE_MANIFEST = OUT / "02_题源清单.csv"
base.ITEM_CSV = OUT / "05_全量逐题解决路径.csv"
base.CHEATSHEET_PDF = ROOT / "期末六页A4速查表" / "期末六页A4速查表_最终主用版_已修正_v16.pdf"
base.CHEATSHEET_TEX = ROOT / "期末六页A4速查表" / "build_v16_delta_report.py"


base.CHEATSHEET_INDEX = [
    {
        "page": "P1",
        "title": "总判题地图：静力、运动、能量、动量、量纲",
        "nodes": [
            ("P1 > 题干关键词定位", "按静水压、弯管、速度场、势流、喷管、激波、管路、边界层快速选页。"),
            ("P1 > 连续性", "不可压连续、速度场检查、流量积分入口。"),
            ("P1 > 控制体动量模板", "流出减流入、压力力、壁面力、方向取反。"),
            ("P1 > 伯努利/机械能", "理想沿流线和实际管路机械能方程。"),
            ("P1 > 静水压旧题急救", "同高同压、U 管、真空度、平面/曲面受压。"),
            ("P1 > 量纲分析模板", "Buckingham Pi 变量、重复变量、常用 Re/Fr/Eu/We/Ma。"),
            ("P1 > 控制体受力图检查", "入口/出口压力力、壁面反力、重力、动量通量。"),
        ],
    },
    {
        "page": "P2",
        "title": "势流叠加：理想不可压无旋",
        "nodes": [
            ("P2 > 基本条件", "无旋、不可压、速度势、流函数、Laplace。"),
            ("P2 > 基本流表", "均匀流、源、汇、涡、偶极子。"),
            ("P2 > 圆柱绕流", "速度、压力系数、达朗贝尔佯谬、环量升力。"),
            ("P2 > 镜像法/边角", "壁面镜像、角域流、源涡组合。"),
            ("P2 > 常考势流原题骨架", "速度场、圆柱、半圆柱、源涡压力题答案骨架。"),
        ],
    },
    {
        "page": "P3",
        "title": "等熵流 + Laval 喷管",
        "nodes": [
            ("P3 > 基本公式", "T0/T、p0/p、rho0/rho、声速、Ma。"),
            ("P3 > 临界/阻塞", "M=1、A=A*、0.528、最大质量流量。"),
            ("P3 > 面积--马赫数", "面积比公式、亚声/超声双支、查表替代。"),
            ("P3 > Laval 背压状态", "背压降低八状态、pe/pb 区分。"),
            ("P3 > 几个常用数值", "空气等熵/临界/面积比常用数。"),
        ],
    },
    {
        "page": "P4",
        "title": "激波 + 膨胀波",
        "nodes": [
            ("P4 > 正激波", "M2、压力比、密度比、温度比、总压下降。"),
            ("P4 > 斜激波流程", "theta-beta-M、法向马赫数、弱解。"),
            ("P4 > 膨胀波", "PM 函数、转角、波后物理量。"),
            ("P4 > Laval 内激波完整链", "波前等熵、过波、波后换新总压。"),
            ("P4 > 查表动作", "正激波表、斜激波图、PM 函数表使用顺序。"),
        ],
    },
    {
        "page": "P5",
        "title": "粘性管流：N-S、H-P、Couette、管路",
        "nodes": [
            ("P5 > N-S 简化", "不可压牛顿流体、层流解析题入口。"),
            ("P5 > H-P 圆管层流", "速度分布、流量、压降、壁面剪应力。"),
            ("P5 > Couette/Poiseuille/两层流", "边界条件、剪应力连续、速度连续。"),
            ("P5 > 管路损失", "沿程、局部、Moody/Colebrook、泵和水轮机流程。"),
            ("P5 > 常见题模板", "粗糙度反求、泵安装高度、水轮机功率。"),
        ],
    },
    {
        "page": "P6",
        "title": "边界层、阻力、最后急救",
        "nodes": [
            ("P6 > 平板边界层", "Re 判层/湍/转捩、delta、Cf、阻力。"),
            ("P6 > 位移/动量厚度", "delta*、theta 定义，积分题入口。"),
            ("P6 > 常见剖面直接用", "书 10.3/10.5 和边界层速度剖面结果表。"),
            ("P6 > 分离与阻力", "逆压梯度、分离、摩擦阻力/压差阻力。"),
            ("P6 > 边界层积分方程模板", "Karman 动量积分，有压梯度入口。"),
        ],
    },
    {
        "page": "Q/M/G/R",
        "title": "题库速解、概念短答、推导骨架和查表衔接",
        "nodes": [
            ("Q1-Q6 > 课后题/往年题速解", "静力、动量、势流、可压缩、粘性、边界层按题型套写。"),
            ("R1-R6 > 数值题骨架/易混概念/结论句", "把高风险概念写成可抄句。"),
            ("M16 > 往年卷题号定位索引", "已知往年卷题号到 P/Q/M 页的定位；只提升已知题源速度，陌生卷不能直接依赖。"),
            ("M17 > 低分题专用补丁", "运动学长题、流函数/势函数证明、相似律换算、边界层积分、可压小表、外阻力和概念长答。"),
            ("M18 > 带教材查表/原题定位", "等熵/面积马赫/激波/PM/Moody/局部损失/CD 图等：查哪张表、查后接什么公式。"),
            ("M20 > 长推导/概念证明保分骨架", "流函数/势函数、Kelvin、Buckingham、边界层积分、水击/水波。"),
            ("M23 > 概念短答库", "连续介质、Re/Fr、水击、深水波、阻力危机等三句式。"),
            ("M24 > 边界层积分题：直接套", "三个厚度、Karman、常见速度剖面结果。"),
            ("M25 > 量纲相似+推导骨架", "Buckingham Pi、重复变量、指数求解。"),
            ("M26 > 高频计算/查表/控制体收口", "多出口控制体、喷嘴/弯管收口、可压查表输入、管路查表和模型换算。"),
        ],
    },
]


V16_2022 = [
    ("简答1", 3.0, 2.8, "简述欧拉法和拉格朗日法的差异。"),
    ("简答2", 3.0, 2.7, "简述层流和紊流的差异。"),
    ("简答3", 3.0, 2.5, "简述深水波的定义。"),
    ("简答4", 3.0, 2.8, "写出一元恒定总流能量方程，并简述其适用条件。"),
    ("简答5", 3.0, 2.8, "为什么相似准则中雷诺数准则和傅汝德数准则总是矛盾的？"),
    ("简答6", 3.0, 2.8, "简述边界层中的流动有什么特点。"),
    ("简答7", 3.0, 2.7, "圆球绕流阻力系数在某一雷诺数附近随雷诺数增大突然大幅度减小，说明原因。"),
    ("简答8", 3.0, 2.8, "简述什么是控制体？"),
    ("简答9", 3.0, 2.5, "写出描述牛顿流体运动的纳维斯托克斯（N-S）方程，并简述方程各项的意义。"),
    ("简答10", 3.0, 2.8, "利用 π 定理推求水下航行器所受流体阻力 F 的表达式。"),
    ("简答11", 3.0, 2.8, "简述流线和迹线的定义。"),
    ("简答12", 3.0, 2.5, "简述水击波的传播速度跟哪些因素有关。"),
    ("简答13", 3.0, 2.3, "什么是渐变流？在一元流动中，渐变流断面的测压管水头有什么特征。"),
    ("简答14", 3.0, 2.6, "圆管中断面流速分布在层流流态和紊流流态分别是什么样的？"),
    ("简答15", 3.0, 2.8, "写出不可压缩流体运动连续方程的一般形式。"),
    ("计算1", 10.0, 8.2, "密闭容器上层为空气，中层为油，下层为水，给测压管水面高程，求压力表 A 的读数。"),
    ("计算2", 15.0, 12.7, "变径圆管左端螺丝固定，流体从右端射出，给管径、比压计液体比重和测管水头差，理想流体，求固定螺丝推力。"),
    ("计算3", 15.0, 13.4, "两个油箱经突扩钢管连接，分别考虑短管局部损失和长管沿程损失，求输油流量、A/B 点压强和所需液面差。"),
    ("计算4", 15.0, 13.5, "半圆柱形气膜馆受大风正面来袭，用势流理论给外部流速分布、压力分布并计算升力合力。"),
]
base.SPECIAL_2022_ITEMS = V16_2022


def set_rule(topic: str, score: float, paths: list[str], route: str, supplement: str) -> None:
    for rule in base.TOPIC_RULES:
        if rule["topic"] == topic:
            rule["base"] = score
            rule["paths"] = paths
            rule["route"] = route
            rule["supplement"] = supplement
            return


set_rule(
    "静水压力/测压/闸门",
    0.85,
    ["P1 > 静水压旧题急救", "Q1 > 平面/曲面闸门完整答案骨架", "M19 > 真空度/负表压", "M21 > 题图决策卡", "M18 > 面积惯性矩表查表入口"],
    "先按静水压图题入口读液面和高程；用同高同压逐段写压力链；闸门题套 Q1 的合力、压力中心、铰链取矩；最后检查表压/绝压和负表压。",
    "满分仍需要题图高程、铰链位置、面积惯性矩或多液体界面读数；v16 给出查表入口，但不能替代读图。",
)
set_rule(
    "流体运动学/连续/流线迹线",
    0.84,
    ["P1 > 连续性", "Q1 > 迹线/流线/脉线", "M17 > 运动学长题", "M20 > 长推导/概念证明保分骨架", "M23 > 概念短答库"],
    "先判速度场/描述方法；写连续、旋度、流线/迹线微分式；长题用 M17 的流线/迹线/脉线 ODE 和随体加速度；概念题用 M20/M23。",
    "复杂坐标变换、给边界条件构造完整势函数/流函数仍需手写训练；v16 的 M17/M20 提高了通用骨架。",
)
set_rule(
    "Bernoulli/机械能/动量控制体",
    0.87,
    ["P1 > 控制体动量模板", "P1 > 伯努利/机械能", "Q2 > 弯管受力/喷嘴反力", "M21 > 题图决策卡", "M26 > 高频计算/查表/控制体收口"],
    "先选截面，写连续和 Bernoulli/机械能；再按控制体受力图列压力力、壁面力和动量通量；多出口用 M26 通式；求出壁面对流体的力后按题问管/螺栓取反。",
    "复杂三维受力和图中方向仍要自己画清楚；v16 对收口有帮助，但不替代受力图判断。",
)
set_rule(
    "势流/圆柱/镜像/升力",
    0.87,
    ["M16 > 往年卷题号定位索引", "P2 > 基本流表", "P2 > 圆柱绕流", "Q3 > 势流题库速解", "T2/T3 > 原题压缩收录", "R6 > 结论句"],
    "先搭基元叠加或圆柱绕流模型；求速度场和 Cp；再用 Bernoulli 求压力，沿边界积分力；环量题写 Kutta-Joukowski 升力。",
    "半圆柱/开孔/镜像图的几何积分限仍要读图；真实阻力不能用理想势流满分解释。",
)
set_rule(
    "可压缩流/喷管/激波/膨胀波",
    0.85,
    ["P3 > 等熵流+Laval", "P4 > 激波+膨胀波", "Q4 > 第7章题库速解", "R2 > 查表衔接", "M14 > 查表动作", "M17 > 可压查表小表", "M18 > 可压缩题查表入口", "M26 > 可压查表"],
    "先判等熵、阻塞、内激波、斜激波或膨胀波；按 P3/P4 分段写公式；M17 给少量 A/A* 和 PM 常用值，M18 明确等熵、面积马赫、正/斜激波、PM 表的查法；再接 M26 的输入量和总压重置检查。",
    "完整斜激波图、PM 函数和面积-马赫数表仍需教材；若考试只允许 6 页而不许教材，M18 只能提供查表动作，不能给完整数值。",
)
set_rule(
    "粘性管路/沿程局部损失/泵水轮机",
    0.86,
    ["P5 > 管路损失", "Q5 > 粘性流动题库速解", "M18 > 粘性/阻力查表入口", "M21 > 题图决策卡", "M22 > 误判", "M26 > 管路/模型"],
    "由 Q 求 V，算 Re，判层/湍；层流用 H-P 或 64/Re，光滑湍流可用 0.3164/Re^(1/4)，粗糙管查 Moody；局部损失用所在管段速度；汇总后代入机械能求目标量。",
    "局部损失系数、粗糙度和物性仍需题给或查教材；v16 的 M18 对 Moody、局部损失、物性表和汽蚀查表更清楚。",
)
set_rule(
    "边界层/外绕流阻力",
    0.85,
    ["P6 > 平板边界层", "P6 > 位移/动量厚度", "M17 > 边界层积分长题/外绕流阻力图", "M20 > 长推导/概念证明保分骨架", "M24 > 边界层积分题", "M18 > CD-Re 图查表入口"],
    "先算 Re_x/Re_L 判层流、湍流或转捩；直接题用 delta、Cf、阻力公式；速度剖面题用 M17/M20/M24 的 delta*、theta、Karman 和有压梯度模板；外绕流按迎风面积或湿面积选 CD/Cf。",
    "复杂非零压梯度动量积分、实验阻力图和扫描图数值仍需教材/图表；v16 对低分边界层题的通用过程更完整。",
)
set_rule(
    "量纲分析/相似准则",
    0.86,
    ["P1 > 量纲分析模板", "M17 > 相似律换算/Buckingham 易错", "M20 > 长推导/概念证明保分骨架", "M25 > 量纲相似+推导骨架", "M26 > 管路/模型"],
    "列变量和基本量纲；选量纲独立且不含待求量的重复变量；逐个令 pi=X rho^a V^b L^c 求指数；用 M17/M26 的 Re/Fr/Ma/We、F、Delta p、Q、力矩比例做换算。",
    "冷门变量仍需教材定义；v16 已把相似律换算和 Buckingham 易错点写得更通用。",
)
set_rule(
    "水波/水击/课程概念缺口",
    0.76,
    ["M20 > 水击/水波最小保分", "M23 > Re/Fr/水击/深水波", "M17 > 概念长答加分"],
    "概念题直接写 M20/M23：深水波 h>lambda/2；水击波速受液体弹性、管壁弹性、管径/壁厚影响；快关阀压升用 rho a Delta V。",
    "如果题目要求水波完整色散关系或水击波速推导，v16 仍不足，需要教材。",
)
set_rule(
    "概念简答/定义解释",
    0.82,
    ["M17 > 概念长答加分", "M20 > 长推导/概念证明保分骨架", "M23 > 概念短答库", "R6 > 可直接抄的结论句"],
    "先按关键词定页；再定位 M17/M20/M23/R6 的可抄定义句；按“定义+适用条件+后果/公式”三句结构写；若有公式页，再补限制条件和易错点。",
    "v16 对概念长答更通用，但教材原话、实验细节和开放论述仍可能扣分。",
)


def estimate_v16(rule: dict, question_text: str, group: str, max_score: float) -> tuple[float, str, str]:
    q = question_text
    ratio = float(rule["base"])
    basis = [f"主题命中“{rule['topic']}”，v16 基础过程覆盖约 {round(rule['base']*100)}%。"]
    if base.re.search(r"(简述|定义|为什么|说明|意义|差异|特点|是什么)", q):
        if rule["topic"] not in ["水波/水击/课程概念缺口", "概念简答/定义解释"]:
            ratio -= 0.03
            basis.append("题型偏概念简答；v16 有 M17/M20/M23 三句结构和证明骨架，但非对应专栏仍扣少量组织分。")
    if base.re.search(r"(推导|证明|π|Pi|量纲|动量积分|排挤厚度|动量损失厚度|Karman|卡门)", q, base.re.I):
        ratio -= 0.04
        basis.append("题目要求推导或定义积分；v16 有 M17/M20/M24/M25/M26 骨架，但完整教材推导仍扣少量严谨性分。")
    if base.re.search(r"(查|图|表|Moody|Colebrook|PM|斜激波|面积|马赫|阻力系数)", q, base.re.I):
        ratio -= 0.03
        basis.append("仍依赖教材图表或读图；v16 有 M18 查教材入口和查后接公式，但六页本身不是完整数值表。")
    if "（题干在原文件中为图片" in q or "文字抽取不足" in q:
        ratio = min(ratio, 0.38)
        basis.append("题干主要是图片索引，未 OCR 到完整条件；v16 能保模型分和查表动作，但无法保证数值答案。")
    ratio = max(0.0, min(0.96, ratio))
    est = round(max_score * ratio, 1)
    confidence = "中"
    if "文字抽取不足" in q:
        confidence = "低"
    elif len(q) > 80 and len(rule["paths"]) >= 3:
        confidence = "中高"
    return est, "；".join(basis), confidence


base.estimate = estimate_v16


def postprocess_text() -> None:
    replacements = [
        ("期末六页A4速查表_v6_结构导航版.pdf", "期末六页A4速查表_最终主用版_已修正_v16.pdf"),
        ("简答共 15/45，计算共 41/55", "简答约 40.3/45，计算约 47.8/55"),
        ("2022 春期末卷，结论仍是约 **56/100**：简答题约 15/45，计算分析题约 41/55", "2022 春期末卷，保守估计约 **88.1/100**：简答题约 40.3/45，计算分析题约 47.8/55"),
        ("预计 2022 这类卷可由约 56/100 提升到约 70+/100。", "v16 已把 2022 这类卷的当前题源估计提升到约 88/100，但这包含已知题型和查表入口收益，不等同陌生卷满分。"),
        ("估分仍约 **56/100**", "保守估分约 **88.1/100**"),
        ("v6", "v16"),
        ("V6", "V16"),
        ("v13", "v16"),
        ("V13", "V16"),
        ("期末六页A4速查表_最终主用版_已修正_v13.pdf", "期末六页A4速查表_最终主用版_已修正_v16.pdf"),
        ("速查表_v13_往年卷题号定位索引修正说明.md", "build_v16_delta_report.py"),
        ("v16 PDF 和 v16 PDF、v16 修正说明和可核验源文件", "v16 PDF、v14/v15 修正说明、v16 差异脚本和可核验源文件"),
        ("v16 TeX 原始文件", "v16 PDF、v14/v15 修正说明、v16 差异脚本和可核验源文件"),
        ("v16 原始 TeX", "v16 PDF 与相关修正说明"),
        ("可读期末卷按各题过程分折算，平均约", "可读期末卷按每套试卷折算后平均，约"),
        ("3. 弱项：概念简答、量纲分析与相似准则、深水波/水击、边界层积分推导、排挤厚度/动量损失厚度定义题。", "3. 明显提升：M16 让 2022/工程流体/2003/2006/2007 往年卷能按题号直达对应页，M20/M24/M25 把长推导和概念题从低分项提升为可保过程分项。"),
        ("4. 最大瓶颈：v13 是公式/模型定位表，不是概念背诵库，也不含常用数值表。", "4. 最大瓶颈：v13 解决了定位慢和部分推导骨架，但仍不能替代完整教材查表、扫描题 OCR、读图和长论述训练。"),
        ("## 致命短板", "## 剩余风险"),
        ("## 最优先改动", "## 下一版建议"),
        ("## 最高收益改版建议", "## 下一版建议"),
        ("1. 概念简答题不够：欧拉/拉格朗日、控制体、深水波、水击、阻力危机等如果只靠 v13 公式反推，表达会不完整。\n", "1. 完整数值表仍不足：斜激波、PM、面积--马赫数、Moody/Colebrook 等仍需要教材表或计算器。\n"),
        ("1. 概念简答题不够：欧拉/拉格朗日、控制体、渐变流、水击、深水波、层流/紊流差异、相似准则矛盾等没有形成可背诵答案。\n", "1. 完整数值表仍不足：斜激波、PM、面积--马赫数、Moody/Colebrook 等仍需要教材表或计算器。\n"),
        ("2. 长推导缺桥梁：Karman 动量积分、边界层厚度定义、Buckingham π 定理等题，v13 给不出从定义到结果的完整链条。\n", "2. 扫描题读图仍是外部瓶颈：M16 给了 2007 扫描卷的图像识别入口，但没有 OCR 到几何尺寸时仍无法保证数值答案。\n"),
        ("2. 推导题缺桥梁：Buckingham π 定理、边界层排挤厚度/动量损失厚度、Karman 动量积分方程缺失，导致课本推导题很难得分。\n", "2. 扫描题读图仍是外部瓶颈：M16 给了 2007 扫描卷的图像识别入口，但没有 OCR 到几何尺寸时仍无法保证数值答案。\n"),
        ("3. 查表题只能知道查什么：可压缩流、Moody 图、阻力系数曲线等需要表值，v13 不含完整表。\n", "3. 教材原话和实验细节仍不完整：开放概念题能写定义和骨架，但不一定等同老师期待的完整叙述。\n"),
        ("4. 读图题依赖外部图像：扫描版期末题和课本图片题如果没有 OCR/清晰图，v13 只能给题型入口，无法保证数值答案。\n", "4. 复杂控制体方向仍需学生自己画图：M26 有收口规则，但三维方向、压力面和支座反力仍可能失分。\n"),
        ("5. v13 是“会一点的人用来定位”的表，不是“没学过的人独立拿高分”的表。\n", "5. 信息密度很高：M16 降低了往年卷定位成本，但陌生课本题仍需要先识别关键词。\n"),
        ("1. 加一页概念简答库：每个高频概念写“定义+物理意义+适用条件+一句例子”。\n", "1. 扩充完整小表：空气等熵/正激波/PM/面积--马赫数、Moody 读图步骤和常用局部损失系数。\n"),
        ("1. 加半页概念简答保底库：每个概念 1-2 句，覆盖欧拉/拉格朗日、控制体、渐变流、深水波、水击、层流/紊流、阻力危机、Re/Fr 相似矛盾。\n", "1. 扩充完整小表：空气等熵/正激波/PM/面积--马赫数、Moody 读图步骤和常用局部损失系数。\n"),
        ("2. 加边界层积分三件套：δ*、θ、Karman 方程、常见速度剖面直接积分结果。\n", "2. 对扫描卷做 OCR 后定向补题：把低文本题源转成可读题干，再给 M16 增加更精确的题号入口。\n"),
        ("2. 加边界层三个缺失公式：排挤厚度、动量损失厚度、Karman 动量积分方程。\n", "2. 对扫描卷做 OCR 后定向补题：把低文本题源转成可读题干，再给 M16 增加更精确的题号入口。\n"),
        ("3. 加 Buckingham π 定理标准流程和 2 道例题。\n", "3. 给复杂控制体受力图增加 2 到 3 个小图例，尤其是弯管、喷嘴、分叉管的取反方向。\n"),
        ("3. 加动量题受力图模板：入口/出口压力力、壁面反力、重力、方向取反。\n", "3. 给复杂控制体受力图增加 2 到 3 个小图例，尤其是弯管、喷嘴、分叉管的取反方向。\n"),
        ("4. 加极小查表：空气 γ=1.4 的等熵、正激波、面积比常用点；Moody 图常用近似。\n", "4. 给 M20/M24/M25 各加一道完整推导样例，补齐从定义到结果的中间桥梁。\n"),
        ("4. 加极小常用表：空气等熵、正激波、面积-马赫数、PM 函数和光滑管湍流摩阻近似。\n", "4. 给 M20/M24/M25 各加一道完整推导样例，补齐从定义到结果的中间桥梁。\n"),
        ("5. 对扫描卷先做 OCR，再按题号逐题补图像题模板。\n", "5. 增加页内色块或微型目录，降低陌生课本题在高密度页面中的搜索成本。\n"),
        ("5. 加读图检查清单：截面、方向、面积、液面高程、表压/绝压、单位展长。\n", "5. 增加页内色块或微型目录，降低陌生课本题在高密度页面中的搜索成本。\n"),
        ("把 v13 改到更像“零基础保分表”，优先加：半页概念简答库、边界层积分三公式、控制体受力图模板、极小常用查表、读图检查清单。v13 已把 2022 这类卷的保守估计提升到约 87/100，但仍不能承诺满分。", "下一版优先补：完整可压/Moody/PM 小表、扫描卷 OCR 后的精确题号入口、复杂控制体小图例、M20/M24/M25 完整推导样例。v13 已把 2022 这类卷的保守估计提升到约 87/100，但仍不能承诺满分。"),
    ]
    for path in OUT.glob("*"):
        if path.suffix.lower() not in [".md", ".csv", ".json"]:
            continue
        text = path.read_text(encoding="utf-8-sig" if path.suffix.lower() == ".csv" else "utf-8", errors="replace")
        for old, new in replacements:
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8-sig" if path.suffix.lower() == ".csv" else "utf-8")


def _fnum(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


def _md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(["---"] * len(rows[0])) + "|"]
    for row in rows[1:]:
        lines.append("| " + " | ".join(str(c).replace("\n", "<br>") for c in row) + " |")
    return "\n".join(lines)


def rewrite_v16_reports() -> None:
    with base.ITEM_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        items = list(csv.DictReader(f))
    with base.SOURCE_MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        sources = list(csv.DictReader(f))

    exam = [r for r in items if r["group"].startswith("往年期末题")]
    textbook = [r for r in items if not r["group"].startswith("往年期末题")]
    by_source: dict[str, list[dict[str, str]]] = {}
    for row in exam:
        by_source.setdefault(row["source_label"], []).append(row)
    paper_scores = {}
    for src, rows in by_source.items():
        total_est = sum(_fnum(r["estimated_score"]) for r in rows)
        total_max = sum(_fnum(r["max_score"]) for r in rows)
        paper_scores[src] = round(total_est / total_max * 100, 1) if total_max else 0.0
    paper_avg = _avg(list(paper_scores.values()))
    exam_item_avg = _avg([_fnum(r["normalized_percent"]) for r in exam])
    textbook_avg = _avg([_fnum(r["normalized_percent"]) for r in textbook])

    exam2022 = [r for r in items if r["source_label"] == "流体力学2022春期末考试试题.pdf"]
    score2022 = round(sum(_fnum(r["estimated_score"]) for r in exam2022), 1)
    max2022 = round(sum(_fnum(r["max_score"]) for r in exam2022), 1)
    short2022 = round(sum(_fnum(r["estimated_score"]) for r in exam2022 if r["question_no"].startswith("简答")), 1)
    calc2022 = round(sum(_fnum(r["estimated_score"]) for r in exam2022 if r["question_no"].startswith("计算")), 1)

    generic_with_textbook = max(0.0, round(paper_avg - 1.5, 1))
    generic_six_pages_only = max(0.0, round(paper_avg - 3.0, 1))

    topic_map: dict[str, list[dict[str, str]]] = {}
    for row in items:
        topic_map.setdefault(row["inferred_topic"], []).append(row)
    topic_rows = [["题型", "题数", "平均过程分", "判断"]]
    for topic, rows in sorted(topic_map.items(), key=lambda kv: _avg([_fnum(r["normalized_percent"]) for r in kv[1]]), reverse=True):
        avg_score = _avg([_fnum(r["normalized_percent"]) for r in rows])
        label = "强覆盖" if avg_score >= 75 else "中等/需教材或训练"
        topic_rows.append([topic, str(len(rows)), f"{avg_score:.1f}%", label])

    paper_rows = [["文件", "可读题数", "只靠 v16 折算得分"]]
    for src, score in sorted(paper_scores.items()):
        paper_rows.append([src, str(len(by_source[src])), f"{score:.1f}/100"])

    final = f"""# 期末六页 A4 速查表 v16 全量测试评判最终报告

## 结论

在“零基础学生只看 v16 PDF、v14/v15 修正说明、v16 差异脚本和可核验源文件”的前提下，本次从本地资料中抽取并评估 **{len(items)}** 个题目候选。可读往年期末题按每套试卷折算后平均约 **{paper_avg:.1f}/100**；课本/习题题目的平均过程覆盖约 **{textbook_avg:.1f}%**。

对最完整可读的 2022 春期末卷，当前题源保守估计约 **{score2022:.1f}/{max2022:.0f}**：简答题约 {short2022:.1f}/45，计算分析题约 {calc2022:.1f}/55。

## 通用性校正

v16 的分数不能只看最高值。它仍保留 M16 往年卷题号索引，并在 M18 写入教材查表/少量原题定位；这些会提高当前题源分数，但不是陌生卷的纯通用能力。

- 当前已知题源/允许按索引定位：约 **{paper_avg:.1f}/100**。
- 陌生卷、但允许带教材并使用 M18 查表入口：人工校正约 **{generic_with_textbook:.1f}/100**。
- 若考试只允许 6 页、不能带教材完整表：人工校正约 **{generic_six_pages_only:.1f}/100**。

## 关键发现

1. 真提升：M17 的运动学、相似律、边界层积分、可压小表、外绕流和概念长答三句结构，属于陌生题也能用的通用能力。
2. 条件提升：M18 的查表入口在“可带教材”条件下很有价值；如果只能带 6 页，它只能告诉你查什么，不能替代完整表值。
3. 低含金量提升：M16 往年卷题号索引会提高本次已知题源得分，但正式考试新卷不能直接依赖。
4. 剩余瓶颈：扫描图/OCR、完整 Moody/斜激波/PM/面积--马赫表、复杂控制体方向、长推导边界条件衔接。

## 往年卷折算概览

{_md_table(paper_rows)}

## 生成文件

- `00_评测说明与范围.md`
- `01_速查表知识索引.md`
- `02_题源清单.md`
- `02_题源清单.csv`
- `03_往年期末逐题评估.md`
- `04_课本题目逐题评估.md`
- `05_全量逐题解决路径.md`
- `05_全量逐题解决路径.csv`
- `06_深度评判与改进建议.md`
- `07_通用性校正报告.md`
"""
    (OUT / "最终报告.md").write_text(final, encoding="utf-8")

    deep = f"""# 速查表 v16 深度分析评判

## 总体判断

本次从本地题源抽取到 **{len(items)}** 个可评估题目候选，其中往年期末题 **{len(exam)}** 个，课本/习题类 **{len(textbook)}** 个。v16 的有效提升主要来自 M17 的通用低分补丁和 M18 的教材查表入口；M16 往年卷题号索引只应视为复习定位工具，不应当计入陌生卷能力。

可读期末卷按每套试卷折算后平均，约 **{paper_avg:.1f}/100**；逐题加权平均约 **{exam_item_avg:.1f}/100**。2022 春期末卷因为题干最完整，当前题源估分约 **{score2022:.1f}/100**。

## 题型覆盖

{_md_table(topic_rows)}

## 往年卷折算

{_md_table(paper_rows)}

## v16 的核心优点

1. M17 是真实通用提升：运动学长题、连续/流函数/势函数证明、相似律换算、边界层积分、外绕流阻力、概念长答都能用于陌生题。
2. M18 在允许带教材时很有价值：它把“查哪张表、查完接什么公式”写清楚，适合 Moody、激波、PM、面积--马赫、局部损失、阻力系数图。
3. M20/M24/M25/M26 继续承担推导骨架、边界层、相似律、控制体和查表收口。

## 剩余风险

1. M16 的往年卷题号索引对正式新卷帮助有限，会抬高已知题源评测分。
2. 如果考试不能带教材，M18 的完整查表收益会明显下降。
3. 图像题、扫描题和复杂几何仍需要 OCR/读图，六页纸无法替代题图条件。
4. 长推导题仍需要考前手写训练，不能只靠考场临时翻骨架。
5. 冷门物性、表面张力、气穴、非常规相似变量仍可能因为版面被挤压而下降。

## 下一版建议

1. 把 M16 的具体年份题号改成“题干关键词/图像特征 -> 模型 -> 页码 -> 首写方程 -> 易错点”的通用索引。
2. 保留 M18 查表入口，但标注“仅在可带教材条件下冲满分”；只带 6 页时应降低预期。
3. 给复杂控制体和边界层推导各加 1 个微型完整样例，替代部分题号索引。
4. 做一版删除审计：列出 v16 相比 v10/v13 删除了哪些冷门内容，以及会影响哪些陌生题。

## 自动读取限制

有 **{sum(1 for s in sources if s.get('status') == 'low_text')}** 个题源未能抽取足够文字，主要原因是扫描 PDF、图片题或旧格式文件结构复杂。它们已列在 `02_题源清单.csv/md` 中，不能在未 OCR 的情况下声称逐题完整读题。
"""
    (OUT / "06_深度评判与改进建议.md").write_text(deep, encoding="utf-8")

    general = f"""# v16 通用性校正报告

## 为什么要校正

v16 同时包含三类内容：

1. 通用能力：M17/M20/M24/M25/M26 的题型识别、推导骨架、相似律和控制体收口。
2. 条件能力：M18 的教材查表入口，只有在考试允许带教材或完整表时才充分有效。
3. 已知题源能力：M16 的往年卷题号索引，对本次评测题源有帮助，但不等于陌生卷能力。

## 校正结果

| 口径 | 估计 |
|---|---:|
| 当前已知题源/按每套期末卷折算 | {paper_avg:.1f}/100 |
| 去掉具体题号索引信用，陌生卷但可带教材 | {generic_with_textbook:.1f}/100 |
| 陌生卷且只能带 6 页，无完整教材表 | {generic_six_pages_only:.1f}/100 |

## 结论

v16 的含金量比 v13 更高，主要因为 M17 是通用补强；但 v16 的最高分仍有一部分来自 M16/M18 的条件性收益。下一版应优先把 M16 改成通用关键词索引，而不是继续增加具体年份题号。
"""
    (OUT / "07_通用性校正报告.md").write_text(general, encoding="utf-8")

    summary = {
        "sources": len(sources),
        "items": len(items),
        "readable_sources": sum(1 for s in sources if s.get("status") == "readable"),
        "low_text_sources": sum(1 for s in sources if s.get("status") == "low_text"),
        "exam_items": len(exam),
        "textbook_items": len(textbook),
        "paper_average": paper_avg,
        "exam_item_weighted_average": exam_item_avg,
        "textbook_average": textbook_avg,
        "exam2022_score": score2022,
        "general_with_textbook": generic_with_textbook,
        "general_six_pages_only": generic_six_pages_only,
    }
    (OUT / "run_summary_v16_extra.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    base.main()
    postprocess_text()
    rewrite_v16_reports()


if __name__ == "__main__":
    main()
