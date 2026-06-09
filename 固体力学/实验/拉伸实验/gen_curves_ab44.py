"""
为AB44组三种材料重新绘制σ-ε曲线
严格按PPT要求：(1)坐标转换 (2)坐标平移 (3)标出指标
"""
import csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
rcParams['axes.unicode_minus'] = False
rcParams['font.size'] = 11

def read_csv_data(filename, encoding='gbk'):
    """读取CSV，返回 {group_name: {col_header: [values]}}"""
    with open(filename, 'r', encoding=encoding) as f:
        reader = csv.reader(f)
        row0 = next(reader)  # group names
        row1 = next(reader)  # headers
        row2 = next(reader)  # units
        
        # 找列数per group
        n_cols = len(row1)
        # 找group分隔
        groups = []
        headers_per_group = []
        for i, v in enumerate(row0):
            if v.strip():
                groups.append((i, v.strip()))
        
        # 确定每组列数
        group_data = {}
        for gi in range(len(groups)):
            start = groups[gi][0]
            end = groups[gi+1][0] if gi+1 < len(groups) else n_cols
            gname = groups[gi][1]
            hdrs = [row1[j].strip() for j in range(start, end)]
            group_data[gname] = {h: [] for h in hdrs}
            group_data[gname]['_start'] = start
            group_data[gname]['_end'] = end
            group_data[gname]['_headers'] = hdrs
        
        for row in reader:
            for gname, gd in group_data.items():
                s, e = gd['_start'], gd['_end']
                try:
                    vals = [float(row[j]) for j in range(s, e)]
                    for hi, h in enumerate(gd['_headers']):
                        gd[h].append(vals[hi])
                except (ValueError, IndexError):
                    pass
        
        # 转numpy
        for gname in group_data:
            for h in group_data[gname]['_headers']:
                group_data[gname][h] = np.array(group_data[gname][h])
    
    return group_data

def coordinate_shift(strain, stress):
    """
    坐标平移：低载非线性段线性化
    1. 找弹性段的线性部分
    2. 做线性拟合
    3. 拟合直线与横轴交点 → 新原点
    4. 应变减去偏移量
    """
    # 找弹性段: 应力在20%~80%最大应力范围内的上升段
    max_stress = np.max(stress)
    # 找到应力首次达到max_stress的位置(排除后段)
    peak_idx = np.argmax(stress)
    
    # 弹性段：取应力从10%到50%最大应力的区间
    s_low = 0.10 * max_stress
    s_high = 0.50 * max_stress
    
    mask = (stress > s_low) & (stress < s_high) & (np.arange(len(stress)) < peak_idx)
    if np.sum(mask) < 10:
        # 数据太少，取更宽范围
        s_low = 0.05 * max_stress
        s_high = 0.60 * max_stress
        mask = (stress > s_low) & (stress < s_high) & (np.arange(len(stress)) < peak_idx)
    
    if np.sum(mask) < 5:
        return strain, 0  # 无法平移
    
    strain_fit = strain[mask]
    stress_fit = stress[mask]
    
    # 线性拟合: stress = k * strain + b
    coeffs = np.polyfit(strain_fit, stress_fit, 1)
    k, b = coeffs
    
    # 拟合直线与横轴交点: 0 = k * strain_0 + b => strain_0 = -b/k
    strain_offset = -b / k if k != 0 else 0
    
    shifted_strain = strain - strain_offset
    return shifted_strain, strain_offset

# ============================================================
# 1. 铝合金
# ============================================================
print("=== 铝合金 ===")
# 弹性模量数据在complete_analysis.json中已有
# 破坏数据
al_data = read_csv_data('铝合金破坏.csv')
gname = list(al_data.keys())[0]
al = al_data[gname]
print(f"  铝合金破坏数据组: {gname}, headers: {al['_headers']}")

# 参数
d0_al = 4.81; S0_al = np.pi * d0_al**2 / 4; L0_al = 25.0
ext_gauge = 50.0  # mm

