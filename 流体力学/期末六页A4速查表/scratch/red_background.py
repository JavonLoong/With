import os

paths = [
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex',
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex'
]

# 1. Define new color and macros
def add_macros(content):
    target = r'\definecolor{subbg}{HTML}{B9D7FF}'
    replacement = (
        r'\definecolor{subbg}{HTML}{B9D7FF}' + '\n' +
        r'\definecolor{redbg}{HTML}{FFEBEE}' + '\n' +
        r'\newcommand{\redinfotxt}[1]{\colorbox{redbg}{\begin{minipage}{\dimexpr\linewidth-2\fboxsep\relax}\fontsize{4.82}{5.02}\selectfont #1\end{minipage}}\par\vspace{0.10pt}}' + '\n' +
        r'\newcommand{\fmlbred}[1]{\par\noindent\colorbox{redbg}{\begin{minipage}{\dimexpr\linewidth-2\fboxsep\relax}\centering\fontsize{5.12}{5.42}\selectfont\ensuremath{\displaystyle #1}\end{minipage}}\par\vspace{0.10pt}}'
    )
    if replacement in content:
        return content
    return content.replace(target, replacement)

# 2. Restructure boundary layer and momentum thickness block
# 3. Highlight flow separation block
def restructure_content(content):
    # Target 1: Von Karman formulas inside green block
    target_block = (
        r'\text{阻力：}&\quad D=\bar C_f\frac12\rho U^2A,\qquad P=DU' + '\n' +
        r'\end{aligned}}' + '\n' +
        r'' + '\n' +
        r'\formq{位移/动量厚度/Von Karman}' + '\n' +
        r'\fmlb{\color{warnc}\begin{aligned}' + '\n' +
        r'\delta^*&=\int_0^\delta(1-u/U)\,dy\\' + '\n' +
        r'\theta&=\int_0^\delta(u/U)(1-u/U)\,dy' + '\n' +
        r'\end{aligned}}' + '\n' +
        r'\fmlb{\color{warnc}\begin{aligned}' + '\n' +
        r'\frac{\tau_w}{\rho U^2}&=\frac{d\theta}{dx}\qquad(dp/dx=0)\\' + '\n' +
        r'\frac{\tau_w}{\rho U^2}&=\frac{d\theta}{dx}' + '\n' +
        r'+\frac{2\theta+\delta^*}{U}\frac{dU}{dx}' + '\n' +
        r'\end{aligned}}' + '\n' +
        r'给$u/U=f(\eta),\eta=y/\delta$：把$dy=\delta d\eta$代入积分。' + '\n' +
        r'\stepq{常见剖面直接用}' + '\n' +
        r'\fmlb{\begin{array}{c|c|c}' + '\n' +
        r'u/U & \delta^* & \theta\\ \hline' + '\n' +
        r'\eta & \delta/2 & \delta/6\\' + '\n' +
        r'2\eta-\eta^2 & \delta/3 & 2\delta/15' + '\n' +
        r'\end{array}}' + '\n' +
        r'若题给幂律$u/U=\eta^{1/n}$，先代$\eta$积分，不要展开成$y$。' + '\n' +
        r'' + '\n' +
        r'}'
    )
    
    replacement_block = (
        r'\text{阻力：}&\quad D=\bar C_f\frac12\rho U^2A,\qquad P=DU' + '\n' +
        r'\end{aligned}}' + '\n' +
        r'}' + '\n' +
        r'\infoh{位移/动量厚度/Von Karman}' + '\n' +
        r'\redinfotxt{%' + '\n' +
        r'\fmlbred{\begin{aligned}' + '\n' +
        r'\delta^*&=\int_0^\delta(1-u/U)\,dy\\' + '\n' +
        r'\theta&=\int_0^\delta(u/U)(1-u/U)\,dy' + '\n' +
        r'\end{aligned}}' + '\n' +
        r'\fmlbred{\begin{aligned}' + '\n' +
        r'\frac{\tau_w}{\rho U^2}&=\frac{d\theta}{dx}\qquad(dp/dx=0)\\' + '\n' +
        r'\frac{\tau_w}{\rho U^2}&=\frac{d\theta}{dx}' + '\n' +
        r'+\frac{2\theta+\delta^*}{U}\frac{dU}{dx}' + '\n' +
        r'\end{aligned}}' + '\n' +
        r'给$u/U=f(\eta),\eta=y/\delta$：把$dy=\delta d\eta$代入积分。' + '\n' +
        r'\stepq{常见剖面直接用}' + '\n' +
        r'\fmlbred{\begin{array}{c|c|c}' + '\n' +
        r'u/U & \delta^* & \theta\\ \hline' + '\n' +
        r'\eta & \delta/2 & \delta/6\\' + '\n' +
        r'2\eta-\eta^2 & \delta/3 & 2\delta/15' + '\n' +
        r'\end{array}}' + '\n' +
        r'若题给幂律$u/U=\eta^{1/n}$，先代$\eta$积分，不要展开成$y$。' + '\n' +
        r'}'
    )
    
    # Target 2: Flow separation conditions
    target_separation = (
        r'\stepq{分离与阻力}' + '\n' +
        r'\warn{必要条件：逆压梯度$dp/dx>0$（或速度减小）；充分条件（分离判据）：壁面剪力$\tau_w=0$（即$\partial u/\partial y|_w=0$）。}摩擦阻力来自$\tau_w$；压差阻力来自分离尾流。'
    )
    
    replacement_separation = (
        r'\redinfotxt{%' + '\n' +
        r'\stepq{分离与阻力}' + '\n' +
        r'\warn{必要条件：逆压梯度$dp/dx>0$（或速度减小）；充分条件（分离判据）：壁面剪力$\tau_w=0$（即$\partial u/\partial y|_w=0$）。}摩擦阻力来自$\tau_w$；压差阻力来分尾流。' + '\n' +
        r'}'
    )
    
    content = content.replace(target_block, replacement_block)
    content = content.replace(target_separation, replacement_separation)
    return content

for path in paths:
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    
    c = add_macros(c)
    c = restructure_content(c)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print(f"Processed file: {os.path.basename(path)}")
