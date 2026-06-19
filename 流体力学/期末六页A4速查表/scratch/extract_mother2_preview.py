import subprocess

# The preview PDF was generated around commit aff00fd (2026-06-16 03:13:12)
# Let's check the content at that commit for the subdirectory file
git_path = '流体力学/期末六页A4速查表/新建文件夹/期末六页A4速查表_重整版四_公式重排版.tex'

# Try aff00fd first
commit = 'aff00fd'
cmd = ['git', 'show', f'{commit}:{git_path}']
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if res.returncode != 0:
    print(f"Error: {res.stderr.decode('utf-8', errors='ignore')}")
else:
    content = res.stdout.decode('utf-8', errors='ignore')
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
        print(f"Mother Topic 2 spans lines {start_line+1} to {end_line} in commit {commit}")
        print("=" * 80)
        for i in range(start_line, end_line):
            print(f"{i+1}: {lines[i]}")
    else:
        print(f"Could not find Mother Topic 2 boundaries. start={start_line}, end={end_line}")
        # Search for related keywords
        for i, line in enumerate(lines):
            if '母题2' in line or '信息库A' in line or '信息库B' in line or '信息库C' in line:
                print(f"{i+1}: {line}")
