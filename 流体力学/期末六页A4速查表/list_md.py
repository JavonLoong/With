import os

dir_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表"
for f in os.listdir(dir_path):
    if f.endswith('.md'):
         print(f)
