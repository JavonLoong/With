import os

workspace_dir = r'd:\虚拟C盘\学习'
search_words = ["D1=200mm", "水轮机输出功率", "泵吸水管最大安装高度"]

matching_files = {}

for root, dirs, files in os.walk(workspace_dir):
    for f in files:
        if f.endswith(('.md', '.txt', '.pdf', '.json', '.html')):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file_obj:
                    content = file_obj.read()
                for word in search_words:
                    if word in content:
                        if word not in matching_files:
                            matching_files[word] = []
                        matching_files[word].append(path)
            except Exception as e:
                # ignore encoding or read errors
                pass

for word, paths in matching_files.items():
    print(f"=== WORD: {word} ===")
    for p in paths[:5]:
        print(p)
