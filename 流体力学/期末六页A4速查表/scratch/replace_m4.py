import re

filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

start_pattern = r'\\infoh\{激波/PM信息库A 基础公式和数学运算\}'
end_pattern = r'\\subq\{正激波：已知波前M1或面积位置，求M2、p2、T2、总压损失\}'

start_match = re.search(start_pattern, content)
end_match = re.search(end_pattern, content)

if start_match and end_match:
    print(f"Start index: {start_match.start()}, End index: {end_match.start()}")
    
    new_m4_db = r"""\infoh{激波/PM信息库A 基础公式和数学运算}
\conceptq{正激波：已知波前Ma1，求波后Ma2、压力、温度、总压损失}
\fmlb{\begin{gathered}
Ma_2^2 = \frac{1 + \frac{\gamma-1}{2} Ma_1^2}{\gamma Ma_1^2 - \frac{\gamma-1}{2}} = \frac{1 + 0.2Ma_1^2}{1.4Ma_1^2 - 0.2}\quad (\text{空气})\\
\frac{p_2}{p_1} = 1 + \frac{2\gamma}{\gamma+1}(Ma_1^2 - 1) = \frac{7Ma_1^2 - 1}{6}\quad (\text{空气})\\
\frac{\rho_2}{\rho_1} = \frac{(\gamma+1)Ma_1^2}{(\gamma-1)Ma_1^2 + 2} = \frac{6Ma_1^2}{Ma_1^2 + 5}\quad (\text{空气})\\
\frac{T_2}{T_1} = (p_2/p_1)/(\rho_2/\rho_1),\quad \frac{p_{02}}{p_{01}} = \frac{p_2}{p_1} \left(\frac{1+0.2Ma_2^2}{1+0.2Ma_1^2}\right)^{3.5}
\end{gathered}}
\conceptq{斜激波与PM膨胀波基础公式}
\fmlb{\begin{gathered}
Ma_{n1} = Ma_1\sin\beta,\quad Ma_2 = \frac{Ma_{n2}}{\sin(\beta-\theta)},\quad \mu = \sin^{-1}(1/Ma)\\
\tan\theta = 2\cot\beta \frac{Ma_1^2\sin^2\beta - 1}{Ma_1^2(\gamma + \cos2\beta) + 2}\\
\nu(Ma) = \sqrt{\frac{\gamma+1}{\gamma-1}}\tan^{-1}\sqrt{\frac{\gamma-1}{\gamma+1}(Ma^2-1)} - \tan^{-1}\sqrt{Ma^2-1}\\
\text{空气：}\quad \nu(Ma) = \sqrt6\tan^{-1}\sqrt{(Ma^2-1)/6} - \tan^{-1}\sqrt{Ma^2-1}
\end{gathered}}

\infoh{激波/PM信息库B 判定链与计算流程}
\stepq{斜激波计算流程}
1. 已知 $Ma_1$ 和 $\theta$，查 $\theta-\beta-Ma$ 曲线或用公式迭代求得波角 $\beta$ (通常取弱激波解)；\\
2. 计算等效法向入口马赫数 $Ma_{n1} = Ma_1\sin\beta$；\\
3. 利用正激波关系求出法向波后马赫数 $Ma_{n2}$ 以及压强比 $p_2/p_1$、温度比 $T_2/T_1$ 等；\\
4. 还原斜激波后真实马赫数 $Ma_2 = Ma_{n2}/\sin(\beta-\theta)$。\\
\stepq{Prandtl-Meyer 膨胀波计算流程}
1. 已知 $Ma_1$ 和壁面转角 $\delta$ (膨胀角)，计算波后 PM 函数值 $\nu(Ma_2) = \nu(Ma_1) + \delta$；\\
2. 利用 $\nu(Ma)$ 关系式或查表求得波后马赫数 $Ma_2$；\\
3. 由于膨胀波为等熵过程，故滞止量 $p_0, T_0$ 不变；\\
4. 由等熵关系式求出波后静压 $p_2 = p_0/(1+0.2Ma_2^2)^{3.5}$ 和静温 $T_2 = T_0/(1+0.2Ma_2^2)$。

\infoh{激波/PM信息库C 难点大综合与常考物理问答}
\subq{激波反射与交汇波系分析（多波计算）}
多波交汇或反射时，逐道波更新状态：每过一道斜激波用斜激波关系，每过一道膨胀波用 PM 等熵膨胀。接触面两侧静压相等 ($p_2=p_3$) 且气流方向一致 ($\theta_2=\theta_3$)。\\
\subq{运动正激波与撞墙反射}
坐标系固结在激波上，将运动激波转化为定常激波。反射波需满足墙面不穿透边界条件，即反射波后流体相对墙壁静止 ($V_3=0$)。\\
\subq{脱体激波判定}
若偏转角 $\theta > \theta_{\max}$，斜激波无法附着在前缘，形成脱体弓形激波。此时前缘附近为正激波。\\
\conceptq{概念简答：激波与膨胀波物理特征}
激波为超声速流受压阻碍产生的有限强度间断，是强非等熵过程，滞止温度 $T_0$ 不变，滞止压强 $p_0$ 下降 (熵增造成波阻)；而膨胀波是无数连续微弱扰动的叠加，为等熵过程，$p_0, T_0$ 保持不变。

\infoh{激波/PM信息库D 速查小表格}
\lookq{小查表：空气等熵/PM函数关系表}
{\centering\renewcommand{\arraystretch}{1.15}\begin{tabular}{|c|c|c|c|c|}
\hline $Ma$ & $T_0/T$ & $p_0/p$ & $A/A^*$ & $\nu(^\circ)$ \\ \hline
0.5 & 1.05 & 1.19 & 1.34 & -- \\ \hline
1.0 & 1.20 & 1.89 & 1.00 & 0 \\ \hline
1.5 & 1.45 & 3.67 & 1.18 & 11.9 \\ \hline
2.0 & 1.80 & 7.82 & 1.69 & 26.4 \\ \hline
2.5 & 2.25 & 17.1 & 2.64 & 39.1 \\ \hline
3.0 & 2.80 & 36.7 & 4.23 & 49.8 \\ \hline
\end{tabular}\par}\renewcommand{\arraystretch}{1}
\lookq{小查表：空气正激波对照表}
{\centering\renewcommand{\arraystretch}{1.15}\begin{tabular}{|c|c|c|c|}
\hline $Ma_1$ & $Ma_2$ & $p_2/p_1$ & $p_{02}/p_{01}$ \\ \hline
1.5 & 0.701 & 2.46 & 0.93 \\ \hline
2.0 & 0.577 & 4.50 & 0.72 \\ \hline
3.0 & 0.475 & 10.33 & 0.33 \\ \hline
\end{tabular}\par}\renewcommand{\arraystretch}{1}

"""
    new_content = content[:start_match.start()] + new_m4_db + content[end_match.start():]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Mother Topic 4 Info Databases A-D replaced successfully!")
else:
    print("Could not find start or end pattern for Topic 4!")
