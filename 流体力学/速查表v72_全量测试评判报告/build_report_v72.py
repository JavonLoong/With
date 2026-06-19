from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
V71_DIR = ROOT / "速查表v71_全量测试评判报告"
OUT = ROOT / "速查表v72_全量测试评判报告"

spec = importlib.util.spec_from_file_location(
    "build_report_v71_module",
    V71_DIR / "build_report_v71.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("无法加载 v71 评判脚本")

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
base = module.base

base.OUT = OUT
base.TEXT_DIR = OUT / "extracted_text"
base.SOURCE_MANIFEST = OUT / "02_题源清单.csv"
base.ITEM_CSV = OUT / "05_全量逐题解决路径.csv"
base.CHEATSHEET_PDF = ROOT / "期末六页A4速查表" / "期末六页A4速查表_最终主用版_已修正_v72.pdf"
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
    "边界层/外绕流阻力",
    0.80,
    " v72 已补局部摩阻系数 cf、单位宽阻力 D'、CD=2theta/L、转捩位置 xcr、平板层/湍/混合阻力判定和湿表面积/迎风面积区分；复杂分离与实验阻力图仍需教材。",
)

old_estimate = base.estimate


def replace_version(text: str) -> str:
    for old in ["v10", "v6", "v70", "v71"]:
        text = re.sub(rf"(?<![A-Za-z0-9]){old}(?![A-Za-z0-9])", "v72", text)
        text = re.sub(rf"(?<![A-Za-z0-9]){old.upper()}(?![A-Za-z0-9])", "V72", text)
    return text


def estimate_v72(rule: dict, question_text: str, group: str, max_score: float) -> tuple[float, str, str]:
    est, basis, confidence = old_estimate(rule, question_text, group, max_score)
    return est, replace_version(basis), confidence


base.estimate = estimate_v72


def postprocess_v72() -> None:
    literal_replacements = [
        ("期末六页A4速查表_v6_结构导航版.pdf", "期末六页A4速查表_最终主用版_已修正_v72.pdf"),
        ("期末六页A4速查表_v6_结构导航版.tex", "期末六页A4速查表_最终主用版.tex"),
        ("期末六页A4速查表_最终主用版_已修正_v10.pdf", "期末六页A4速查表_最终主用版_已修正_v72.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v70.pdf", "期末六页A4速查表_最终主用版_已修正_v72.pdf"),
        ("期末六页A4速查表_最终主用版_已修正_v71.pdf", "期末六页A4速查表_最终主用版_已修正_v72.pdf"),
        ("只靠 v72 得分", "只靠 v72 过程覆盖估计得分"),
        ("只靠 v72 折算得分", "只靠 v72 过程覆盖估计得分"),
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
    postprocess_v72()


if __name__ == "__main__":
    main()
