import os

for f in os.listdir(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表"):
    if f.startswith('page_new'):
        print(f)
