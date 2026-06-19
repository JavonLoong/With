import re

filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = r'从吸水池水面到泵入口列能量，不含泵项：\fml{0+0+z_0=p_B/(\rho g)+V^2/(2g)+z_B+h_f+\sum h_\zeta}。约束$p_B\ge p_v+\Delta p_{\rm safe}$，越高越危险。顺序：$Q\to V\to Re,\varepsilon/d\to\lambda\to h_{\max}$。'

# Let's escape the regex characters in target
escaped_target = re.escape(target)

new_text = r"""从吸水池水面至泵入口列能量（无泵）：
\fmlb{0+0+z_0=\frac{p_B}{\rho g}+\frac{V^2}{2g}+z_B+h_f+\sum h_\zeta}
约束 $p_B\ge p_v+\Delta p_{\rm safe}$，越高越危险。\\
顺序：$Q\to V\to Re,\varepsilon/d\to\lambda\to h_{\max}$。"""

if target in content:
    content = content.replace(target, new_text)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully replaced pump suction height formatting in root file!")
else:
    print("Target string not found in file!")
