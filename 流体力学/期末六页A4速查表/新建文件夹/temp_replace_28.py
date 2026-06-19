import re

file_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update the table in Sub-library 2
old_table = r"""3. \key{混淆要点对比表}：\\
\begin{tabular}{p{2.2cm}|c|c} \hline
流动类别 & 流函数 $\psi$ & 势函数 $\phi$ \\ \hline
二维不可压有旋 & 存在 ($\checkmark$) & 不存在 ($\times$) \\
二维不可压无旋 & 存在 ($\checkmark$) & 存在 ($\checkmark$) \\
三维不可压有旋 & 不存在 ($\times$) & 不存在 ($\times$) \\
三维无旋（不论可压与否） & 不存在 ($\times$) & 存在 ($\checkmark$) \\ \hline
\end{tabular} \\"""

new_table = r"""3. \key{混淆要点对比表}：\\
\begin{tabular}{p{2.2cm}|c|c} \hline
流动类别 & 流函数 $\psi$ & 势函数 $\phi$ \\ \hline
二维不可压有旋 & 存在 ($\checkmark$) & 不存在 ($\times$) \\
二维不可压无旋 & 存在 ($\checkmark$) & 存在 ($\checkmark$) \\
三维不可压有旋 & 不存在 ($\times$) & 不存在 ($\times$) \\
三维不可压无旋 & 不存在 ($\times$) & 存在 ($\checkmark$) \\
三维可压无旋 & 不存在 ($\times$) & 存在 ($\checkmark$) \\ \hline
\end{tabular} \\"""

if old_table in content:
    content = content.replace(old_table, new_table)
    print("Table updated successfully")
else:
    print("WARNING: Table not found")

# 2. Update Sub-library 3
old_lib3 = r"""1. \key{声速与马赫数}：\\
{\fontspec{SimSun}①} 声速 $c=\sqrt{\gamma RT}$ 仅是温度的函数。\\
{\fontspec{SimSun}②} 马赫数 $Ma=V/c$ 反映可压缩程度，当 $Ma < 0.3$ 时可近似为不可压缩流动。\\
{\fontspec{SimSun}③} 声波传播极快，\warn{为等熵过程，而非等温过程}。\\"""

new_lib3 = r"""1. \key{声速与马赫数}：\\
{\fontspec{SimSun}①} 声速 $a=\sqrt{\gamma RT}$ 仅是温度的函数。\\
{\fontspec{SimSun}②} 马赫数 $Ma=V/a$ 反映可压缩程度，当 $Ma < 0.3$ 时可近似为不可压缩流动。\\
{\fontspec{SimSun}③} 声波传播极快且温度/压力变化极微小，来不及进行热交换，故可视为无摩擦的绝热过程，即\warn{等熵过程，而非等温过程}。\\"""

if old_lib3 in content:
    content = content.replace(old_lib3, new_lib3)
    print("Sub-library 3 updated successfully")
else:
    print("WARNING: Sub-library 3 not found")

# 3. Update speed of sound in Sub-library 4
old_sub4_c = r"弹性力起主导作用取\warn{马赫数相似 $Ma = V/c$}"
new_sub4_c = r"弹性力起主导作用取\warn{马赫数相似 $Ma = V/a$}"

if old_sub4_c in content:
    content = content.replace(old_sub4_c, new_sub4_c)
    print("Sub-library 4 updated successfully")
else:
    # Let's search for any occurrences of "Ma = V/c" in the file to make sure
    print("WARNING: old_sub4_c not found. Let's do a search.")
    # Actually, in the file it was: "弹性力起主导作用取\warn{马赫数相似 $Ma = V/c$}"
    # Wait, let's check what it was in Sub-library 4 from my previous run:
    # It might not have been in the file because it was in the old Sub-library 4!
    # Ah! In the new Sub-library 4, did it have Ma = V/c? Let's check:
    # "弹性力起主导作用取\warn{马赫数相似 $Ma = V/c$}。"
    # Let's look at temp_replace_24.py:
    # "弹性力起主导作用取\warn{马赫数相似 $Ma = V/c$}。" (Wait, in temp_replace_24.py I wrote $Ma = V/c$)
    # Let's see what is currently in the file.
    # Ah, let's do a replace using regex or simple search.

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Finished updates.")
