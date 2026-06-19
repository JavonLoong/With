import os
import fitz

extracted_dir = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip"
pdf_files = []
for root, dirs, files in os.walk(extracted_dir):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(root, f))

for pdf_path in pdf_files:
    try:
        doc = fitz.open(pdf_path)
        print(f"File: {os.path.basename(pdf_path)} - Pages: {len(doc)}")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
