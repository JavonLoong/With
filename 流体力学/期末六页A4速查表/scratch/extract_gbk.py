import zipfile
import os

zip_path = r"d:\虚拟C盘\新建文件夹 (3)\几页纸（带考场）.zip"
dest_dir = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip"

# Clean destination directory first
import shutil
if os.path.exists(dest_dir):
    shutil.rmtree(dest_dir)
os.makedirs(dest_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    for info in zip_ref.infolist():
        # Get the filename bytes
        filename_bytes = info.filename.encode('cp437') # Zipfile library decodes to cp437 string by default, we encode back to get raw bytes.
        try:
            filename = filename_bytes.decode('gbk')
        except Exception:
            try:
                filename = filename_bytes.decode('utf-8')
            except Exception:
                filename = info.filename
        
        # Output directory path
        out_path = os.path.join(dest_dir, filename)
        # Create directories if needed
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        # Extract the file
        if not info.is_dir():
            with zip_ref.open(info) as source, open(out_path, 'wb') as target:
                shutil.copyfileobj(source, target)
            print(f"Extracted: {filename}")
