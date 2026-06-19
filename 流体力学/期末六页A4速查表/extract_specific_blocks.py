import re

with open(r"d:\虚拟C盘\学习\流体力学\期末开卷资料_母题证据链版一\期末开卷资料_母题证据链版二十一_旧版全量归位解题链稿.tex", 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find blocks of the form \qt{...} and the following \ans{...} or \chain{...}
# We can use a regex to find all \qt{...} and their content, and then the following \ans or \chain or \res

pattern = re.compile(r'\\qt\{([^{}]+)\}\s*(\\ans\{([^{}]+)\}|\\chain\{([^{}]+)\}|\\res\{([^{}]+)\})?', re.DOTALL)

# Let's write a parser to find matching braces because LaTeX blocks can have nested braces.
# We will iterate through the file and extract blocks that look like \qt{...} and what follows.

blocks = []
pos = 0
while True:
    match = text.find(r'\qt{', pos)
    if match == -1:
        break
    
    # Extract \qt{...} content by matching braces
    start_qt = match + 4
    brace_count = 1
    i = start_qt
    while i < len(text) and brace_count > 0:
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
        i += 1
    qt_content = text[start_qt:i-1]
    
    # Now find the next command (it could be \ans, \chain, \res, \warn, etc.)
    # We look for the next backslash in the next few hundred characters
    next_pos = i
    ans_content = ""
    ans_type = ""
    # Find next command
    cmd_match = re.search(r'\\(ans|chain|res|warn|textbf)\{', text[next_pos:next_pos+300])
    if cmd_match:
        cmd_start = next_pos + cmd_match.start()
        cmd_name = cmd_match.group(1)
        brace_start = cmd_start + len(cmd_name) + 2
        brace_count = 1
        j = brace_start
        while j < len(text) and brace_count > 0:
            if text[j] == '{':
                brace_count += 1
            elif text[j] == '}':
                brace_count -= 1
            j += 1
        ans_content = text[brace_start:j-1]
        ans_type = cmd_name
        pos = j
    else:
        pos = i
        
    blocks.append({
        'qt': qt_content.strip(),
        'ans': ans_content.strip(),
        'ans_type': ans_type,
        'start_pos': match
    })

# Now filter blocks based on keywords
keywords_map = {
    'pump': ['离心泵', '汽蚀', '吸水管'],
    'turbine': ['水轮机'],
    'momentum': ['弯管', '法兰', '射流冲板'],
    'gate': ['闸门', '曲面闸门', '平面闸门', '压力中心'],
    'hp': ['Hagen', 'Poiseuille', '层流'],
    'wall_law': ['壁律', '底层', '摩擦速度', 'sublayer'],
    'dimension': ['量纲', 'Buckingham', '相似'],
    'stress': ['应力张量', '应力矢量', '指定平面']
}

output = []
for key, kws in keywords_map.items():
    output.append(f"=== KEYWORD: {key} ===")
    found = 0
    for b in blocks:
        qt = b['qt']
        ans = b['ans']
        # Check if any keyword matches
        if any(kw in qt or kw in ans for kw in kws):
            output.append(f"QT: {qt}")
            output.append(f"{b['ans_type'].upper()}: {ans}")
            output.append("-" * 30)
            found += 1
            if found >= 3: # limit to top 3 matches
                break

with open("extracted_problems_clean.txt", "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(output))

print("Extracted and saved!")
