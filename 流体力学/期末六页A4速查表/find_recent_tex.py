import os
import glob
import time

tex_files = glob.glob("期末六页A4速查表*.tex")
tex_files.sort(key=os.path.getmtime, reverse=True)

for tf in tex_files:
    mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(tf)))
    print(f"{mtime} - {tf} - {os.path.getsize(tf)} bytes")
