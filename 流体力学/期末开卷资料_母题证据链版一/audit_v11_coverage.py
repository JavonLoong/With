from pathlib import Path
import csv
import json
import re


outdir = Path.cwd()
root = outdir.parent
files = {
    "v106": root / "期末六页A4速查表" / "期末六页A4速查表_v106_严格母题子题六页版.tex",
    "v108": root / "期末六页A4速查表" / "期末六页A4速查表_v108_母题层级强化版.tex",
    "complete_original": root / "全目录题目归类_重整版一" / "母题子题精选结构_完整原题版一.md",
    "v11": outdir / "期末开卷资料_母题证据链版十一_旧版材料归位补强稿.tex",
}


def read(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def clean_latex(s: str) -> str:
    s = re.sub(r"%.*", "", s)
    s = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}$\\_^&~]", " ", s)
    return re.sub(r"\s+", " ", s)


def extract_items(name: str, text: str):
    items = []
    if name == "complete_original":
        for i, line in enumerate(text.splitlines(), 1):
            m = re.match(r"^(#{1,3})\s*(.+)", line.strip())
            if m:
                title = m.group(2).strip()
                if any(k in title for k in ["母题", "真题", "子题", "变式"]):
                    items.append({"source": name, "line": i, "kind": m.group(1), "title": title})
    else:
        pats = [
            r"\\chap\{([^{}]+)\}",
            r"\\mt\{([^{}]+)\}",
            r"\\sect\{([^{}]+)\}",
            r"\\qt\{([^{}]+)\}",
            r"\\realq\{([^{}]+)\}",
            r"\\subt\{([^{}]+)\}",
            r"\\real\{([^{}]+)\}",
        ]
        for i, line in enumerate(text.splitlines(), 1):
            for pat in pats:
                for m in re.finditer(pat, line):
                    title = m.group(1).strip()
                    if title:
                        items.append({"source": name, "line": i, "kind": pat, "title": title})
    return items


texts = {k: read(p) for k, p in files.items()}
v11_text = texts["v11"]
v11_plain = clean_latex(v11_text)

items = []
for source in ("v106", "v108", "complete_original"):
    items.extend(extract_items(source, texts[source]))

must_terms = [
    "普通池底放水", "虹吸", "泵安装高度", "汽蚀", "水轮机", "并联", "串联", "突扩", "孔板", "文丘里", "液面随时间",
    "平面闸门", "倾斜闸门", "曲面受压", "浮体稳定", "U 管", "多管测压计", "圆柱体", "真空吸水",
    "喷嘴", "法兰", "弯管", "支座力", "射流", "运动叶片", "烟囱", "U 型管", "振荡",
    "点源", "点汇", "点涡", "偶极子", "镜像", "Rankine", "圆柱绕流", "环量", "机翼", "半圆柱", "气膜馆", "达朗贝尔", "Kutta",
    "Laval", "拉伐尔", "阻塞", "背压", "面积", "马赫", "正激波", "斜激波", "PM", "Prandtl", "Meyer", "Fanno", "等熵", "质量流量",
    "Couette", "Poiseuille", "Hagen", "Stokes", "两层", "倾斜平板", "充分发展", "壁面律", "摩擦速度", "N-S",
    "边界层", "平板", "阻力危机", "气球", "沉降", "位移厚度", "动量厚度", "Von Karman", "转捩",
    "应力张量", "速度场", "不可压", "无旋", "势函数", "流函数", "散度", "旋度", "速度环量",
    "量纲", "Buckingham", "模型", "相似", "Re", "Fr", "Ma", "水击", "浅水波", "明渠",
    "RANS", "LES", "DNS", "连续介质", "Bernoulli", "流线", "迹线", "脉线", "非定常",
]

term_rows = []
for term in must_terms:
    sources = [k for k in ("v106", "v108", "complete_original") if term in texts[k]]
    if sources:
        term_rows.append({"term": term, "in_sources": "+".join(sources), "in_v11": term in v11_plain or term in v11_text})

rows = []
for item in items:
    title = item["title"]
    if any(bad in title for bad in ["页间导航", "四件套", "标准答案四行", "高频易错", "导航"]):
        continue
    tokens = [t for t in re.split(r"[：:，,、/（）()\s$\\^_{}\-\[\]0-9.]+", title) if len(t) >= 2]
    hits = [t for t in tokens if t in v11_text]
    rows.append({
        **item,
        "tokens": "|".join(tokens[:10]),
        "hit_count": len(hits),
        "hits": "|".join(hits[:8]),
        "covered": len(hits) > 0,
    })

out_csv = outdir / "v11_旧版材料覆盖审计.csv"
with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["source", "line", "kind", "title", "tokens", "hit_count", "hits", "covered"])
    writer.writeheader()
    writer.writerows(rows)

out_terms = outdir / "v11_关键题型词覆盖审计.csv"
with out_terms.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["term", "in_sources", "in_v11"])
    writer.writeheader()
    writer.writerows(term_rows)

missing_terms = [r for r in term_rows if not r["in_v11"]]
low = [r for r in rows if not r["covered"]]
md = outdir / "v11_旧版材料覆盖审计.md"
md.write_text(
    "\n".join([
        "# v11 旧版材料覆盖审计",
        "",
        "- 审计源：v106、v108、完整原题版一。",
        f"- 标题/小题项总数：{len(rows)}；粗略未命中项：{len(low)}。",
        f"- 关键题型词总数：{len(term_rows)}；未在 v11 明确出现：{len(missing_terms)}。",
        "",
        "## 关键题型词未覆盖",
        *[f"- {r['term']}（来源：{r['in_sources']}）" for r in missing_terms[:80]],
        "",
        "## 标题未粗略命中 Top",
        *[f"- [{r['source']}:{r['line']}] {r['title']}" for r in low[:120]],
    ]),
    encoding="utf-8",
)

print(json.dumps({
    "rows": len(rows),
    "low": len(low),
    "terms": len(term_rows),
    "missing_terms": len(missing_terms),
    "csv": str(out_csv),
    "term_csv": str(out_terms),
    "md": str(md),
}, ensure_ascii=False, indent=2))
