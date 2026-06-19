import os

parent_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex"
subdir_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex"

print("Parent size:", os.path.getsize(parent_path))
print("Subdir size:", os.path.getsize(subdir_path))

with open(parent_path, 'r', encoding='utf-8', errors='ignore') as f:
    parent_content = f.read()

with open(subdir_path, 'r', encoding='utf-8', errors='ignore') as f:
    subdir_content = f.read()

print("Is subdir content inside parent?", subdir_content[:1000] in parent_content)
# Find some differences or headers
print("Parent lines:", len(parent_content.splitlines()))
print("Subdir lines:", len(subdir_content.splitlines()))
