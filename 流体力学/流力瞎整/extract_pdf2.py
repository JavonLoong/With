import fitz
import sys
sys.stdout.reconfigure(encoding='utf-8')

pdf = fitz.open(r'd:\虚拟C盘\流体力学\第3章 流体运动学基础-2-2025.pdf')
print(f'共{len(pdf)}页')
for i, page in enumerate(pdf):
    text = page.get_text()
    print(f'=== 第{i+1}页 ===')
    print(text)
    print()
