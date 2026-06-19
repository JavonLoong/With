import os

paths = [
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex',
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex'
]

targets = {
    # 1. Displacement and momentum thickness formulas: make the math red
    r'\fmlb{\begin{aligned}' + '\n' + r'\delta^*&=\int_0^\delta(1-u/U)\,dy\\' + '\n' + r'\theta&=\int_0^\delta(u/U)(1-u/U)\,dy' + '\n' + r'\end{aligned}}':
        r'\fmlb{\color{warnc}\begin{aligned}' + '\n' + r'\delta^*&=\int_0^\delta(1-u/U)\,dy\\' + '\n' + r'\theta&=\int_0^\delta(u/U)(1-u/U)\,dy' + '\n' + r'\end{aligned}}',
        
    # 2. Von Karman integral formulas: make the math red
    r'\fmlb{\begin{aligned}' + '\n' + r'\frac{\tau_w}{\rho U^2}&=\frac{d\theta}{dx}\qquad(dp/dx=0)\\' + '\n' + r'\frac{\tau_w}{\rho U^2}&=\frac{d\theta}{dx}' + '\n' + r'+\frac{2\theta+\delta^*}{U}\frac{dU}{dx}' + '\n' + r'\end{aligned}}':
        r'\fmlb{\color{warnc}\begin{aligned}' + '\n' + r'\frac{\tau_w}{\rho U^2}&=\frac{d\theta}{dx}\qquad(dp/dx=0)\\' + '\n' + r'\frac{\tau_w}{\rho U^2}&=\frac{d\theta}{dx}' + '\n' + r'+\frac{2\theta+\delta^*}{U}\frac{dU}{dx}' + '\n' + r'\end{aligned}}',
        
    # 3. Flow separation conditions: make text red and explicit
    r'逆压梯度$dp/dx>0$使边界层减速增厚；$\partial u/\partial y|_w=0$为分离临界。':
        r'\warn{必要条件：逆压梯度$dp/dx>0$（或速度减小）；充分条件（分离判据）：壁面剪力$\tau_w=0$（即$\partial u/\partial y|_w=0$）。}'
}

for path in paths:
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    modified = content
    for target, replacement in targets.items():
        count = modified.count(target)
        if count == 1:
            modified = modified.replace(target, replacement)
            print(f"Successfully highlighted target in {os.path.basename(path)}")
        elif count == 0:
            if replacement in modified:
                print(f"Already highlighted in {os.path.basename(path)}")
            else:
                print(f"Error: Target not found in {os.path.basename(path)}")
        else:
            print(f"Error: Target found multiple times ({count}) in {os.path.basename(path)}")
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write(modified)

print("Highlighting script completed!")
