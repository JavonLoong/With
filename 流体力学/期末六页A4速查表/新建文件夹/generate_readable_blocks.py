with open('matched_utf8.txt', 'r', encoding='utf-8') as f:
    text = f.read()

blocks = text.split("================================================================================\n")

with open('matched_readable.txt', 'w', encoding='utf-8') as out:
    for idx, b in enumerate(blocks):
        if not b.strip():
            continue
        
        # search for keywords in the block
        keywords = []
        if '吸水管' in b or '汽蚀' in b or '安装高度' in b:
            keywords.append('吸水/汽蚀/安装高度')
        if '水轮机' in b:
            keywords.append('水轮机')
        if '弯管' in b or '法兰' in b or '喷嘴' in b or '动量' in b:
            keywords.append('弯管/法兰/喷嘴/动量')
            
        if keywords:
            out.write("="*80 + "\n")
            out.write(f"BLOCK {idx} | KEYWORDS: {keywords}\n")
            out.write("="*80 + "\n")
            out.write(b + "\n\n")

print("Done! Check matched_readable.txt.")
