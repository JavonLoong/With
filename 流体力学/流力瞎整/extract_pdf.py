import pdfplumber
import sys
sys.stdout.reconfigure(encoding='utf-8')

pdf = pdfplumber.open(r'd:\虚拟C盘\流体力学\第3章 流体运动学基础-2-2025.pdf')
for i in range(len(pdf.pages)):
    p = pdf.pages[i]
    t = p.extract_text()
    print(f'=== 第{i+1}页 ===')
    if t:
        print(t)
    print()