# 提取数据
al_load = al.get('载荷', al.get('load', None))
al_ext_strain = None
al_stroke = None
for h in al['_headers']:
    if '引伸计' in h and '应变' in h:
        al_ext_strain = al[h]
    elif '行程' == h or h == '行程':
        al_stroke = al[h]
    elif '载荷' in h:
        al_load = al[h]

if al_ext_strain is None:
    # 尝试其他列名
    for h in al['_headers']:
        if '引伸计' in h and '应变' not in h:
            # 引伸计位移，需要除以标距
            al_ext_disp = al[h]
            al_ext_strain = al_ext_disp / ext_gauge * 100  # %
            break

print(f"  load shape: {al_load.shape}, ext_strain: {al_ext_strain.shape if al_ext_strain is not None else 'None'}")

# 应力
al_stress = al_load / S0_al  # MPa

# 应变：引伸计有效段用引伸计，之后用行程/Lc
Lc_al = 70.0  # mm, 平行段
if al_ext_strain is not None:
    # 找引伸计最大值点(被取下)
    ext_max_idx = np.argmax(np.abs(al_ext_strain))
    # 拼接
    al_strain = np.copy(al_ext_strain)
    if al_stroke is not None and ext_max_idx < len(al_strain) - 100:
        stroke_strain = al_stroke / Lc_al * 100
        offset = al_strain[ext_max_idx] - stroke_strain[ext_max_idx]
        al_strain[ext_max_idx+1:] = stroke_strain[ext_max_idx+1:] + offset
else:
    al_strain = al_stroke / Lc_al * 100

# 坐标平移
al_strain_shifted, al_offset = coordinate_shift(al_strain, al_stress)
print(f"  坐标平移偏移量: {al_offset:.4f}%")

# 力学指标
Fm_al = np.max(al_load); Rm_al = Fm_al / S0_al
Fm_idx_al = np.argmax(al_load)
# Rp0.2: 0.2%偏移法
# 从拟合直线偏移0.2%找交点
# 简化：从分析结果取
Fp02_al = 6929; Rp02_al = Fp02_al / S0_al
print(f"  Rm={Rm_al:.1f}MPa, Rp0.2={Rp02_al:.1f}MPa")

# ============================================================
# 2. 铸铁
# ============================================================
print("\n=== 铸铁 ===")
ci_data = read_csv_data('铸铁破坏.csv')
gname_ci = list(ci_data.keys())[0]
ci = ci_data[gname_ci]
print(f"  铸铁破坏数据组: {gname_ci}, headers: {ci['_headers']}")

d0_ci = 4.87; S0_ci = np.pi * d0_ci**2 / 4
Lc_ci = 70.0  # mm (平行段，来源PPT)

ci_load = None; ci_stroke = None
for h in ci['_headers']:
    if '载荷' in h: ci_load = ci[h]
    elif '行程' == h or h == '行程': ci_stroke = ci[h]

# 铸铁无引伸计(破坏时)，用行程/Lc
ci_stress = ci_load / S0_ci
ci_strain = ci_stroke / Lc_ci * 100  # %

# 坐标平移
ci_strain_shifted, ci_offset = coordinate_shift(ci_strain, ci_stress)
print(f"  坐标平移偏移量: {ci_offset:.4f}%")

Fm_ci = np.max(ci_load); Rm_ci = Fm_ci / S0_ci
print(f"  Rm={Rm_ci:.1f}MPa")

# ============================================================
# 3. 高分子
# ============================================================
print("\n=== 高分子 ===")
poly_data = read_csv_data('AB44高分子材料拉伸.csv')
gname_poly = list(poly_data.keys())[0]
poly = poly_data[gname_poly]
print(f"  高分子数据组: {gname_poly}, headers: {poly['_headers']}")

b_poly = 10.0; h_poly = 4.0; S0_poly = b_poly * h_poly
Lc_poly = 55.0  # mm (平行段，PPT Slide 31)

