import os

paths = [
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex',
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex'
]

for path in paths:
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Replace begin{multicols}{3} with begin{multicols*}{3}
    content = content.replace(r'\begin{multicols}{3}', r'\begin{multicols*}{3}')
    
    # 2. Replace end{multicols} with end{multicols*}
    content = content.replace(r'\end{multicols}', r'\end{multicols*}')
    
    # 3. Add \columnbreak before the concept library
    target_concept = r'\infoh{选择与判断题高频概念秒杀库（防坑指南）}'
    if target_concept in content:
        # Check if columnbreak is already there
        if r'\columnbreak' not in content[content.find(target_concept)-50 : content.find(target_concept)]:
            content = content.replace(target_concept, r'\columnbreak' + '\n' + target_concept)
            print(f"Added columnbreak before concept library in {os.path.basename(path)}")
        else:
            print(f"columnbreak already present in {os.path.basename(path)}")
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Updated multicols to multicols* in {os.path.basename(path)}")

print("Multicols* transformation completed!")
