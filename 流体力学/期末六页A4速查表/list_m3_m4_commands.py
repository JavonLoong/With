import re

with open(r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

m3_commands = []
m4_commands = []
current_mother = 0

for idx, line in enumerate(lines):
    line_num = idx + 1
    if r'\chap{母题3' in line or r'\chap{母题三' in line:
        current_mother = 3
    elif r'\chap{母题4' in line or r'\chap{母题四' in line:
        current_mother = 4
    elif r'\chap{母题5' in line or r'\chap{母题五' in line:
        current_mother = 5
    
    if current_mother in (3, 4):
        # check if it is subq, varq, realq, stepq, formq
        match = re.search(r'\\(subq|varq|realq|stepq|formq|symq|conceptq|lookq|warn|errq)\{([^}]+)\}', line)
        if match:
            cmd = match.group(1)
            arg = match.group(2)
            if current_mother == 3:
                m3_commands.append((line_num, cmd, arg))
            else:
                m4_commands.append((line_num, cmd, arg))

print("=== MOTHER 3 ===")
for l, c, a in m3_commands:
    print(f"Line {l}: \\{c}{{{a}}}")

print("\n=== MOTHER 4 ===")
for l, c, a in m4_commands:
    print(f"Line {l}: \\{c}{{{a}}}")
