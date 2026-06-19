import filecmp
file1 = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
file2 = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex'
if filecmp.cmp(file1, file2, shallow=False):
    print("Files are identical!")
else:
    print("Files are different!")
