import os

workspace = r"d:\虚拟C盘\学习"
for root, dirs, files in os.walk(workspace):
    for f in files:
        if '覆盖' in f or '对照' in f:
            print(os.path.join(root, f))
