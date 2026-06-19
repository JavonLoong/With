import os
from datetime import datetime

dir_path = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表"
files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith('.tex') or f.endswith('.pdf')]
files.sort(key=os.path.getmtime, reverse=True)

with open('recent_tex_pdf.txt', 'w', encoding='utf-8') as f_out:
    for f in files[:30]:
        mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d %H:%M:%S')
        name = os.path.basename(f)
        f_out.write(f"{mtime} - {name} - {os.path.getsize(f)} bytes\n")
print("Done")
