from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
V72_DIR = ROOT / "速查表v72_全量测试评判报告"
OUT = ROOT / "速查表v73_全量测试评判报告"

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
base.CHEATSHEET_PDF = ROOT / "期末六页A4速查表" / "期末六页A4速查表_最终主用版_已修正_v73.pdf"
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
    0.80,
    " v73 已补非定常 Bernoulli 推导条件、速度势单值/路径无关证明和涡量矩随体守恒模板；更长证明仍需教材措辞。",
)
bump_rule(
    "量纲分析/相似准则",
    0.82,
    " v73 已补量纲齐次/Rayleigh 指数配平和球阻力 CD=f(Re) 标准推导；冷门变量仍需逐项列量纲。",
)
bump_rule(
    "边界层/外绕流阻力",
    0.82,
    " v73 已补给定速度剖面到 delta、theta、tau_w、CD 的通用积分链，以及 Karman--Pohlhausen 配边界步骤。",
)

old_estimate = base.estimate


def replace_version(text: str) -> str:
    for old in ["v10", "v6", "v70", "v71", "v72"]:
        text = re.sub(rf"(?<![A-Za-z0-9]){old}(?![A-Za-z0-9])", "v73", text)
        text = re.sub(rf"(?<![A-Za-z0-9]){old.upper()}(?![A-Za-z0-9])", "V73", text)
    return text


def estimate_v73(rule: dict, question_text: str, group: str, max_score: float) -> tuple[float, str, str]:
    est, basis, confidence = old_estimate(rule, question_text, group, max_score)
    return est, replace_version(basis), confidence


base.estimate = estimate_v73


def postprocess_v73() -> None:
    literal_replacements = [
        ("期末六页A4速查表_v6_结构导航版.pdf", "期末六页A4速查表_最终主用版_已修正_v73.pdf"),
        ("期末六页A4速查表_v6_结构导航版.tex", "期末六页A4速查表_最终主用版.tex"),
        ("期末六页A4速查表_最终主用版_已修正_v10.pdf", "期末六页A4速查表_最终主用版_已修正_v73.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v70.pdf", "期末六页A4速查表_最终主用版_已修正_v73.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v71.pdf", "期末六页A4速查表_最终主用版_已修正_v73.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v72.pdf", "期末六页A4速查表_最终主用版_已修正_v73.pdf"),
        ("只靠 v73 得分", "只靠 v73 过程覆盖估计得分"),
        ("只靠 v73 折算得分", "只靠 v73 过程覆盖估计得分"),
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
    postprocess_v73()


if __name__ == "__main__":
    main()
