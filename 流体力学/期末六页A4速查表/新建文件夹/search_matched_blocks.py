with open('matched_utf8.txt', 'r', encoding='utf-8') as f:
    text = f.read()

blocks = text.split("================================================================================\n")

for b in blocks:
    if not b.strip():
        continue
    lines = b.strip().split('\n')
    block_num_line = lines[0]
    
    # search for keywords in the block
    keywords = []
    if '吸水管' in b or '汽蚀' in b or '安装高度' in b:
        keywords.append('吸水/汽蚀/安装高度')
    if '水轮机' in b:
        keywords.append('水轮机')
    if '弯管' in b or '法兰' in b or '喷嘴' in b:
        keywords.append('弯管/法兰/喷嘴')
        
    if keywords:
        print(f"{block_num_line} - Keywords: {keywords}")
        # Print first 5 lines of content (excluding the header block)
        content_lines = [l for l in lines[2:7] if l.strip()]
        for cl in content_lines:
            print("  ", cl)
