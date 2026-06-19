import os
import zipfile

review_dir = r'd:\虚拟C盘\学习\流体力学\复习'
names = ['流力总结（1）.docx', '流力总结（2）.docx', '流力考点预测.docx']

for name in names:
    path = os.path.join(review_dir, name)
    if os.path.exists(path):
        with zipfile.ZipFile(path) as zf:
            infolist = zf.infolist()
            print(f"{name}: total entries = {len(infolist)}")
            media_count = sum(1 for info in infolist if 'word/media/' in info.filename)
            xml_size = sum(info.file_size for info in infolist if 'word/document.xml' in info.filename)
            print(f"  media files count = {media_count}")
            print(f"  document.xml size = {xml_size} bytes")
