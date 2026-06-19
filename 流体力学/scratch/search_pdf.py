import os
import sys

# Configure standard output to use utf-8
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r'd:\虚拟C盘\学习\流体力学\复习\流体力学期末背诵提纲超级完整版.pdf'

# Try different pdf libraries
try:
    import pypdf
    print("Using pypdf")
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
except ImportError:
    try:
        import pdfplumber
        print("Using pdfplumber")
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
    except ImportError:
        try:
            import fitz # PyMuPDF
            print("Using PyMuPDF")
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
        except ImportError:
            print("No PDF library installed")
            text = None

if text:
    keywords = ['选择', '判断', '说法正确', '条件是', '激波', '低雷诺数', '势函数', '连续性方程', '转捩', '分界线', '雷诺数', '压强']
    lines = text.split('\n')
    matches = []
    for line in lines:
        for kw in keywords:
            if kw in line:
                matches.append(line)
                break
    print(f"Found {len(matches)} matching lines. Showing first 40:")
    for m in matches[:40]:
        try:
            print(f" - {m[:120]}")
        except Exception:
            print(" - [Encoding error]")
else:
    print("Failed to extract text from PDF")
