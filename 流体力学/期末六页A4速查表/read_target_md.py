import os

dir_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表"
target_file = None
for f in os.listdir(dir_path):
    if '证据' in f and '对照' in f:
        target_file = os.path.join(dir_path, f)
        break

if target_file:
    print("Found file:", target_file)
    with open(target_file, 'r', encoding='utf-8') as f_in:
        content = f_in.read()
    with open('view_coverage_utf8.txt', 'w', encoding='utf-8') as f_out:
        f_out.write(content)
else:
    print("Not found")
