import sys

files = [
    r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex",
    r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex"
]

for fp in files:
    print(f"=== File: {fp} ===")
    for enc in ['utf-8', 'gbk', 'gb18030', 'utf-16']:
        try:
            with open(fp, 'r', encoding=enc) as f:
                content = f.read()
            print(f"Success reading with {enc}. Length: {len(content)}")
            # print first 200 chars
            preview = content[:200].replace('\n', ' ')
            print(f"  Preview: {preview}")
            break
        except UnicodeDecodeError:
            print(f"  Failed reading with {enc}")
        except Exception as e:
            print(f"  Error with {enc}: {e}")
