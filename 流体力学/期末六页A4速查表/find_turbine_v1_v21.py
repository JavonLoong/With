import os

root_dir = r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一"
results = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".tex"):
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if "水轮机" in content and "D=20" in content:
                    results.append(filepath)
            except Exception:
                pass

for res in results:
    print(res)
