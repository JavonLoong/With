import os
import shutil

artifact_dir = r"C:\Users\15410\.gemini\antigravity\brain\d7a3129b-a055-473f-8391-d61281f1f488"
browser_dir = os.path.join(artifact_dir, "browser")
os.makedirs(browser_dir, exist_ok=True)

images = [
    "mid_wbz_p1.png",
    "final_wbz_p1.png",
    "mid_cl_p1.png",
    "mid_ref_p1.png",
    "final_cl_p1.png",
    "final_ref_p1.png"
]

for img in images:
    src = os.path.join(artifact_dir, img)
    dst = os.path.join(browser_dir, img)
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"Copied {img} to browser folder")
    else:
        print(f"Source not found: {src}")

# Generate HTML viewer page
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Cheatsheet Reference Viewer</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 20px; }
        h1 { color: #333; }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h2 { margin-top: 0; font-size: 16px; color: #555; }
        img { width: 100%; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Cheatsheet Reference Viewer (Page 1s)</h1>
    <div class="grid">
        <div class="card">
            <h2>期中一页纸_wbz.pdf (Page 1)</h2>
            <img src="mid_wbz_p1.png">
        </div>
        <div class="card">
            <h2>期末一页纸_wbz.pdf (Page 1)</h2>
            <img src="final_wbz_p1.png">
        </div>
        <div class="card">
            <h2>流力期中一张纸_cl.pdf (Page 1)</h2>
            <img src="mid_cl_p1.png">
        </div>
        <div class="card">
            <h2>流力期中参考纸.pdf (Page 1)</h2>
            <img src="mid_ref_p1.png">
        </div>
        <div class="card">
            <h2>流力期末两张纸_cl.pdf (Page 1)</h2>
            <img src="final_cl_p1.png">
        </div>
        <div class="card">
            <h2>流力期末参考纸.pdf (Page 1)</h2>
            <img src="final_ref_p1.png">
        </div>
    </div>
</body>
</html>
"""

html_path = os.path.join(browser_dir, "view_pdfs.html")
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f"Generated HTML viewer at {html_path}")
