import os

dir_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表"
for f in os.listdir(dir_path):
    if '证据' in f or '对照' in f or '版一' in f:
        print(f"File name: {f}")
