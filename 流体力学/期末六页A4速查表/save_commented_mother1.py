with open(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex", 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
commented = lines[381:887] # lines 382 to 887 (0-indexed 381 to 886)
with open("mother1_commented.txt", "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(commented))

print(f"Saved {len(commented)} lines to mother1_commented.txt")
