import subprocess, sys

git_path = '流体力学/期末六页A4速查表/新建文件夹/期末六页A4速查表_重整版四_公式重排版.tex'
commit = 'aff00fd'
cmd = ['git', 'show', f'{commit}:{git_path}']
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if res.returncode != 0:
    print(f"Error: {res.stderr.decode('utf-8', errors='ignore')}")
    sys.exit(1)

# Try multiple encodings
content = None
for enc in ['utf-8', 'gbk', 'utf-8-sig', 'latin-1']:
    try:
        content = res.stdout.decode(enc)
        break
    except:
        pass

if content is None:
    print("Failed to decode")
    sys.exit(1)

lines = content.splitlines()

# Find Mother Topic 2 section
in_section = False
start_line = None
end_line = None
for i, line in enumerate(lines):
    if '母题2' in line and 'chap' in line:
        in_section = True
        start_line = i
    elif in_section and '母题3' in line and 'chap' in line:
        end_line = i
        break

if start_line is not None and end_line is not None:
    print(f"Mother Topic 2: lines {start_line+1} to {end_line}")
    # Only print the info section A/B/C/D parts  
    for i in range(start_line, min(end_line, start_line + 120)):
        print(f"{i+1}: {lines[i]}")
else:
    print(f"Boundaries: start={start_line}, end={end_line}")
