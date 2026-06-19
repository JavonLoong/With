import os
import zipfile
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

review_dir = r'd:\虚拟C盘\学习\流体力学\复习'
docx_files = [
    '流力考点预测.docx',
    '流力总结（1）.docx',
    '流力总结（2）.docx',
    '流体力学.docx',
    '考试范围.docx'
]

def get_docx_text(path):
    try:
        with zipfile.ZipFile(path) as zf:
            xml_content = zf.read('word/document.xml')
            root = ET.fromstring(xml_content)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs = []
            for p in root.findall('.//w:p', ns):
                texts = [t.text for t in p.findall('.//w:t', ns) if t.text]
                if texts:
                    paragraphs.append(''.join(texts))
            return '\n'.join(paragraphs)
    except Exception as e:
        return f"Error reading {path}: {str(e)}"

# Keywords to search
keywords = ['正确的是', '错误的是', '不正确的是', '说法正确', '说法错误', '思考题', '选择', '判断', '简答', '考点']

for name in docx_files:
    path = os.path.join(review_dir, name)
    if not os.path.exists(path):
        continue
    print(f"\n=================== Searching in {name} ===================")
    text = get_docx_text(path)
    lines = text.split('\n')
    matches = []
    for line in lines:
        for kw in keywords:
            if kw in line:
                matches.append(line)
                break
    print(f"Found {len(matches)} matching lines. Showing first 30:")
    for m in matches[:30]:
        try:
            print(f" - {m[:120]}")
        except Exception:
            print(f" - [Encoding error in line of length {len(m)}]")
