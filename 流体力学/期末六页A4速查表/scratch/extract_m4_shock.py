import subprocess

git_path = '流体力学/期末六页A4速查表/新建文件夹/期末六页A4速查表_重整版四_公式重排版.tex'
commit = 'aff00fd'
cmd = ['git', 'show', f'{commit}:{git_path}']
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

for enc in ['utf-8', 'gbk', 'utf-8-sig', 'latin-1']:
    try:
        content = res.stdout.decode(enc)
        break
    except:
        pass

lines = content.splitlines()

# Find chap boundaries
chaps = []
for i, line in enumerate(lines):
    if '\\chap{' in line:
        chaps.append((i, line.strip()))

# Mother Topic 4 = chap index 4 (0-based), starts at chaps[4]
# Mother Topic 5 = chap index 5, starts at chaps[5]
start = chaps[4][0]  # 母题4
end = chaps[5][0]    # 母题5

with open('流体力学/期末六页A4速查表/scratch/m4_shock_preview.txt', 'w', encoding='utf-8') as f:
    for i in range(start, end):
        f.write(f"{i+1}: {lines[i]}\n")

print(f"Mother Topic 4 (激波): lines {start+1}-{end}, {end-start} lines")
