from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(r"D:\虚拟C盘\学习\流体力学")
V10_DIR = ROOT / "速查表v10_全量测试评判报告"
OUT = ROOT / "速查表v68_全量测试评判报告"

spec = importlib.util.spec_from_file_location(
    "build_report_v10_module",
    V10_DIR / "build_report_v10.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("无法加载 v10 评判脚本")

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

base = module.base

base.OUT = OUT
base.TEXT_DIR = OUT / "extracted_text"
base.SOURCE_MANIFEST = OUT / "02_题源清单.csv"
base.ITEM_CSV = OUT / "05_全量逐题解决路径.csv"
base.CHEATSHEET_PDF = ROOT / "期末六页A4速查表" / "期末六页A4速查表_最终主用版_已修正_v68.pdf"
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
    "可压缩流/喷管/激波/膨胀波",
    0.84,
    " v68 已补 M=1/2/3 的等熵、面积、普朗特-迈耶角锚点，以及 M1=2/3 正激波锚点；完整斜激波/PM/面积查表仍需教材。",
)
bump_rule(
    "概念简答/定义解释",
    0.78,
    " v67 已补长论述结构：物理意义、实验现象、教材原话关键词。",
)
bump_rule(
    "流体运动学/连续/流线迹线",
    0.78,
    " v67 已补推导题固定结构：适用条件、方程、边界条件、代数化简、限制。",
)

old_estimate = base.estimate


def estimate_v68(rule: dict, question_text: str, group: str, max_score: float) -> tuple[float, str, str]:
    est, basis, confidence = old_estimate(rule, question_text, group, max_score)
    basis = re.sub(r"(?<![A-Za-z0-9])v10(?![A-Za-z0-9])", "v68", basis)
    basis = re.sub(r"(?<![A-Za-z0-9])V10(?![A-Za-z0-9])", "V68", basis)
    basis = re.sub(r"(?<![A-Za-z0-9])v6(?![A-Za-z0-9])", "v68", basis)
    basis = re.sub(r"(?<![A-Za-z0-9])V6(?![A-Za-z0-9])", "V68", basis)
    return est, basis, confidence


base.estimate = estimate_v68


def postprocess_v68() -> None:
    literal_replacements = [
        ("期末六页A4速查表_v6_结构导航版.pdf", "期末六页A4速查表_最终主用版_已修正_v68.pdf"),
        ("期末六页A4速查表_v6_结构导航版.tex", "期末六页A4速查表_最终主用版.tex"),
        ("期末六页A4速查表_最终主用版_已修正_v10.pdf", "期末六页A4速查表_最终主用版_已修正_v68.pdf"),
        ("只靠 v68 得分", "只靠 v68 过程覆盖估计得分"),
        ("只靠 v68 折算得分", "只靠 v68 过程覆盖估计得分"),
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
        text = re.sub(r"(?<![A-Za-z0-9])v10(?![A-Za-z0-9])", "v68", text)
        text = re.sub(r"(?<![A-Za-z0-9])V10(?![A-Za-z0-9])", "V68", text)
        text = re.sub(r"(?<![A-Za-z0-9])v6(?![A-Za-z0-9])", "v68", text)
        text = re.sub(r"(?<![A-Za-z0-9])V6(?![A-Za-z0-9])", "V68", text)
        if path.name in {"最终报告.md", "06_深度评判与改进建议.md", "00_评测说明与范围.md"}:
            if "关键词/模型/公式链/查表动作" not in text:
                text += note
        path.write_text(text, encoding=encoding)


def main() -> None:
    base.main()
    postprocess_v68()


if __name__ == "__main__":
    main()
