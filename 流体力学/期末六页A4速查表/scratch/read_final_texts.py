import os

files = [
    ("流力期末两张纸_cl.txt", "final_cl_content.txt"),
    ("流力期末参考纸.txt", "final_ref_content.txt")
]

for src_name, dst_name in files:
    src_path = os.path.join(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_text", src_name)
    dst_path = os.path.join(r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch", dst_name)
    if os.path.exists(src_path):
        with open(src_path, 'r', encoding='utf-8') as f:
            text = f.read()
        with open(dst_path, 'w', encoding='utf-8') as f_out:
            f_out.write(text)
        print(f"Successfully wrote {src_name} to {dst_name}")
    else:
        print(f"File not found: {src_path}")
