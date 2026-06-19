import subprocess

git_path = '流体力学/期末六页A4速查表/新建文件夹/期末六页A4速查表_重整版四_公式重排版.tex'

res = subprocess.run(['git', 'log', '--format=%H', '--', git_path], stdout=subprocess.PIPE)
commits = res.stdout.decode('utf-8').splitlines()

seen_schemeshock = set()

for commit in commits:
    cmd = ['git', 'show', f'{commit}:{git_path}']
    res_show = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res_show.returncode != 0:
        continue
    content = res_show.stdout.decode('utf-8', errors='ignore')
    if 'schemeshock' in content:
        idx = content.find('newcommand{\\schemeshock}')
        if idx != -1:
            t_end = content.find('}', idx)
            # Find matching braces or just the tikzpicture block inside it
            tik_start = content.find('\\begin{tikzpicture}', idx)
            tik_end = content.find('\\end{tikzpicture}', tik_start)
            if tik_start != -1 and tik_end != -1:
                tikz_code = content[tik_start:tik_end+17]
                norm = " ".join(tikz_code.split())
                if norm not in seen_schemeshock:
                    seen_schemeshock.add(norm)
                    print(f"Commit: {commit[:7]} (Date: {subprocess.check_output(['git', 'show', '-s', '--format=%ci', commit]).decode('utf-8').strip()})")
                    print(tikz_code)
                    print("===================================\n")
