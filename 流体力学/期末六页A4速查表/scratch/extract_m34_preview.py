import subprocess, sys

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

# Find all chap boundaries
chaps = []
for i, line in enumerate(lines):
    if '\\chap{' in line:
        chaps.append((i, line.strip()))

for idx, (linenum, text) in enumerate(chaps):
    print(f"Chap {idx+1} at line {linenum+1}: {text[:60]}")

# Extract Mother Topic 3 content (between chap 3 and chap 4)
# Extract Mother Topic 4 content (between chap 4 and chap 5)
for target_idx in [2, 3]:  # 0-indexed, so chap 3 and 4
    if target_idx < len(chaps):
        start = chaps[target_idx][0]
        end = chaps[target_idx+1][0] if target_idx+1 < len(chaps) else len(lines)
        
        # Write to file
        topic_num = target_idx + 1
        outfile = f'流体力学/期末六页A4速查表/scratch/m{topic_num}_preview.txt'
        with open(outfile, 'w', encoding='utf-8') as f:
            for i in range(start, min(end, start + 200)):
                f.write(f"{i+1}: {lines[i]}\n")
        print(f"\nWrote Mother Topic {topic_num} (lines {start+1}-{min(end, start+200)}) to {outfile}")
