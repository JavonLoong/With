import os
import fitz

extracted_dir = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_zip"
out_dir = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch\extracted_text"
os.makedirs(out_dir, exist_ok=True)

# Find all PDF files in extracted_dir
pdf_files = []
for root, dirs, files in os.walk(extracted_dir):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(root, f))

print(f"Found {len(pdf_files)} PDF files.")

for pdf_path in pdf_files:
    rel_name = os.path.relpath(pdf_path, extracted_dir)
    print(f"Extracting text from: {rel_name}")
    try:
        doc = fitz.open(pdf_path)
        text_content = []
        for i, page in enumerate(doc):
            text_content.append(f"--- Page {i+1} ---")
            text_content.append(page.get_text())
        
        # Save to text file
        base_name = os.path.basename(pdf_path).replace('.pdf', '.txt')
        out_path = os.path.join(out_dir, base_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(text_content))
        print(f"Saved extracted text to {out_path} (size: {os.path.getsize(out_path)} bytes)")
    except Exception as e:
        print(f"Error extracting from {pdf_path}: {e}")

print("Text extraction complete!")
