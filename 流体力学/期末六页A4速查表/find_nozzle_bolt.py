import os
import re

root_dir = r'd:\虚拟C盘\学习\流体力学'
keywords = ["345kPa", "103.4kPa", "水平喷嘴"]

results = []

for root, dirs, files in os.walk(root_dir):
    for f in files:
        if f.endswith(('.md', '.txt', '.py', '.json', '.html')):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as file_obj:
                    content = file_obj.read()
                matched_kws = []
                for kw in keywords:
                    if kw in content:
                        matched_kws.append(kw)
                if matched_kws:
                    results.append(f"=== File: {filepath} (Matches: {matched_kws}) ===")
                    for kw in matched_kws:
                        for m in re.finditer(re.escape(kw), content):
                            start = max(0, content.rfind('\n\n', 0, m.start()))
                            end = min(len(content), content.find('\n\n', m.end()))
                            results.append(f"[{kw}] snippet:")
                            results.append(content[start:end].strip())
                            results.append("-" * 20)
                            break
            except Exception as e:
                pass

with open('nozzle_bolt_search.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(results))
print("Search complete.")
