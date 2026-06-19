import sys

# redirect output to nozzle_results.txt
with open('nozzle_results.txt', 'w', encoding='utf-8') as f_out:
    sys.stdout = f_out
    
    import os
    root_dir = r'd:\虚拟C盘\学习\流体力学'
    pattern = "D1=200mm"

    matches = []
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if f.endswith(('.md', '.txt', '.py', '.json', '.html')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file_obj:
                        content = file_obj.read()
                    if pattern in content:
                        matches.append((path, content))
                except Exception:
                    pass

    print(f"Found {len(matches)} files")
    for path, content in matches:
        print(f"=== File: {path} ===")
        lines = content.split('\n')
        for idx, line in enumerate(lines):
            if pattern in line:
                start_idx = max(0, idx - 10)
                end_idx = min(len(lines), idx + 35)
                print('\n'.join(lines[start_idx:end_idx]))
                print("*"*50)
