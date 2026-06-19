import os

paths = [
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex',
    r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.tex'
]

new_page6_content = r"""\chap{母题7 场变量、应力张量\\静水压与证明小题}
\mview{\key{母题定位}：看见速度场$u,v,w$、应力张量$P$、给定平面法向$\bm n$、闸门/曲面/浮体、或“证明存在势函数/流函数/伯努利条件”，归到本母题。先判模型，再写最短公式链。}

\infoh{场变量与静水压核心概念与证明}
\infotxt{%
梯度$\nabla f=(f_x,f_y,f_z)$；散度$\nabla\cdot\bm V=u_x+v_y+w_z$（不可压流为0）；旋度$\nabla\times\bm V=(w_y-v_z,\ u_z-w_x,\ v_x-u_y)$（无旋为0，$\bm V=\nabla\phi$，满足$\nabla^2\phi=0$）。二维不可压有流函数：$u=\psi_y,v=-\psi_x$，流线满足$dy/dx=v/u$或$\psi=C$。材料导数$D/Dt=\partial_t+u\partial_x+v\partial_y+w\partial_z$。强迫涡自由面：$z=\omega^2r^2/(2g)+C$。应力矢量$\bm t_n=P\bm n$，法向应力$\sigma_n=\bm t_n\cdot\bm n$，切向应力大小$\tau=\sqrt{|\bm t_n|^2-\sigma_n^2}$。平面闸门力$F=\rho gh_CA$；压力中心$y_p=y_C+I_C/(y_CA)$；曲面分力：$F_H=\rho gh_{Cx}A_x$（竖直投影），$F_V=\rho gV$（压力体水重）。应力张量对称：无体偶力时微元角动量平衡（故$p_{xy}=p_{yx}$）。压力中心低于形心：静水压随深度增大，下部压力权重大。
}

\subq{应力张量：$P = \begin{pmatrix} -7 & 0 & 2 \\ 0 & -5 & 0 \\ 2 & 0 & -4 \end{pmatrix}$ kPa，$\bm n = (\frac{2}{3}, -\frac{2}{3}, \frac{1}{3})^T$}
解：1. $\bm t_n = P \bm n = (-4, 10/3, 0)^T$ kPa。2. $\sigma_n = \bm t_n \cdot \bm n = -4.89$ kPa (压)。法向分量 $\bm t_N = \sigma_n \bm n = (-3.26, 3.26, -1.63)^T$ kPa。3. 切向分量 $\bm t_T = \bm t_n - \bm t_N = (-0.74, 0.07, 1.63)^T$，大小 $\tau = |\bm t_T| = 1.79$ kPa。4. $\cos\alpha = \sigma_n/|\bm t_n| = -0.939 \Rightarrow \alpha = 159.9^\circ$。

\subq{倾斜闸门：宽 $b=2$, 长 $L=3$, $\theta=60^\circ$。顶在水深 $h_1=1$（铰链在顶）}
解：1. 顶距水面交线 $y_1 = h_1/\sin 60^\circ = 1.155$。形心坐标 $y_C = y_1 + L/2 = 2.655$，形心深度 $h_C = y_C \sin 60^\circ = 2.30$。2. 总压力：$F = \rho g h_C A = 135.4\text{ kN}$。3. 压力中心：$y_p = y_C + I_C/(y_C A) = 2.655 + 4.5/(2.655 \times 6) = 2.938$。离顶距 $L_p = y_p - y_1 = 1.783$。4. 力矩平衡：$F \times L_p - T \times (L \sin 60^\circ) = 0 \Rightarrow T = 92.9\text{ kN}$。

\subq{常用几何：静水压和量纲题会用}
圆$A=\pi d^2/4,\ I_C=\pi d^4/64$；矩形$A=bh,\ I_C=bh^3/12$；三角形$A=bh/2,\ I_C=bh^3/36$；半圆$A=\pi R^2/2,\ y_C=4R/(3\pi)$。量纲法：变量$n$个、基本量纲$r$个，则$\pi$群$n-r$个；常选$\rho,V,L$作重复变量。

\stepq{解题步骤与易错点}
速度场：连续（$\nabla\cdot\bm V=0$）、有旋（$\nabla\times\bm V=0$）；不可压找$\psi$，无旋找$\phi$；迹线必须积分。闸门：算$h_C\to F\to y_p\to$力矩。相对平衡：加速沿倾角$\tan\alpha=a/g$，旋转面$z=\omega^2r^2/(2g)+C$。注意：迹线不等于流线；有流函数不一定无旋。

\infoh{选择与判断题高频概念秒杀库（防坑指南）}
\infotxt{%
\textbf{激波前后物性}：通过正激波（相对静止）：静压$p\uparrow$、静密$\rho\uparrow$、静温$T\uparrow$、静焓$h\uparrow$；总温$T_0$、总焓$h_0$不变（绝热流）；总压$p_0\downarrow$（有熵增）；临界截面积$A^*$不变（流率守恒，考试以此为准）。如果是斜激波，切向速度$V_t$不变，法向速度减速。\\
\textbf{连续性方程}：连续性方程$\partial_t \rho + \nabla\cdot(\rho \bm V)=0$源自质量守恒（运动学规律），不涉及粘性或力，故\warn{粘性流体与理想流体的连续性方程形式完全相同}。\\
\textbf{低Re小球绕流}：当$Re<1$（Stokes流）时，流动中惯性力极微弱，核心是\warn{忽略了流体质点的加速度}（即忽略主导惯性项），但绝对没有忽略流体粘性（粘性是主导项）。\\
\textbf{流函数与势函数}：1. 只要是二维不可压流动（定常与否、有无粘性均可），\warn{必然存在流函数 $\psi$}。2. 只有无旋流动才存在势函数 $\phi$。3. 有流函数不一定有势函数（可能有旋）；有势函数不一定有流函数（可能三维）。\\
\textbf{层流与湍流}：1. 雷诺数$Re$是惯性力与粘性力之比，能在一定程度上反映粘性流体流动特征。2. 转捩雷诺数受管壁粗糙度和外界扰动影响，不是确定的常数。3. 湍流时均化后引入了雷诺应力项，其时均连续和动量方程均\warn{不封闭}，必须引入湍流模型。\\
\textbf{流线与迹线}：流线是同一时刻不同质点速度切线（$dx/u=dy/v=dz/w$）；迹线是同一质点在不同时刻的轨迹（$dx/dt=u$）。定常流动中流线与迹线重合，非定常时通常不重合。\\
\textbf{Bernoulli方程条件}：沿流线成立条件：定常、不可压、无粘性、保守质量力（如重力）；无旋时可全场成立。\\
\textbf{流动分离条件}：必要条件：存在逆压梯度（即$dp/dx>0$）；充分条件（分离判据）：壁面剪力降为零（$\tau_w=0$）。\\
\textbf{阻力危机}：圆柱/球等钝体在临界$Re$附近，边界层由层流转捩为湍流，动量增加，抗逆压梯度能力增强，分离点后移，尾流变窄，压差阻力突降，总阻力系数$C_D$骤减。\\
\textbf{水击（水锤）}：阀门突然关闭引起管内流速骤变，导致压强交替升降。最大压强变化$\Delta p = \rho c \Delta v$，$c$为水击波速。
}

\end{multicols}
\end{document}
"""

for path in paths:
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find the chap position
    target_start = r'\chap{母题7 场变量、应力张量'
    pos = content.find(target_start)
    if pos == -1:
        # Try alternate name if any
        target_start = r'\chap{母题7'
        pos = content.find(target_start)
        
    if pos != -1:
        modified = content[:pos] + new_page6_content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(modified)
        print(f"Successfully reorganized Page 6 in {os.path.basename(path)}")
    else:
        print(f"Error: Could not find Mother Topic 7 start in {os.path.basename(path)}")

print("Page 6 reorganization completed!")
