import subprocess

git_path = '流体力学/期末六页A4速查表/新建文件夹/期末六页A4速查表_重整版四_公式重排版.tex'

res = subprocess.run(['git', 'log', '--format=%H', '--', git_path], stdout=subprocess.PIPE)
commits = res.stdout.decode('utf-8').splitlines()

seen_tikz = set()

for commit in commits:
    cmd = ['git', 'show', f'{commit}:{git_path}']
    res_show = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res_show.returncode != 0:
        continue
    content = res_show.stdout.decode('utf-8', errors='ignore')
    if '真题[4]' in content:
        idx = content.find('真题[4]')
        # find the begin{tikzpicture} near here
        t_start = content.find('\\begin{tikzpicture}', idx)
        if t_start == -1 or t_start > idx + 500:
            # try looking backwards
            t_start = content.rfind('\\begin{tikzpicture}', 0, idx)
        
        t_end = content.find('\\end{tikzpicture}', t_start)
        if t_start != -1 and t_end != -1:
            tikz_code = content[t_start:t_end+17]
            # normalize whitespace to compare
            norm = " ".join(tikz_code.split())
            if norm not in seen_tikz:
                seen_tikz.add(norm)
                print(f"Commit: {commit[:7]} (Date: {subprocess.check_output(['git', 'show', '-s', '--format=%ci', commit]).decode('utf-8').strip()})")
                print(tikz_code)
                print("===================================\n")
