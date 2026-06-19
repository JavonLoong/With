import re

filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

start_pattern = r'\\infoh\{可压/Laval信息库A 基础公式和数学运算\}'
end_pattern = r'\\realq\{真题：Laval喷管最大质量流量，给\$p\_0,T\_0,A\_t\$求\$\\dot m\_\{\\max\}\$\}'

start_match = re.search(start_pattern, content)
end_match = re.search(end_pattern, content)

if start_match and end_match:
    print(f"Start index: {start_match.start()}, End index: {end_match.start()}")
    
    new_m3_db = r"""\infoh{可压/Laval信息库A 基础公式和数学运算}
\fmlb{\begin{gathered}
p=\rho RT,\quad a=\sqrt{\gamma RT},\quad Ma=V/a,\quad T_0/T=1+0.2Ma^2\\
p_0/p=(1+0.2Ma^2)^{3.5},\quad \rho_0/\rho=(1+0.2Ma^2)^{2.5}
\end{gathered}}
\fmlb{\begin{gathered}
\frac{T^*}{T_0}=0.833,\quad \frac{p^*}{p_0}=0.528,\quad \frac{\rho^*}{\rho_0}=0.634,\quad Ma=1,\ A=A^*\\
\frac{A}{A^*}=\frac1{Ma}\left(\frac{5+Ma^2}{6}\right)^3,\quad A/A^*>1\Rightarrow Ma<1\text{或}Ma>1\\
\dot m=\rho VA=ApMa\sqrt{\gamma/(RT)} = A p_0\sqrt{\gamma/(RT_0)}Ma(1+0.2Ma^2)^{-3}\\
\dot m_{\max}=0.0404A^*p_0/\sqrt{T_0}\quad(\text{空气，}p_0{\rm Pa},T_0{\rm K})
\end{gathered}}

\infoh{可压/Laval信息库B 证明链和判定链}
\textbf{等熵关系证明链}：能量给$T_0=T+V^2/(2c_p)$，代$V=Ma,\ a^2=\gamma RT,\ c_p=\gamma R/(\gamma-1)$得$T_0/T=1+(\gamma-1)Ma^2/2$；再用等熵$p/\rho^\gamma=C,\ p=\rho RT$得$p_0/p=(T_0/T)^{\gamma/(\gamma-1)}$。\\
\textbf{阻塞判定链}：质量流量$\dot m(Ma)$对$Ma$求极值，最大点$Ma=1$，故最小面积截面若达到$Ma=1$则阻塞；继续降背压只改变下游波系，不增大$\dot m$。\\
\textbf{背压判定链}：收缩管比$p_b/p_0$和0.528；Laval先判$A_t=A^*$，再由$A_e/A_t$求两支$Ma_e$，得$p_{b1},p_{b3}$，再用出口正激波得$p_{b2}$，把实际$p_b$放入区间。

\infoh{可压/Laval信息库C 常见结论库}
\par\noindent \renewcommand{\arraystretch}{1.15}{\centering\begin{tabular}{|>{\centering\arraybackslash}p{0.25\linewidth}|>{\centering\arraybackslash}p{0.66\linewidth}|}
\hline 亚声速面积效应 & 收缩加速、扩张减速升压。\\ \hline
超声速面积效应 & 扩张加速降压、收缩减速升压；Laval靠扩张段得到超声速。\\ \hline
收缩喷管 & 未阻塞$p_e=p_b$；阻塞时出口$Ma=1,p_e=p^*$，$\dot m$最大。\\ \hline
Laval背压 & 高背压全亚；再降喉部阻塞；管内激波向出口移动；设计时全管等熵；更低欠膨胀。\\ \hline
跨正激波 & $T_0$不变、$p_0$下降；后续等熵计算必须换$p_{02}$。\\ \hline
\end{tabular}\par}\renewcommand{\arraystretch}{1}

\infoh{可压/Laval信息库D 易错检查}
$p_0,T_0$是滞止量，$p,T$是静量；$p_b$是外界背压，$p_e$是出口内压，二者不总相等。$A_t$是几何喉部，阻塞时才等于$A^*$。$0.528$只表示空气$Ma=1$临界静压比，不是所有喉部/出口/背压比。面积--马赫数有亚/超两支，必须写明支路。压强用绝压，温度用K；液体管路Bernoulli/H--P不能直接套到可压喷管。

"""
    new_content = content[:start_match.start()] + new_m3_db + content[end_match.start():]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Mother Topic 3 Info Databases A-D replaced successfully!")
else:
    print("Could not find start or end pattern for Topic 3!")
