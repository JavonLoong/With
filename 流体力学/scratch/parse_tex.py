import re

tex_path = r"D:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex"

with open(tex_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Define \dbsection and \dbblock in preamble
preamble_target = r'\newcommand{\infoh}[1]'
preamble_replacement = r"""\newcommand{\dbsection}[1]{\vspace{0.45pt}{\fontsize{5.8}{6.0}\selectfont\bfseries\color{white}\colorbox{infoc}{\strut\;#1\;}}\par\vspace{0.15pt}}
\newcommand{\dbblock}[1]{\par\noindent\colorbox{infobg}{\begin{minipage}{\dimexpr\linewidth-2\fboxsep\relax}\fontsize{4.85}{5.05}\selectfont #1\end{minipage}}\par\vspace{0.10pt}}
\newcommand{\infoh}[1]"""

if preamble_target in content:
    content = content.replace(preamble_target, preamble_replacement)
    print("Added \\dbsection and \\dbblock to preamble.")

# 2. Modify \pvzfig using string replace instead of re.sub
pvz_old = r"\newcommand{\pvzfig}{\par\noindent\hfill\begin{tikzpicture}[>=Latex,scale=.34,every node/.style={font=\tiny}]"
pvz_old_full = r"""\newcommand{\pvzfig}{\par\noindent\hfill\begin{tikzpicture}[>=Latex,scale=.34,every node/.style={font=\tiny}]
\draw[fill=gray!15,draw=black] (0,0) rectangle (.9,1.45);\draw[fill=gray!15,draw=black] (4.4,0) rectangle (5.25,.85);
\draw[dashed] (.1,1.2)--(5.1,1.2);\draw[dashed] (.1,.45)--(5.1,.45);
\draw[thick] (.9,.36)--(2.15,.36)--(2.15,.54)--(.9,.54);\draw[thick] (2.15,.28)--(4.4,.28)--(4.4,.62)--(2.15,.62);
\draw[blue,->] (1.15,.45)--(3.85,.45);\draw[<->] (.45,.45)--(.45,1.2);\node[left] at (.45,.83){$H$};\draw[<->] (4.85,.85)--(4.85,1.2);\node[right] at (4.85,1.03){$h$};
\node at (1.25,.22){A细};\node at (3.25,.18){B粗};\node at (2.15,.82){突扩};\node at (.45,1.38){C};\node at (4.85,1.02){D};\end{tikzpicture}\hfill\par\vspace{-4pt}}"""

new_pvz = r"""\newcommand{\pvzfig}{\begin{center}\vspace{-2pt}\begin{tikzpicture}[>=Latex,scale=.26,every node/.style={font=\tiny}]
\draw[fill=gray!15,draw=black] (0,0) rectangle (.9,1.45);\draw[fill=gray!15,draw=black] (4.4,0) rectangle (5.25,.85);
\draw[dashed] (.1,1.2)--(5.1,1.2);\draw[dashed] (.1,.45)--(5.1,.45);
\draw[thick] (.9,.36)--(2.15,.36)--(2.15,.54)--(.9,.54);\draw[thick] (2.15,.28)--(4.4,.28)--(4.4,.62)--(2.15,.62);
\draw[blue,->] (1.15,.45)--(3.85,.45);\draw[<->] (.45,.45)--(.45,1.2);\node[left] at (.45,.83){$H$};\draw[<->] (4.85,.85)--(4.85,1.2);\node[right] at (4.85,1.03){$h$};
\node at (1.25,.22){A细};\node at (3.25,.18){B粗};\node at (2.15,.82){突扩};\node at (.45,1.38){C};\node at (4.85,1.02){D};\end{tikzpicture}\vspace{-8pt}\end{center}}"""

if pvz_old_full in content:
    content = content.replace(pvz_old_full, new_pvz)
    print("Replaced \\pvzfig using exact match.")
else:
    # try just replacing the first line as a fallback
    lines = content.split('\n')
    for idx, l in enumerate(lines):
        if "\\newcommand{\\pvzfig}" in l:
            # Reconstruct and replace from idx to idx+5
            target_chunk = "\n".join(lines[idx:idx+6])
            content = content.replace(target_chunk, new_pvz)
            print("Replaced \\pvzfig via line matching.")
            break

# 3. Replace the base database block (Column 2)
new_db_content = r"""\dbsection{A. 常数与基本物性 (Constants \& Properties)}
\dbblock{%
$g = 9.81\,\mathrm{m/s^2}$, $\rho_w = 1000\,\mathrm{kg/m^3}$ (水密度), $\rho_{Hg} = 13600\,\mathrm{kg/m^3}$ (水银密度).\\
$\mu_w = 1.0\times 10^{-3}\,\mathrm{Pa\cdot s}$, $\nu_w = 1.0\times 10^{-6}\,\mathrm{m^2/s}$ (水在20$^\circ$C).\\
空气气体常数 $R = 287\,\mathrm{J/(kg\cdot K)}$, 比热比 $\gamma = 1.4$.\\
标准大气压 $p_a = 101.3\,\mathrm{kPa}$ ($\approx 10.33\,\mathrm{mH_2O}$).\\
单位换算: $1\,\mathrm{kPa}=10^3\,\mathrm{Pa}$, $1\,\mathrm{MPa}=10^6\,\mathrm{Pa}$, $1\,\mathrm{mmHg}=133.3\,\mathrm{Pa}$.\\
流量换算: $1\,\mathrm{L/s}=10^{-3}\,\mathrm{m^3/s}$, $1\,\mathrm{m^3/h}=1/3600\,\mathrm{m^3/s}$.\\
高频关系: $\mu=\rho\nu$, $\nu=\mu/\rho$, $\dot{m}=\rho Q$ (质量流量).\\
压强关系: 表压 $p_g = p_{\rm abs} - p_a$ (绝压), 真空度 $p_v = p_a - p_{\rm abs}$.\\
气体极限速度: $V_{\max} = \sqrt{\frac{2\gamma}{\gamma-1}RT_0}$ (空气 $V_{\max}\approx 44.82\sqrt{T_0}$).\\
\key{流量积分公式}:\\
体积流量: $Q = \iint_A \bm V \cdot \bm n \, dA$, 质量流量: $\dot{m} = \iint_A \rho \bm V \cdot \bm n \, dA$.\\
直角2D: $Q = \int_{y_1}^{y_2} u(y) \, dy$ (单位宽 $q = \int u\,dy$); 直角3D: $Q = \iint u(y,z) \, dydz$.\\
圆管轴对称: $Q = 2\pi\int_0^R u(r)r \, dr$; 环隙轴对称: $Q = 2\pi\int_{R_i}^{R_o} u(r)r \, dr$.\\
球冠面流速 $v_r(\theta)$ 积分: $Q = 2\pi r^2 \int_0^{\theta_0} v_r(\theta)\sin\theta \, d\theta$.%
}

\dbsection{B. 常用几何特征与惯性矩 (Geometry \& Inertia)}
\dbblock{%
圆形: $A = \pi R^2 = \pi d^2/4$, 形心惯性矩 $I_C = \pi R^4/4 = \pi d^4/64$.\\
矩形: $A = bh$, 形心惯性矩 $I_C = bh^3/12$.\\
三角形 (平行底边): $A = bh/2$, 形心惯性矩 $I_C = bh^3/36$.\\
半圆形 (平行直径 centroid 轴): $A = \pi R^2/2$, 形心位置 $y_C = \frac{4R}{3\pi}$, $I_C \approx 0.1098 R^4$.\\
迎风面积 (绕流): 球 $A = \pi d^2/4$, 圆柱 $A = dL$. 摩擦面积 (平板): 双面 $A = 2bL$, 单面 $bL$.\\
\key{静水压力与中心}:\\
平面合力 $F = \rho g h_C A$ ($h_C$为形心竖直深度).\\
倾斜平面 (沿板长坐标 $y$): $h_C = y_C\sin\theta$, 压力中心 $y_D = y_C + \frac{I_C}{y_C A}$.\\
曲面分力: 水平 $F_x = \rho g h_C A_x$ ($A_x$为曲面在竖直面的投影面积); 竖直 $F_y = \rho g V_p$ ($V_p$为压力体体积, 方向看压力体在曲面哪侧).%
}

\dbsection{C. 矢量运算与投影 (Vectors \& Projections)}
\dbblock{%
点乘: $\bm a \cdot \bm b = a_x b_x + a_y b_y + a_z b_z$.\\
叉乘: $\bm a \times \bm b = (a_y b_z - a_z b_y)\bm i + (a_z b_x - a_x b_z)\bm j + (a_x b_y - a_y b_x)\bm k$.\\
力矩/动量矩: $\bm M_O = \bm r \times \bm F$, $\sum \bm M_O = \sum_{\rm out} \rho Q(\bm r \times \bm V) - \sum_{\rm in} \rho Q(\bm r \times \bm V)$.\\
\key{单位法向与平面应力投影}:\\
平面方程 $F(x,y,z)=0$ 的单位法向 $\bm n = \pm \nabla F / |\nabla F|$. 圆柱面 $y^2+z^2=R^2$ 的 $\bm n = (0, y/R, z/R)$.\\
指定平面上的应力矢量 $\bm t_n = P \bm n$ (矩阵-向量乘积).\\
法向应力 $\sigma_n = \bm t_n \cdot \bm n = \bm n^T P \bm n$.\\
切应力矢量 $\bm \tau = \bm t_n - \sigma_n \bm n$, 切应力大小 $\tau = \sqrt{\bm t_n\cdot\bm t_n - \sigma_n^2}$, 夹角 $\cos\alpha = \sigma_n / |\bm t_n|$.%
}

\dbsection{D. 微分算子与坐标变换 (Differential Operators)}
\dbblock{%
梯度 $\nabla f$: 直角 $\left(\frac{\partial f}{\partial x}, \frac{\partial f}{\partial y}, \frac{\partial f}{\partial z}\right)$; 柱坐标 $\left(\frac{\partial f}{\partial r}, \frac{1}{r}\frac{\partial f}{\partial\theta}, \frac{\partial f}{\partial z}\right)$.\\
散度 $\nabla \cdot \bm V$: 直角 $u_x + v_y + w_z$; 柱坐标 $\frac{1}{r}\frac{\partial(r v_r)}{\partial r} + \frac{1}{r}\frac{\partial v_\theta}{\partial\theta} + \frac{\partial v_z}{\partial z}$.\\
旋度 $\nabla \times \bm V$: 直角 $(w_y - v_z)\bm i + (u_z - w_x)\bm j + (v_x - u_y)\bm k$.\\
柱坐标旋度 $z$ 分量 (二维极坐标): $\Omega_z = \frac{1}{r}\left(\frac{\partial(r v_\theta)}{\partial r} - \frac{\partial v_r}{\partial\theta}\right)$.\\
二维平面流旋度 (直角): $\Omega_z = v_x - u_y$, 角速度 $\omega_z = \frac{1}{2}(v_x - u_y)$.%
}

\dbsection{E. 速度变化与应变率 (Kinematics \& Strain Rates)}
\dbblock{%
材料导数: $\frac{D}{Dt} = \frac{\partial}{\partial t} + u\frac{\partial}{\partial x} + v\frac{\partial}{\partial y} + w\frac{\partial}{\partial z}$.\\
加速度: $a_x = u_t + u u_x + v u_y + w u_z$, $a_y = v_t + u v_x + v v_y + w v_z$, $a_z = w_t + u w_x + v w_y + w w_z$.\\
速度梯度张量 $\nabla\bm V$: 分量 $(\nabla\bm V)_{ij} = \frac{\partial v_i}{\partial x_j}$.\\
应变率张量 $e_{ij}$: $e_{xx} = u_x$, $e_{yy} = v_y$, $e_{zz} = w_z$, $e_{xy} = \frac{1}{2}(u_y + v_x)$, $e_{yz} = \frac{1}{2}(v_z + w_y)$, $e_{zx} = \frac{1}{2}(w_x + u_z)$.\\
角变形率: $\dot{\gamma}_{xy} = 2 e_{xy} = u_y + v_x$. 体积变形率: $\nabla\cdot\bm V$.%
}

\dbsection{F. 应力张量与本构方程 (Stress \& Constitution)}
\dbblock{%
对称性: $p_{ij}=p_{ji}$ (微元角动量守恒, 无体偶力).\\
不可压牛顿流体本构: $\sigma_{ij} = -p\delta_{ij} + 2\mu e_{ij}$.\\
正应力: $\sigma_{xx} = -p + 2\mu u_x$, $\sigma_{yy} = -p + 2\mu v_y$, $\sigma_{zz} = -p + 2\mu w_z$.\\
切应力: $\tau_{xy} = \mu(u_y + v_x)$, $\tau_{yz} = \mu(v_z + w_y)$, $\tau_{zx} = \mu(w_x + u_z)$.\\
一维平行流 $u=u(y), v=w=0$: 剪应力 $\tau = \mu\frac{du}{dy}$.\\
粘性力体积源项 (N-S右侧项): $\bm f_{\rm visc} = \mu \nabla^2 \bm V$.%
}

\dbsection{G. 势流、流函数与等价判定 (Potential \& Stream Function)}
\dbblock{%
不可压: $\nabla\cdot\bm V=0 \iff$ 2D 存在流函数 $\psi$ 使得 $u = \psi_y, v = -\psi_x$.\\
无旋: $\nabla\times\bm V=0 \iff$ 存在势函数 $\phi$ 使得 $\bm V = \nabla\phi$.\\
极坐标速度: $v_r = \frac{\partial\phi}{\partial r} = \frac{1}{r}\frac{\partial\psi}{\partial\theta}$, $v_\theta = \frac{1}{r}\frac{\partial\phi}{\partial\theta} = -\frac{\partial\psi}{\partial r}$.\\
Cauchy-Riemann: $\phi_x = \psi_y$, $\phi_y = -\psi_x$.\\
无旋不可压势流 (满足 Laplace 方程): $\nabla^2\phi = 0$, $\nabla^2\psi = 0$.\\
极坐标 Laplace: $\frac{\partial^2 f}{\partial r^2} + \frac{1}{r}\frac{\partial f}{\partial r} + \frac{1}{r^2}\frac{\partial^2 f}{\partial\theta^2} = 0$ (对 $\phi, \psi$ 均适用).%
}

\dbsection{H. 常用证明落笔骨架 (Proof Skeletons)}
\dbblock{%
\key{无旋存在势函数}: $\nabla\times\bm V=0 \implies \oint \bm V\cdot d\bm r = \iint (\nabla\times\bm V)\cdot\bm n\,dA = 0 \implies$ 两点间积分路径无关 $\implies \exists \phi$ 使得 $\bm V = \nabla\phi$.\\
\key{不可压存在流函数}: $\nabla\cdot\bm V=0 \implies u_x+v_y=0 \implies d\psi=u\,dy-v\,dx$ 为全微分 $\implies \exists \psi$ 使得 $u=\psi_y, v=-\psi_x$. 流量 $q' = \psi_2-\psi_1$.\\
\key{等势线与流线正交}: $\nabla\phi\cdot\nabla\psi = (u,v)\cdot(-v,u) = -uv+vu = 0$, 故切线正交.\\
\key{应力张量对称}: 对微元体列角动量平衡 $\sum M_O = I\alpha$. 微元尺寸 $\Delta x \to 0$ 时, 体力矩与惯性矩为 $O(\Delta x^4)$, 表面力剪应力矩为 $O(\Delta x^3) \implies \tau_{xy}=\tau_{yx}$.\\
\key{Bernoulli方程条件}: Euler $\frac{D\bm V}{Dt} = -\frac{1}{\rho}\nabla p + \bm g$. 沿流线积分 ($d\bm r \parallel \bm V$), 在定常、不可压、无粘、保守体力下 $\implies \frac{p}{\rho} + \frac{V^2}{2} + gz = C$. 无旋时扩展至全场.%
}

\dbsection{I. 常见结论与极速定位 (Common Conclusions)}
\dbblock{%
\key{点涡速度}: $v_r = 0, v_\theta = \frac{\Gamma}{2\pi r}$ (原点外无旋 $\nabla\times\bm V = 0$, 但环量 $\Gamma$ 非零).\\
\key{强迫涡速度}: $v_r = 0, v_\theta = \omega r$ (处处有旋 $\Omega_z = 2\omega$, 像刚体旋转).\\
\key{点源速度}: $v_r = \frac{Q}{2\pi r}, v_\theta = 0$. 镜像法: 遇固壁在对称点补等强度同号源/异号涡.\\
\key{有环量圆柱绕流}: 升力 $L' = \rho U \Gamma$ (库塔-儒可夫斯基); 阻力 $D' = 0$ (达朗贝尔佯谬).\\
\key{Couette流动}: $u(y) = U y / h$. 剪应力 $\tau = \mu U/h$.\\
\key{Hagen-Poiseuille流动}: $u(r) = u_{\max}(1-r^2/R^2)$, 平均速度 $\bar{u}=u_{\max}/2$. 压降 $\Delta p = 32\mu L\bar{u}/d^2$.\\
\key{Stokes阻力} ($Re<1$): $D = 3\pi \mu d U$. 经验阻力: $D = C_D \frac{1}{2}\rho U^2 A_{\rm front}$.\\
\key{当地声速}: $a = \sqrt{\gamma R T}$ (空气约 $20.05\sqrt{T}$). 水声速 $a = \sqrt{K/\rho} \approx 1435\,\mathrm{m/s}$.\\
\key{平板层流边界层}: 厚度 $\delta \approx 5x/\sqrt{Re_x}$, 摩擦系数 $C_f = 1.328/\sqrt{Re_L}$ (阻力 $D = C_f \frac{1}{2}\rho U^2 A$).%
}

\dbsection{J. 量纲分析与相似性 (Dimensionless \& Scaling)}
\dbblock{%
无量纲数个数 $N_{\pi} = n - r$ ($n$为变量数, $r$为基本量纲数, 通常为3).\\
雷诺数 $Re = VL/\nu$, 弗劳德数 $Fr = V/\sqrt{gL}$, 欧拉数 $Eu = \Delta p / (\rho V^2)$, 马赫数 $Ma = V/a$, 韦伯数 $We = \rho V^2 L / \sigma$.\\
动力相似: $Re_m = Re_p$ (粘性流), $Fr_m = Fr_p$ (明渠/重力波), $Ma_m = Ma_p$ (高速气体).\\
比例换算: 流量 $Q \sim V L^2$, 力 $F \sim \rho V^2 L^2$, 功率 $P \sim \rho V^3 L^2$, 压强差 $\Delta p \sim \rho V^2$.%
}"""

db_start_marker = r"\infoh{基础信息库A 总公式库：母题1能调用的式子}"
db_end_marker = r"短管可忽略沿程必须题目明说，长管必须算$\lambda L/d$。"

start_idx = content.find(db_start_marker)
end_idx = content.find(db_end_marker)

if start_idx != -1 and end_idx != -1:
    end_idx += len(db_end_marker)
    # Replace that range
    content = content[:start_idx] + new_db_content + content[end_idx:]
    print("Replaced base database block with the Global Base Info Database.")
else:
    print("Error: base database markers not found!")

# Save the updated tex file
with open(tex_path, "w", encoding="utf-8") as f:
    f.write(content)
print("File saved successfully.")
