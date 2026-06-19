import os

filepath = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_text\流力期中一张纸_cl.txt"
out_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\mid_cl_content.txt"

if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    with open(out_path, 'w', encoding='utf-8') as f_out:
        f_out.write(text)
    print("Successfully wrote content to scratch/mid_cl_content.txt")
else:
    print("File not found!")
