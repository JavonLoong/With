import re

filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's verify we can find the start and end patterns
start_pattern = r'\\infoh\{势流信息库A 基础公式和数学运算\}'
end_pattern = r'\\subq\{圆柱绕流：已知U、a、theta或表面点，求速度、压力、阻力/升力\}'

start_match = re.search(start_pattern, content)
end_match = re.search(end_pattern, content)

if start_match and end_match:
    print(f"Start index: {start_match.start()}, End index: {end_match.start()}")
    
    new_m2_db = r"""\infoh{势流信息库A 基础公式和数学运算}
\fmlb{\begin{gathered}
\nabla\cdot\bm V = \nabla^2\phi = 0,\ \nabla\times\bm V = \bm\Omega = 0\\
\text{直角：}u_x+v_y+w_z=0,\ \Omega_z=v_x-u_y=-\nabla^2\psi=0\\
\text{极：}\tfrac{\partial v_r}{\partial r} + \tfrac{v_r}{r} + \tfrac{\partial v_\theta}{r\partial\theta}=0,\ \Omega_z=\tfrac{\partial v_\theta}{\partial r} + \tfrac{v_\theta}{r} - \tfrac{\partial v_r}{r\partial\theta}=0\\
u,v=\phi_x,\phi_y=\psi_y,-\psi_x;\ v_r,v_\theta=\phi_r,r^{-1}\phi_\theta=r^{-1}\psi_\theta,-\psi_r\\
p+\tfrac12\rho V^2=\text{const},\ C_p=1-(V/U_\infty)^2,\ q'=\psi_2-\psi_1\\
\Gamma = \oint \bm V\cdot d\bm l,\ L' = \rho U \Gamma,\ \text{点涡：}v_\theta = \tfrac{\Gamma}{2\pi r},\ v_r=0
\end{gathered}}
\par\noindent \renewcommand{\arraystretch}{1.15}{\centering\begin{tabular}{|>{\centering\arraybackslash}p{0.18\linewidth}|>{\centering\arraybackslash}p{0.35\linewidth}|>{\centering\arraybackslash}p{0.35\linewidth}|}
\hline 基元 & $\phi$ & $\psi$\\ \hline
均匀流 & $Ur\cos\theta$ & $Ur\sin\theta$\\ \hline
源/汇 & $\pm Q\ln r/(2\pi)$ & $\pm Q\theta/(2\pi)$\\ \hline
点涡 & $\Gamma\theta/(2\pi)$ & $-\Gamma\ln r/(2\pi)$\\ \hline
偶极 & $M\cos\theta/r$ & $-M\sin\theta/r$\\ \hline
\end{tabular}\par}\renewcommand{\arraystretch}{1}

\infoh{势流信息库B 证明与概念库}
\conceptq{为什么有流函数}二维不可压连续方程$u_x+v_y=0$保证存在$\psi$使$u=\psi_y,v=-\psi_x$。流函数差等于两条流线间单位宽流量。\\
\conceptq{为什么有势函数}无旋$\nabla\times\bm V=0$且区域单连通时，速度场为某标量势的梯度$\bm V=\nabla\phi$。等势线与流线正交。\\
\conceptq{连续/流函数/势函数证明}不可压$\nabla\cdot\bm V=0$；二维给$\psi$：$u=\psi_y,\ v=-\psi_x$；无旋给$\phi$：$\bm V=\nabla\phi$；二者合用得$\nabla^2\phi=0,\ \nabla^2\psi=0$。题问“存在性”先写区域单连通/无旋或二维不可压条件。\\
\conceptq{流函数存在与物理意义}二维不可压：$u_x+v_y=0$。令$u=\psi_y,\ v=-\psi_x$，自动满足连续；反过来连续保证可构造$\psi$。微分式$d\psi=u\,dy-v\,dx$，两流线间单位宽流量$q'=\psi_2-\psi_1$。流线为$\psi=C$，因$d\psi=0\Rightarrow dy/dx=v/u$。\\
\formq{流函数Poisson方程}二维不可压：$u=\psi_y,v=-\psi_x$。涡量$\Omega=v_x-u_y=-(\psi_{xx}+\psi_{yy})=-\nabla^2\psi$，故$\nabla^2\psi=-\Omega$。

\infoh{势流信息库C 常见结论与物理概念}
\par\noindent \renewcommand{\arraystretch}{1.15}{\centering\begin{tabular}{|>{\centering\arraybackslash}p{0.22\linewidth}|>{\centering\arraybackslash}p{0.69\linewidth}|}
\hline 圆柱绕流 & 均匀流+偶极（$M=Ua^2$）。壁面速度 $v_\theta=-2U\sin\theta$，压强 $p=p_\infty+\frac{1}{2}\rho U^2(1-4\sin^2\theta)$。无环量时阻力升力均为0。\\ \hline
有环量圆柱 & 叠加点涡。壁面速度 $v_\theta=-2U\sin\theta+\Gamma/(2\pi a)$，升力 $L'=\rho U\Gamma$（Kutta-Joukowski）。\\ \hline
镜像法 & 固壁为流线。源/汇靠直壁：同号镜像；点涡靠直壁：反号镜像。半平面源汇分母常由 $2\pi\to\pi$。\\ \hline
角域流 & 夹角 $\alpha$，指数 $n=\pi/\alpha$。$\phi=Ar^n\cos n\theta,\psi=Ar^n\sin n\theta$。速度 $V\sim r^{n-1}$。\\ \hline
Rankine半体 & 均匀流+点源。驻点距源 $r=Q/(2\pi U)$，分界流线为 $\psi=Q/2$。\\ \hline
\end{tabular}\par}\renewcommand{\arraystretch}{1}
\conceptq{偶极子物理意义}源汇距离趋零、强度趋无穷 but 乘积有限，得到偶极。圆柱绕流就是均匀流+偶极，偶极强度$M=Ua^2$。\\
\conceptq{为什么圆柱理想阻力为0}势流无粘且前后对称，压力积分$x$方向抵消。该结论与现实矛盾，称达朗贝尔佯谬，现实阻力由粘性分离导致。\\
\conceptq{达朗贝尔佯谬句}“理想不可压无粘定常绕流中，圆柱前后压力分布对称，积分阻力为零；实际阻力来自粘性边界层分离。”\\
\formq{机翼升力}势流中机翼可由保角变换把圆柱映到翼型；环量由Kutta条件确定；升力公式仍为$L'=\rho U\Gamma$。考试概念题写这个即可。\\
\idq{图像：圆柱/球外绕}低Re可能Stokes；高Re看分离和阻力系数。理想势流只给压力分布和升力概念，不给真实阻力。\\
\idq{图里有“圆柱/球绕流”}若是理想势流，压力积分阻力为0；若题给$C_D$，阻力$D=C_D(0.5\rho U^2)A_{\rm front}$，面积取迎风面积。

\infoh{势流信息库D 易错检查与概念}
极坐标速度偏导别漏 $1/r$；流线为 $\psi=C$ ；点涡除原点外无旋但环量非零；$\psi$之差为单位宽流量；半平面源汇分母常由 $2\pi\to\pi$；全场Bernoulli仅在无旋时成立。\\
\errq{错13：把流函数当势函数}流线是$\psi=C$，等势线是$\phi=C$，二者正交。速度关系符号不同，特别是$v=-\psi_x$。\\
\conceptq{空化}局部压力最低处若$p_{\min}\le p_v$发生空化。伯努利题中速度最大点压强最低；泵吸入口高度越大，入口压越低。

"""
    # Replace content between start_match and end_match
    new_content = content[:start_match.start()] + new_m2_db + content[end_match.start():]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Mother Topic 2 Info Databases A-D replaced successfully!")
else:
    print("Could not find start or end pattern!")
