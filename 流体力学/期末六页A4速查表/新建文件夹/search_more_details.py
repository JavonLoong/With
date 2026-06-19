import os

folder = r'd:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一'
tex_files = [f for f in os.listdir(folder) if f.endswith('.tex')]

query = '离心泵吸水管'
query2 = '水轮机'

for f in tex_files:
    path = os.path.join(folder, f)
    with open(path, 'rb') as file_obj:
        content = file_obj.read().decode('utf-8', errors='ignore')
    
    if query in content or query2 in content:
        # Print where it occurs
        for line in content.split('\n'):
            if query in line or '最大安装高度' in line or '水轮机管路' in line:
                # print file name and line
                print(f"File: {f} | Line: {line[:100]}")
