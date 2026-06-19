import os

extracted_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip"
# Let's walk the directory and print all files
for root, dirs, files in os.walk(extracted_path):
    for f in files:
        full_path = os.path.join(root, f)
        print(f"File: {os.path.relpath(full_path, extracted_path)} - Size: {os.path.getsize(full_path)} bytes")
