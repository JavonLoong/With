from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
V72_DIR = ROOT / "速查表v72_全量测试评判报告"
OUT = ROOT / "速查表v81_全量测试评判报告"

spec = importlib.util.spec_from_file_location(
    "build_report_v72_module",
    V72_DIR / "build_report_v72.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("无法加载 v72 评判脚本")

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
base = module.base

base.OUT = OUT
base.TEXT_DIR = OUT / "extracted_text"
base.SOURCE_MANIFEST = OUT / "02_题源清单.csv"
base.ITEM_CSV = OUT / "05_全量逐题解决路径.csv"
base.CHEATSHEET_PDF = ROOT / "期末六页A4速查表" / "期末六页A4速查表_最终主用版_已修正_v81.pdf"
base.CHEATSHEET_TEX = ROOT / "期末六页A4速查表" / "期末六页A4速查表_最终主用版.tex"


def bump_rule(topic: str, score: float | None = None, supplement_append: str = "") -> None:
    for rule in base.TOPIC_RULES:
        if rule["topic"] == topic:
            if score is not None:
                rule["base"] = score
            if supplement_append and supplement_append not in rule["supplement"]:
                rule["supplement"] += supplement_append
            return


bump_rule(
    "流体运动学/连续/流线迹线",
    0.87,
    " v81 保留新题定位入口、非定常 Bernoulli 推导条件、速度势单值/路径无关证明、Lagrange/Kelvin 可抄证明句、涡管强度 ΩA 守恒、涡量矩模板、自由射流动量通量和 RTT 入口，并新增证明题关键词卡，补纳维-斯托克斯原词、圆管断面速度分布原词、渐变流测压管水头；长证明仍需教材措辞。",
)
bump_rule(
    "量纲分析/相似准则",
    0.86,
    " v81 保留量纲齐次/Rayleigh 指数配平、完全/部分相似及 Re/Fr 冲突说明、关键词到 π 群的定位入口、球阻力 CD=f(Re) 标准推导，并补量纲公式、雷诺相似、自模化和压力系数 Cp/Eu 定义；冷门变量仍需逐项列量纲。",
)
bump_rule(
    "边界层/外绕流阻力",
    0.88,
    " v81 保留给定速度剖面到 delta、theta、delta_E、tau_w、CD 的通用积分链，补强 delta、delta*、theta、delta_E 的物理意义，保留层/湍速度剖面标准句、Boussinesq 涡黏、吸气/吹气修正、自由射流动量通量入口、Theta 分离判据、Karman--Pohlhausen 配边界步骤，并在证明卡中写入边界层积分推导链。",
)
bump_rule(
    "概念简答/定义解释",
    0.91,
    " v81 已补简答题首句索引：N-S、深水波、水击波速、渐变流、圆管层/湍速度分布、完全/部分相似；并保留控制体外力组成、Boussinesq 涡黏、孔板/自由射流概念、Ma 物理意义与 0.3 判据、RTT 守恒入口和标准四行答案模板。",
)
bump_rule(
    "Bernoulli/机械能/动量控制体",
    0.85,
    " v81 保留雷诺输运、压力力方向/表压、孔板/文丘里流量计公式链，并补控制体外力组成、自由射流动量通量提示和 RTT/控制体证明首句；复杂控制体仍需画受力图。",
)
bump_rule(
    "粘性管路/沿程局部损失/泵水轮机",
    0.85,
    " v81 保留管路机械能、沿程/局部损失、泵/水轮机功率、Moody/Colebrook 入口，并补圆管层流抛物线速度分布、湍流丰满剖面和平均/最大速度易错。",
)
bump_rule(
    "势流/圆柱/镜像/升力",
    0.82,
    " v81 保留薄板小攻角环量估计和 Kutta 升力收口；复杂构形仍需正确选镜像/基元。",
)
bump_rule(
    "可压缩流/喷管/激波/膨胀波",
    0.81,
    " v81 保留喷管/激波/PM 查表动作和 0.528 易错判断，并补 Fanno 等截面绝热摩擦管入口；同时保留 Ma 物理意义、等熵任意两点、最大速度、弱/强斜激波、脱体激波、PM 最大偏转、背压/出口内压易错和波阻概念；复杂波系仍需按图逐段判支路。",
)
bump_rule(
    "水波/水击/课程概念缺口",
    0.88,
    " v81 保留第一页和反推模板中的水击/声速/水波/明渠定位、水击波速因素与近似公式、深水波 h>lambda/2(kh>pi) 标准定义、浅水判据、色散关系和水击快关公式；少量冷门波动推导仍需教材。",
)

old_estimate = base.estimate


def replace_version(text: str) -> str:
    for old in ["v10", "v6", "v70", "v71", "v72", "v73", "v74", "v75", "v76", "v77", "v78", "v79", "v80"]:
        text = re.sub(rf"(?<![A-Za-z0-9]){old}(?![A-Za-z0-9])", "v81", text)
        text = re.sub(rf"(?<![A-Za-z0-9]){old.upper()}(?![A-Za-z0-9])", "v81", text)
    return text


def estimate_v81(rule: dict, question_text: str, group: str, max_score: float) -> tuple[float, str, str]:
    est, basis, confidence = old_estimate(rule, question_text, group, max_score)
    q = question_text or ""
    proof_like = re.search(r"证明|推导|定理|单值|路径无关|涡通量|涡管|涡量矩|边界层积分|雷诺输运|动量矩", q)
    short_answer_like = re.search(r"简述|写出.*意义|断面流速分布|深水波|水击波|渐变流|纳维|N-S|完全相似|部分相似|自模化", q)
    bonus = 0.0
    if proof_like:
        bonus += 0.04 * max_score
        basis += "；v81 新增证明题关键词卡，能按条件-方程-边界/积分路径-结论写过程。"
    if short_answer_like:
        bonus += 0.03 * max_score
        basis += "；v81 新增简答题首句索引，覆盖本题常见原词。"
    if bonus:
        est = min(max_score * 0.86, est + bonus)
    return est, replace_version(basis), confidence


base.estimate = estimate_v81


def postprocess_v81() -> None:
    literal_replacements = [
        ("期末六页A4速查表_v6_结构导航版.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_v6_结构导航版.tex", "期末六页A4速查表_最终主用版.tex"),
        ("期末六页A4速查表_最终主用版_已修正_v10.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v70.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v71.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v72.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v73.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v74.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v75.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v76.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v77.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v78.pdf", "期末六页A4速查表_最终主用版_已修正_v81.pdf"),
        ("只靠 v81 得分", "只靠 v81 过程覆盖估计得分"),
        ("只靠 v81 折算得分", "只靠 v81 过程覆盖估计得分"),
    ]
    note = (
        "\n\n> 说明：本报告是关键词/模型/公式链/查表动作的过程覆盖估计，"
        "不是满分证明；扫描图、教材完整表和现场读图仍需人工能力。\n"
    )
    for path in OUT.glob("*"):
        if path.suffix.lower() not in {".md", ".csv", ".json"}:
            continue
        encoding = "utf-8-sig" if path.suffix.lower() == ".csv" else "utf-8"
        text = path.read_text(encoding=encoding, errors="replace")
        for old, new in literal_replacements:
            text = text.replace(old, new)
        text = replace_version(text)
        text = re.sub(
            r"对最完整可读的 2022 春期末卷，结论仍是约 \*\*[^*]+\*\*：简答题约 [^，]+，计算分析题约 [^。]+。v81 对计算题很有用，但不能让完全没学过的人稳定拿高分。",
            "对最完整可读的 2022 春期末卷，本脚本按“题干关键词→模型→公式链→查表动作→易错检查”估计过程覆盖；具体分数以本文下方折算表为准。该分数仍不是满分证明；简答题、现场读图和查表细节仍可能失分。",
            text,
        )
        text = re.sub(
            r"预计 2022 这类卷可由约 [^ ]+ 提升到约 [^。]+。",
            "下一轮目标是把低于 70 的条目继续压缩，并补足简答、读图和查表细节，而不是针对某一套卷押题。",
            text,
        )
        text = re.sub(
            r"可读期末卷按各题过程分折算，平均约 \*\*[^*]+/100\*\*。其中 2022 春期末卷因为题干最完整，估分仍约 \*\*[^*]+\*\*；其他试卷若题干抽取质量较差，分数信心较低。",
            "可读期末卷按各题过程分折算，平均值和各卷分数以报告表格为准；其中 2022 春期末卷因题干最完整，分数信心相对更高，其他试卷若题干抽取质量较差，分数信心较低。",
            text,
        )
        if path.name in {"最终报告.md", "06_深度评判与改进建议.md", "00_评测说明与范围.md"}:
            if "关键词/模型/公式链/查表动作" not in text:
                text += note
        path.write_text(text, encoding=encoding)


def main() -> None:
    base.main()
    postprocess_v81()


if __name__ == "__main__":
    main()


