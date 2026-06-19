import os

subfolder_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip\几页纸"
if not os.path.exists(subfolder_path):
    # Let's find the actual subfolder name
    parent = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip"
    subfolder = os.listdir(parent)[0]
    subfolder_path = os.path.join(parent, subfolder)

print(f"Walking folder: {subfolder_path}")
for f in os.listdir(subfolder_path):
    # Try to decode the filename
    # Zipfile decodes raw bytes of filenames using cp437 if the utf-8 flag is not set.
    # To recover the original bytes, we encode back to cp437, then decode using gbk.
    try:
        raw_bytes = f.encode('cp437')
        correct_name = raw_bytes.decode('gbk')
    except Exception as e:
        # If that fails, try utf-8 or keep as is
        correct_name = f
        
    print(f"Original: {f} -> Decoded: {correct_name}")
    # Rename the file if the decoded name is different and valid
    if correct_name != f:
        src = os.path.join(subfolder_path, f)
        dst = os.path.join(subfolder_path, correct_name)
        os.rename(src, dst)

print("Renaming check complete!")