poly_load = None; poly_stroke = None
for h in poly['_headers']:
    if '载荷' in h: poly_load = poly[h]
    elif '行程' == h or h == '行程': poly_stroke = poly[h]

poly_stress = poly_load / S0_poly
poly_strain = poly_stroke / Lc_poly * 100  # %

# 坐标平移
poly_strain_shifted, poly_offset = coordinate_shift(poly_strain, poly_stress)
print(f"  坐标平移偏移量: {poly_offset:.4f}%")

Fm_poly = np.max(poly_load); Rm_poly = Fm_poly / S0_poly
# 屈服强度：平台起点
# 找屈服平台
win = 100
if len(poly_stress) > win * 2:
    poly_smooth = np.convolve(poly_stress, np.ones(win)/win, mode='same')
else:
    poly_smooth = poly_stress

# 屈服：第一个局部最大值后的平台
search_end_poly = min(len(poly_stress) // 3, 15000)
# 找前段最大值
poly_peak_idx = np.argmax(poly_smooth[:search_end_poly])
sigma_y_poly = poly_stress[poly_peak_idx]
print(f"  σy={sigma_y_poly:.1f}MPa, Rm={Rm_poly:.1f}MPa")

# ============================================================
# 4. 绘图 - 报告A: 铝合金单独曲线(两张: 完整+弹性段)
# ============================================================
print("\n=== 绘图 ===")

# --- 报告A: 铝合金 ---
fig_a, axes_a = plt.subplots(1, 2, figsize=(14, 6))

# 左: 完整曲线
axes_a[0].plot(al_strain_shifted, al_stress, 'b-', lw=0.6)
axes_a[0].set_xlabel('工程应变 ε (%)')
axes_a[0].set_ylabel('工程应力 σ (MPa)')
axes_a[0].set_title('铝合金拉伸 工程应力-工程应变曲线')
axes_a[0].grid(True, alpha=0.3)
axes_a[0].set_xlim(left=-0.5)
axes_a[0].set_ylim(bottom=-10)

# 标注 Rp0.2
# 找Rp0.2对应的应变位置
rp02_strain_idx = np.argmin(np.abs(al_load - Fp02_al))
axes_a[0].annotate(f'$R_{{p0.2}}$={Rp02_al:.0f} MPa',
    xy=(al_strain_shifted[rp02_strain_idx], Rp02_al),
    xytext=(al_strain_shifted[rp02_strain_idx]+2, Rp02_al-30),
    arrowprops=dict(arrowstyle='->', color='blue', lw=1.2),
    fontsize=10, color='blue', fontweight='bold')

# 标注 Rm
axes_a[0].annotate(f'$R_m$={Rm_al:.0f} MPa',
    xy=(al_strain_shifted[Fm_idx_al], Rm_al),
    xytext=(al_strain_shifted[Fm_idx_al]-5, Rm_al+15),
    arrowprops=dict(arrowstyle='->', color='red', lw=1.2),
    fontsize=10, color='red', fontweight='bold')

# 右: 弹性段放大 + 0.2%偏移线
elastic_end = min(ext_max_idx if al_ext_strain is not None else 5000, 5000)
axes_a[1].plot(al_strain_shifted[:elastic_end], al_stress[:elastic_end], 'b-', lw=0.8)
axes_a[1].set_xlabel('工程应变 ε (%)')
axes_a[1].set_ylabel('工程应力 σ (MPa)')
axes_a[1].set_title('弹性段放大（含0.2%偏移法）')
axes_a[1].grid(True, alpha=0.3)

# 画0.2%偏移线
# 弹性段斜率
mask_el = (al_stress > 50) & (al_stress < 200) & (np.arange(len(al_stress)) < elastic_end)
if np.sum(mask_el) > 10:
    k_el = np.polyfit(al_strain_shifted[mask_el], al_stress[mask_el], 1)[0]
    eps_line = np.linspace(0.2, al_strain_shifted[elastic_end-1], 100)
    sig_line = k_el * (eps_line - 0.2)
    axes_a[1].plot(eps_line, sig_line, 'r--', lw=1, label='0.2%偏移线')
    axes_a[1].axhline(y=Rp02_al, color='blue', ls=':', alpha=0.5)
    axes_a[1].annotate(f'$R_{{p0.2}}$={Rp02_al:.0f} MPa', 
        xy=(0.2 + Rp02_al/k_el, Rp02_al),
        xytext=(0.2 + Rp02_al/k_el + 0.3, Rp02_al - 40),
        arrowprops=dict(arrowstyle='->', color='blue'),
        fontsize=9, color='blue')
    axes_a[1].legend(fontsize=9)

plt.tight_layout()
plt.savefig('curve_A_aluminum.png', dpi=200, bbox_inches='tight')
plt.close()
print("  curve_A_aluminum.png saved")

# --- 报告B: 铸铁曲线 ---
fig_ci, ax_ci = plt.subplots(figsize=(8, 6))
ax_ci.plot(ci_strain_shifted, ci_stress, 'b-', lw=0.8)
ax_ci.set_xlabel('工程应变 ε (%)')
ax_ci.set_ylabel('工程应力 σ (MPa)')
ax_ci.set_title('铸铁拉伸 工程应力-工程应变曲线')
ax_ci.grid(True, alpha=0.3)
ax_ci.set_xlim(left=-0.1)
ax_ci.set_ylim(bottom=-10)

Fm_idx_ci = np.argmax(ci_load)
ax_ci.annotate(f'$R_m$={Rm_ci:.0f} MPa',
    xy=(ci_strain_shifted[Fm_idx_ci], Rm_ci),
    xytext=(ci_strain_shifted[Fm_idx_ci]*0.5, Rm_ci*0.8),
    arrowprops=dict(arrowstyle='->', color='red', lw=1.2),
    fontsize=11, color='red', fontweight='bold')

plt.tight_layout()
plt.savefig('curve_B_castiron.png', dpi=200, bbox_inches='tight')
plt.close()
print("  curve_B_castiron.png saved")

# --- 报告B: 高分子曲线 ---
fig_poly, ax_poly = plt.subplots(figsize=(8, 6))
ax_poly.plot(poly_strain_shifted, poly_stress, 'b-', lw=0.6)
ax_poly.set_xlabel('工程应变 ε (%)')
ax_poly.set_ylabel('工程应力 σ (MPa)')
ax_poly.set_title('高分子(塑料)拉伸 工程应力-工程应变曲线')
ax_poly.grid(True, alpha=0.3)
ax_poly.set_xlim(left=-1)
ax_poly.set_ylim(bottom=-1)

# 标注σy
ax_poly.annotate(f'$\\sigma_y$={sigma_y_poly:.1f} MPa',
    xy=(poly_strain_shifted[poly_peak_idx], sigma_y_poly),
    xytext=(poly_strain_shifted[poly_peak_idx]+5, sigma_y_poly+3),
    arrowprops=dict(arrowstyle='->', color='blue', lw=1.2),
    fontsize=10, color='blue', fontweight='bold')

# 标注Rm(如果不同于σy)
Fm_idx_poly = np.argmax(poly_load)
if abs(Rm_poly - sigma_y_poly) > 1:
    ax_poly.annotate(f'$R_m$={Rm_poly:.1f} MPa',
        xy=(poly_strain_shifted[Fm_idx_poly], Rm_poly),
        xytext=(poly_strain_shifted[Fm_idx_poly]-10, Rm_poly+3),
        arrowprops=dict(arrowstyle='->', color='red', lw=1.2),
        fontsize=10, color='red', fontweight='bold')

# 标注断裂应变 εtb
last_valid = len(poly_strain_shifted) - 1
etb = poly_strain_shifted[last_valid]
ax_poly.annotate(f'$\\varepsilon_{{tb}}$={etb:.1f}%',
    xy=(poly_strain_shifted[last_valid], poly_stress[last_valid]),
    xytext=(poly_strain_shifted[last_valid]-15, poly_stress[last_valid]+5),
    arrowprops=dict(arrowstyle='->', color='green', lw=1),
    fontsize=9, color='green')

plt.tight_layout()
plt.savefig('curve_B_polymer.png', dpi=200, bbox_inches='tight')
plt.close()
print("  curve_B_polymer.png saved")

# --- 弹性模量曲线: 铝合金 ---
al_e_data = read_csv_data('铝合金弹性模量.csv')
fig_e_al, ax_e_al = plt.subplots(figsize=(8, 6))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
E_results_al = []
for gi, (gn, gd) in enumerate(al_e_data.items()):
    strain_h = [h for h in gd['_headers'] if '引伸计' in h and '应变' in h]
    load_h = [h for h in gd['_headers'] if '载荷' in h]
    if strain_h and load_h:
        s = gd[strain_h[0]]; l = gd[load_h[0]]
        # 线性拟合
        n = len(l); ss, ee = n//10, n-n//10
        if ee-ss > 10:
            c = np.polyfit(s[ss:ee], l[ss:ee], 1)
            E_val = c[0] / S0_al * 100 / 1000
            E_results_al.append(E_val)
            ax_e_al.plot(s, l, color=colors[gi%4], lw=0.8, 
                        label=f'第{gi+1}次 (E={E_val:.1f} GPa)')

ax_e_al.set_xlabel('引伸计应变 (%)'); ax_e_al.set_ylabel('载荷 F (N)')
ax_e_al.set_title('铝合金弹性模量测量-加载循环')
ax_e_al.legend(); ax_e_al.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('curve_A_elastic.png', dpi=200, bbox_inches='tight')
plt.close()
print("  curve_A_elastic.png saved")

# --- 弹性模量曲线: 铸铁 ---
ci_e_data = read_csv_data('铸铁弹性模量.csv')
fig_e_ci, ax_e_ci = plt.subplots(figsize=(8, 6))
E_results_ci = []
for gi, (gn, gd) in enumerate(ci_e_data.items()):
    strain_h = [h for h in gd['_headers'] if '引伸计' in h and '应变' in h]
    load_h = [h for h in gd['_headers'] if '载荷' in h]
    if strain_h and load_h:
        s = gd[strain_h[0]]; l = gd[load_h[0]]
        n = len(l); ss, ee = n//10, n-n//10
        if ee-ss > 10:
            c = np.polyfit(s[ss:ee], l[ss:ee], 1)
            E_val = c[0] / S0_ci * 100 / 1000
            E_results_ci.append(E_val)
            ax_e_ci.plot(s, l, color=colors[gi%4], lw=0.8,
                        label=f'第{gi+1}次 (E={E_val:.1f} GPa)')

ax_e_ci.set_xlabel('引伸计应变 (%)'); ax_e_ci.set_ylabel('载荷 F (N)')
ax_e_ci.set_title('铸铁弹性模量测量-加载循环')
ax_e_ci.legend(); ax_e_ci.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('curve_B_elastic.png', dpi=200, bbox_inches='tight')
plt.close()
print("  curve_B_elastic.png saved")

print("\n=== 所有曲线生成完毕 ===")
print(f"铝合金: Rp0.2={Rp02_al:.1f}MPa, Rm={Rm_al:.1f}MPa, E_avg={np.mean(E_results_al[1:]) if len(E_results_al)>1 else E_results_al[0]:.1f}GPa")
print(f"铸铁: Rm={Rm_ci:.1f}MPa, E_avg={np.mean(E_results_ci[1:]) if len(E_results_ci)>1 else E_results_ci[0]:.1f}GPa")
print(f"高分子: σy={sigma_y_poly:.1f}MPa, Rm={Rm_poly:.1f}MPa, εtb={etb:.1f}%")
