import subprocess

# Path relative to Git repo root
git_path = '流体力学/期末六页A4速查表/新建文件夹/期末六页A4速查表_重整版四_公式重排版.tex'

res = subprocess.run(['git', 'log', '--format=%H', '--', git_path], stdout=subprocess.PIPE)
commits = res.stdout.decode('utf-8').splitlines()
print(f"Total commits: {len(commits)}")

for commit in commits[:30]:
    cmd = ['git', 'show', f'{commit}:{git_path}']
    res_show = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res_show.returncode != 0:
        print(f"Commit {commit[:7]} show failed: {res_show.stderr.decode('utf-8', errors='ignore').strip()}")
        continue
    content = res_show.stdout.decode('utf-8', errors='ignore')
    if '15cm' in content:
        idx = content.find('15cm')
        t_start = content.rfind('\\begin{tikzpicture}', 0, idx)
        t_end = content.find('\\end{tikzpicture}', idx)
        if t_start != -1 and t_end != -1:
            tikz_code = content[t_start:t_end+17]
            print(f"Commit {commit[:7]}: found tikz")
            lines = tikz_code.splitlines()
            for line in lines:
                print("  ", line.strip())
            print("---")
            break # We only need the first commit that contains it (which might be different from current)
        else:
            print(f"Commit {commit[:7]}: 15cm found but no tikz")
    else:
        print(f"Commit {commit[:7]}: 15cm not found")
