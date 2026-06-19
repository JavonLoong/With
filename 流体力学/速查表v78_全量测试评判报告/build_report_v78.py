from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
V72_DIR = ROOT / "速查表v72_全量测试评判报告"
OUT = ROOT / "速查表v78_全量测试评判报告"

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
base.CHEATSHEET_PDF = ROOT / "期末六页A4速查表" / "期末六页A4速查表_最终主用版_已修正_v78.pdf"
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
    0.84,
    " v78 已补新题定位入口、非定常 Bernoulli 推导条件、速度势单值/路径无关证明、Lagrange/Kelvin 可抄证明句、涡管强度 ΩA 守恒、涡量矩模板、自由射流动量通量和 RTT 入口；更长证明仍需教材措辞。",
)
bump_rule(
    "量纲分析/相似准则",
    0.84,
    " v78 保留量纲齐次/Rayleigh 指数配平、完全/部分相似及 Re/Fr 冲突说明、关键词到 π 群的定位入口、球阻力 CD=f(Re) 标准推导；冷门变量仍需逐项列量纲。",
)
bump_rule(
    "边界层/外绕流阻力",
    0.86,
    " v78 保留给定速度剖面到 delta、theta、delta_E、tau_w、CD 的通用积分链，新增层/湍速度剖面标准句和 Boussinesq 涡黏概念；并保留吸气/吹气修正、自由射流动量通量入口、Theta 分离判据和 Karman--Pohlhausen 配边界步骤。",
)
bump_rule(
    "概念简答/定义解释",
    0.87,
    " v78 已补 N-S 各项标准意义、层/湍速度剖面、Boussinesq 涡黏、水击波速因素、孔板/自由射流概念、渐变流测压管水头、Ma 物理意义与 0.3 判据、深水/浅水定义、RTT 守恒入口、完全/部分相似短答和标准四行答案模板，适合先写过程分。",
)
bump_rule(
    "Bernoulli/机械能/动量控制体",
    0.83,
    " v78 保留雷诺输运、压力力方向/表压、孔板/文丘里流量计公式链，并补自由射流动量通量提示；复杂控制体仍需画受力图。",
)
bump_rule(
    "势流/圆柱/镜像/升力",
    0.82,
    " v78 保留薄板小攻角环量估计和 Kutta 升力收口；复杂构形仍需正确选镜像/基元。",
)
bump_rule(
    "可压缩流/喷管/激波/膨胀波",
    0.81,
    " v78 保留喷管/激波/PM 查表动作和 0.528 易错判断，并补 Fanno 等截面绝热摩擦管入口；同时保留 Ma 物理意义、等熵任意两点、最大速度、弱/强斜激波、脱体激波、PM 最大偏转、背压/出口内压易错和波阻概念；复杂波系仍需按图逐段判支路。",
)
bump_rule(
    "水波/水击/课程概念缺口",
    0.88,
    " v78 已在第一页和反推模板中补水击/声速/水波/明渠定位，新增水击波速因素与近似公式，保留深水波 h>lambda/2(kh>pi) 标准定义、浅水判据、色散关系和水击快关公式；少量冷门波动推导仍需教材。",
)

old_estimate = base.estimate


def replace_version(text: str) -> str:
    for old in ["v10", "v6", "v70", "v71", "v72", "v73", "v74", "v75", "v76", "v77"]:
        text = re.sub(rf"(?<![A-Za-z0-9]){old}(?![A-Za-z0-9])", "v78", text)
        text = re.sub(rf"(?<![A-Za-z0-9]){old.upper()}(?![A-Za-z0-9])", "v78", text)
    return text


def estimate_v78(rule: dict, question_text: str, group: str, max_score: float) -> tuple[float, str, str]:
    est, basis, confidence = old_estimate(rule, question_text, group, max_score)
    return est, replace_version(basis), confidence


base.estimate = estimate_v78


def postprocess_v78() -> None:
    literal_replacements = [
        ("期末六页A4速查表_v6_结构导航版.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_v6_结构导航版.tex", "期末六页A4速查表_最终主用版.tex"),
        ("期末六页A4速查表_最终主用版_已修正_v10.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v70.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v71.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v72.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v73.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v74.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v75.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v76.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v77.pdf", "期末六页A4速查表_最终主用版_已修正_v78.pdf"),
        ("只靠 v78 得分", "只靠 v78 过程覆盖估计得分"),
        ("只靠 v78 折算得分", "只靠 v78 过程覆盖估计得分"),
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
        if path.name in {"最终报告.md", "06_深度评判与改进建议.md", "00_评测说明与范围.md"}:
            if "关键词/模型/公式链/查表动作" not in text:
                text += note
        path.write_text(text, encoding=encoding)


def main() -> None:
    base.main()
    postprocess_v78()


if __name__ == "__main__":
    main()


