import os

extracted_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip"
out_file = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\filenames.txt"

with open(out_file, 'w', encoding='utf-8') as out:
    for root, dirs, files in os.walk(extracted_path):
        for f in files:
            full_path = os.path.join(root, f)
            rel = os.path.relpath(full_path, extracted_path)
            out.write(f"File: {rel}\n")
            
print("Wrote filenames to scratch/filenames.txt")
