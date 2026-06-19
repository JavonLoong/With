import re

filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

start_pattern = r'\\formq\{三临界背压区间：这题以及同类Laval背压题都按这个判\}'
end_pattern = r'\\subq\{第三问：设计超声速工况汞柱高度\}'

start_match = re.search(start_pattern, content)
end_match = re.search(end_pattern, content)

if start_match and end_match:
    print(f"Start index: {start_match.start()}, End index: {end_match.start()}")
    
    new_axis = r"""\formq{三临界背压数轴：同类Laval背压题均按此数轴判定}
\par\noindent\begin{minipage}{\linewidth}
\vspace*{2pt}
\centering
\begin{tikzpicture}[>=Latex, scale=0.74, every node/.style={font=\fontsize{4.8}{5.8}\selectfont}]
% Axis line
\draw[->, thick] (0,0) -- (6.0,0) node[right] {$p_b$};

% Ticks and points
\filldraw[red] (1.5,0) circle (1.8pt) node[below=2pt, black] {$p_{b3}$};
\filldraw[blue] (3.3,0) circle (1.8pt) node[below=2pt, black] {$p_{b2}$};
\filldraw[OliveGreen] (5.1,0) circle (1.8pt) node[below=2pt, black] {$p_{b1}$};

% Regions text above the line
\node[above=2pt, align=center] at (0.75,0) {\key{欠膨胀}\\(出口外膨胀波)};
\node[above=2pt, align=center] at (2.4,0) {\key{过膨胀}\\(出口外斜激波)};
\node[above=2pt, align=center] at (4.2,0) {\key{管内正激波}\\(越右越靠喉部)};
\node[above=2pt, align=center] at (5.7,0) {\key{全亚声速}\\(未完全阻塞)};

% Ticks text below
\node[below=10pt, align=center, red] at (1.5,0) {\textbf{等熵设计}};
\node[below=10pt, align=center, blue] at (3.3,0) {\textbf{出口面激波}};
\node[below=10pt, align=center, OliveGreen] at (5.1,0) {\textbf{喉部刚达声速}};
\end{tikzpicture}
\vspace*{-1pt}
\end{minipage}
"""
    new_content = content[:start_match.start()] + new_axis + content[end_match.start():]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Back-pressure relation table replaced with TikZ number line successfully!")
else:
    print("Could not find start or end pattern for the number line!")
