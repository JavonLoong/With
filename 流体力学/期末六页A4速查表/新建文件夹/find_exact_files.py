import os

workspace_dir = r'd:\虚拟C盘\学习'
found_files = []

for root, dirs, files in os.walk(workspace_dir):
    for f in files:
        if '对照' in f or '证据链' in f:
            found_files.append(os.path.join(root, f))

with open('found_files.txt', 'w', encoding='utf-8') as out:
    for f in found_files:
        out.write(f + '\n')
