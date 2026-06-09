"""
分析52组低碳钢数据：弹性模量 + 破坏拉伸
v2: 加入坐标平移处理，完善标注(ReH/ReL/Rm)
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

def coordinate_shift(strain, stress):
    """
    坐标平移：低载非线性段线性化
    1. 找弹性段的线性部分
    2. 做线性拟合
    3. 拟合直线与横轴交点 → 新原点
    4. 应变减去偏移量
    """
    max_stress = np.max(stress)
    peak_idx = np.argmax(stress)
    
    # 弹性段：取应力从10%到50%最大应力的区间
    s_low = 0.10 * max_stress
    s_high = 0.50 * max_stress
    
    mask = (stress > s_low) & (stress < s_high) & (np.arange(len(stress)) < peak_idx)
    if np.sum(mask) < 10:
        s_low = 0.05 * max_stress
        s_high = 0.60 * max_stress
        mask = (stress > s_low) & (stress < s_high) & (np.arange(len(stress)) < peak_idx)
    
    if np.sum(mask) < 5:
        return strain, 0
    
    strain_fit = strain[mask]
    stress_fit = stress[mask]
    
    # 线性拟合: stress = k * strain + b
    coeffs = np.polyfit(strain_fit, stress_fit, 1)
    k, b = coeffs
    
    # 拟合直线与横轴交点: 0 = k * strain_0 + b => strain_0 = -b/k
    strain_offset = -b / k if k != 0 else 0
    
    shifted_strain = strain - strain_offset
    return shifted_strain, strain_offset

d0 = 5.0; L0 = 25.0; S0 = np.pi * d0**2 / 4; Lc = 70.0
print(f"试件: d0={d0}mm, L0={L0}mm, S0={S0:.2f}mm2, Lc={Lc}mm")

# ============ 1. 弹性模量 ============
print("\n=== 弹性模量 ===")
with open('52低碳钢wn.csv', 'r', encoding='gbk') as f:
    reader = csv.reader(f)
    row0 = next(reader); row1 = next(reader); row2 = next(reader)
    group_names = [row0[i] for i in range(0, len(row0), 6) if row0[i]]
    data = {g: {'load': [], 'ext_strain': []} for g in group_names}
    for row in reader:
        for gi, g in enumerate(group_names):
            b = gi * 6
            try:
                data[g]['load'].append(float(row[b+1]))
                data[g]['ext_strain'].append(float(row[b+4]))
            except (ValueError, IndexError): pass

E_results = []
for g in group_names:
    ld = np.array(data[g]['load']); st = np.array(data[g]['ext_strain'])
    n = len(ld); s, e = n//10, n - n//10
    if e - s > 10:
        c = np.polyfit(st[s:e], ld[s:e], 1); slope = c[0]
        E = slope / S0 * 100 / 1000
        E_results.append({'name': g, 'slope': slope, 'E': E,
            'load_range': f"{ld[s]:.0f}~{ld[e-1]:.0f}",
            'strain_range': f"{st[s]:.4f}~{st[e-1]:.4f}"})
        print(f"  {g}: slope={slope:.0f}, E={E:.1f}GPa")

E_vals = [r['E'] for r in E_results]
if len(E_vals) >= 3 and abs(E_vals[0] - np.mean(E_vals[1:])) / np.mean(E_vals[1:]) > 0.05:
    E_avg = np.mean(E_vals[1:])
    print(f"  第1次偏差大, 取后{len(E_vals)-1}次均值")
else:
    E_avg = np.mean(E_vals)
print(f"  E = {E_avg:.1f} GPa")

# ============ 2. 破坏拉伸 ============
print("\n=== 破坏拉伸 ===")
load_list, stroke_list = [], []
with open('52低碳钢破坏wn.csv', 'r', encoding='gbk') as f:
    reader = csv.reader(f)
    for _ in range(3): next(reader)
    for row in reader:
        try:
            load_list.append(float(row[1]))
            stroke_list.append(float(row[2]))
        except (ValueError, IndexError): pass

load_arr = np.array(load_list)
stroke_arr = np.array(stroke_list)
N = len(load_arr)
print(f"  数据点: {N}")

stress = load_arr / S0
strain_pct = stroke_arr / Lc * 100  # 行程/Lc做应变

# ★ 坐标平移 ★
strain_shifted, shift_offset = coordinate_shift(strain_pct, stress)
print(f"  坐标平移偏移量: {shift_offset:.4f}%")

Fm = np.max(load_arr); Rm = Fm / S0; Fm_idx = np.argmax(load_arr)
print(f"  Fm={Fm:.1f}N ({Fm/1000:.3f}kN), Rm={Rm:.1f}MPa")

# 上下屈服点
search_end = min(N // 3, 10000)
win = 50
ss = np.convolve(stress, np.ones(win)/win, mode='same')
el_end = 0
for i in range(N):
    if strain_pct[i] > 0.3: el_end = i; break

FeH_idx = el_end + np.argmax(ss[el_end:search_end])
FeH = load_arr[FeH_idx]; ReH = stress[FeH_idx]
print(f"  FeH={FeH:.1f}N ({FeH/1000:.3f}kN), ReH={ReH:.1f}MPa")

ys, ye = FeH_idx, min(FeH_idx + 5000, search_end)
FeL_idx = ys + np.argmin(ss[ys:ye])
FeL = load_arr[FeL_idx]; ReL = stress[FeL_idx]
print(f"  FeL={FeL:.1f}N ({FeL/1000:.3f}kN), ReL={ReL:.1f}MPa")

# ============ 3. 绘图（使用平移后的应变） ============
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 左: 完整曲线（坐标平移后）
axes[0].plot(strain_shifted, stress, 'b-', lw=0.5)
axes[0].set_xlabel('工程应变 ε (%)')
axes[0].set_ylabel('工程应力 σ (MPa)')
axes[0].set_title('低碳钢拉伸 工程应力-工程应变曲线（坐标平移后）')
axes[0].grid(True, alpha=0.3)
axes[0].set_xlim(left=-0.5)
axes[0].set_ylim(bottom=-10)

# 标注 ReH
axes[0].annotate(f'$R_{{eH}}$={ReH:.0f} MPa',
    xy=(strain_shifted[FeH_idx], ReH),
    xytext=(strain_shifted[FeH_idx]+3, ReH+30),
    arrowprops=dict(arrowstyle='->', color='red', lw=1.2),
    fontsize=10, color='red', fontweight='bold')

# 标注 ReL
axes[0].annotate(f'$R_{{eL}}$={ReL:.0f} MPa',
    xy=(strain_shifted[FeL_idx], ReL),
    xytext=(strain_shifted[FeL_idx]+5, ReL-40),
    arrowprops=dict(arrowstyle='->', color='orange', lw=1.2),
    fontsize=10, color='orange', fontweight='bold')

# 标注 Rm
axes[0].annotate(f'$R_m$={Rm:.0f} MPa',
    xy=(strain_shifted[Fm_idx], Rm),
    xytext=(strain_shifted[Fm_idx]-8, Rm+20),
    arrowprops=dict(arrowstyle='->', color='darkred', lw=1.2),
    fontsize=10, color='darkred', fontweight='bold')

# 右: 弹性段+屈服平台放大（坐标平移后）
zoom_end = min(ye + 2000, N)
axes[1].plot(strain_shifted[:zoom_end], stress[:zoom_end], 'b-', lw=0.8)
axes[1].set_xlabel('工程应变 ε (%)')
axes[1].set_ylabel('工程应力 σ (MPa)')
axes[1].set_title('弹性段与屈服平台（坐标平移后）')
axes[1].grid(True, alpha=0.3)
axes[1].axhline(y=ReH, color='r', ls='--', alpha=0.5, label=f'$R_{{eH}}$={ReH:.0f} MPa')
axes[1].axhline(y=ReL, color='orange', ls='--', alpha=0.5, label=f'$R_{{eL}}$={ReL:.0f} MPa')
axes[1].legend(fontsize=9)

plt.tight_layout()
plt.savefig('52_steel_stress_strain.png', dpi=200, bbox_inches='tight')
print("\n52_steel_stress_strain.png saved (with coordinate shift)")

# 弹性模量循环图
fig2, ax = plt.subplots(figsize=(8, 6))
colors = ['blue', 'red', 'green']
for gi, g in enumerate(group_names):
    s = np.array(data[g]['ext_strain']); l = np.array(data[g]['load'])
    ax.plot(s, l, color=colors[gi%3], lw=0.8, label=f'{g} (E={E_results[gi]["E"]:.1f}GPa)')
ax.set_xlabel('引伸计应变 (%)'); ax.set_ylabel('载荷 F (N)')
ax.set_title('52组 低碳钢弹性模量测量'); ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('52_steel_elastic_modulus.png', dpi=200, bbox_inches='tight')
print("52_steel_elastic_modulus.png saved")

# ============ 4. 汇总 ============
results = {
    'd0': d0, 'L0': L0, 'S0': round(S0,2), 'Lc': Lc, 'E_GPa': round(E_avg,1),
    'shift_offset_pct': round(shift_offset, 4),
    'E_groups': [{'name':r['name'], 'slope':round(r['slope'],0), 'E':round(r['E'],1),
                  'load_range':r['load_range'], 'strain_range':r['strain_range']} for r in E_results],
    'FeH_N': round(FeH,1), 'ReH_MPa': round(ReH,1),
    'FeL_N': round(FeL,1), 'ReL_MPa': round(ReL,1),
    'Fm_N': round(Fm,1), 'Rm_MPa': round(Rm,1),
}
with open('52_steel_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nResults saved to 52_steel_results.json")
print(json.dumps(results, ensure_ascii=False, indent=2))
