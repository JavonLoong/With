import os

paths = [
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex',
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex'
]

targets = {
    # 1. Mother topic 5 overview (yellow box)
    r'检查：充分发展、层流才用H--P、速度剖面与平均速度别混。}':
        r'检查：充分发展、层流才用H--P、速度剖面与平均速度别混。\warn{【别找错：平板边界层/位移/动量厚度/流动分离去第5页母题6红色区！】}}',
        
    # 2. Viscous flow info D易错检查 (green box)
    r'\infoh{粘性管流信息库D 易错检查}' + '\n' + r'\infotxt{%' + '\n' + r'不要把$\mu$和$\nu$混用；':
        r'\infoh{粘性管流信息库D 易错检查}' + '\n' + r'\infotxt{%' + '\n' + r'\warn{【防错导航】若是平板、边界层、位移/动量厚度、流动分离，立刻前往第5页母题六（红色背景区）！}\\' + '\n' + r'不要把$\mu$和$\nu$混用；'
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
            print(f"Successfully added navigation warning to {os.path.basename(path)}")
        elif count == 0:
            if replacement in modified:
                print(f"Navigation warning already present in {os.path.basename(path)}")
            else:
                print(f"Error: Target not found in {os.path.basename(path)}")
        else:
            print(f"Error: Target found multiple times in {os.path.basename(path)}")
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write(modified)

print("Navigation warning script completed!")
