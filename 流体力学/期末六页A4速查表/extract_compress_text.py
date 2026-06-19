with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
out = []
for idx in range(4510, 4545):
    out.append(f"{idx+1}: {lines[idx]}")

with open("extracted_compress_clean.txt", "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(out))
print("Saved clean text!")
