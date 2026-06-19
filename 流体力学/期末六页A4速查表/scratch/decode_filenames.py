import os
import sys

extracted_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip"
subfolder = os.listdir(extracted_path)[0]
subfolder_path = os.path.join(extracted_path, subfolder)
print(f"Subfolder: {subfolder.encode('utf-8', errors='replace')}")

for f in os.listdir(subfolder_path):
    print(f.encode('utf-8', errors='replace').decode('utf-8'))
