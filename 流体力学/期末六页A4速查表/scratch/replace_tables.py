import os

filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    r'\begin{tabular}{|p{0.30\linewidth}|p{0.62\linewidth}|}': r'\begin{tabular}{|>{\centering\arraybackslash}p{0.30\linewidth}|>{\centering\arraybackslash}p{0.62\linewidth}|}',
    r'\begin{tabular}{|p{0.42\linewidth}|p{0.52\linewidth}|}': r'\begin{tabular}{|>{\centering\arraybackslash}p{0.42\linewidth}|>{\centering\arraybackslash}p{0.52\linewidth}|}',
    r'\begin{tabular}{|p{0.21\linewidth}|p{0.70\linewidth}|}': r'\begin{tabular}{|>{\centering\arraybackslash}p{0.21\linewidth}|>{\centering\arraybackslash}p{0.70\linewidth}|}',
    r'\begin{tabular}{|p{0.30\linewidth}|p{0.61\linewidth}|}': r'\begin{tabular}{|>{\centering\arraybackslash}p{0.30\linewidth}|>{\centering\arraybackslash}p{0.61\linewidth}|}',
    r'\begin{tabular}{|p{0.29\linewidth}|p{0.29\linewidth}|p{0.34\linewidth}|}': r'\begin{tabular}{|>{\centering\arraybackslash}p{0.29\linewidth}|>{\centering\arraybackslash}p{0.29\linewidth}|>{\centering\arraybackslash}p{0.34\linewidth}|}',
    r'\begin{tabular}{|p{0.31\linewidth}|p{0.28\linewidth}|p{0.33\linewidth}|}': r'\begin{tabular}{|>{\centering\arraybackslash}p{0.31\linewidth}|>{\centering\arraybackslash}p{0.28\linewidth}|>{\centering\arraybackslash}p{0.33\linewidth}|}',
    r'\begin{tabular}{|p{0.27\linewidth}|p{0.66\linewidth}|}': r'\begin{tabular}{|>{\centering\arraybackslash}p{0.27\linewidth}|>{\centering\arraybackslash}p{0.66\linewidth}|}',
    r'\begin{tabular}{|p{0.28\linewidth}|p{0.66\linewidth}|}': r'\begin{tabular}{|>{\centering\arraybackslash}p{0.28\linewidth}|>{\centering\arraybackslash}p{0.66\linewidth}|}'
}

count = 0
for target, replacement in replacements.items():
    if target in content:
        content = content.replace(target, replacement)
        print(f"Replaced: {target}")
        count += 1
    else:
        print(f"Not found: {target}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Finished. Replaced {count} tables.")
