import os
import zipfile
import xml.etree.ElementTree as ET

path = r'd:\虚拟C盘\学习\流体力学\复习\流体力学.docx'
out_path = r'd:\虚拟C盘\学习\流体力学\scratch\fluid_text.txt'

def get_docx_text(path):
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

text = get_docx_text(path)
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Dumped {len(text)} characters to {out_path}")
