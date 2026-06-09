import markdown
import os

with open(r'd:\虚拟C盘\绪论+课程基础知识讲义+报告模板\探究性课题选题建议.md', 'r', encoding='utf-8') as f:
    text = f.read()

html = markdown.markdown(text, extensions=['tables'])

full_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; padding: 20px; }
  table { border-collapse: collapse; width: 100%; margin: 15px 0; }
  th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
  th { background-color: #f2f2f2; }
  h1, h2, h3 { color: #333; }
</style>
</head>
<body>
""" + html + """
</body>
</html>"""

with open('temp.html', 'w', encoding='utf-8') as f:
    f.write(full_html)

print('HTML generated successfully.')
