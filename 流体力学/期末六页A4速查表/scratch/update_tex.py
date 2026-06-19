import os

paths = [
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex',
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex'
]

targets = {
    # 2. 3D Potential flow (insert after the potential flow table uniquely)
    r'偶极 & $M\cos\theta/r$ & $-M\sin\theta/r$\\ \hline' + '\n' + r'\end{tabular}\par}\renewcommand{\arraystretch}{1}': 
        r'偶极 & $M\cos\theta/r$ & $-M\sin\theta/r$\\ \hline' + '\n' + \
        r'\end{tabular}\par}\renewcommand{\arraystretch}{1}' + '\n' + \
        r'\conceptq{三维基元势流}三维点源：$\phi=-\frac{Q}{4\pi r}$，速度$v_r=\frac{Q}{4\pi r^2}$。三维偶极子：$\phi=\frac{m\cos\theta}{4\pi r^2}$，速度$v_r=-\frac{m\cos\theta}{2\pi r^3},v_\theta=-\frac{m\sin\theta}{4\pi r^3}$。\\'
}

for path in paths:
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = content
    
    # Apply targets
    for target, replacement in targets.items():
        count = modified.count(target)
        if count == 1:
            modified = modified.replace(target, replacement)
            print(f"Successfully replaced potential flow table in {os.path.basename(path)}")
        elif count == 0:
            if replacement in modified:
                print(f"Already replaced potential flow table in {os.path.basename(path)}")
            else:
                print(f"Error: Potential flow target not found in {os.path.basename(path)}")
        else:
            print(f"Error: Potential flow target found multiple times ({count}) in {os.path.basename(path)}")
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write(modified)
        
print("TEX update run complete!")
