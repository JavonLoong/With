import zipfile
import os

zip_path = r"d:\虚拟C盘\新建文件夹 (3)\几页纸（带考场）.zip"
dest_dir = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip"

os.makedirs(dest_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    # Let's print the list of files first to see what's inside without extracting everything if there are too many files.
    file_list = zip_ref.namelist()
    print(f"Total files in zip: {len(file_list)}")
    print("First 30 files in zip:")
    for f in file_list[:30]:
        print(f)
        
    # Now let's extract them
    zip_ref.extractall(dest_dir)
    print("Extraction complete!")
