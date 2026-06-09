"""
分析52组低碳钢数据：弹性模量 + 破坏拉伸
"""
import csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
rcParams['axes.unicode_minus'] = False

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

# ============ 3. 绘图 ============
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

axes[0].plot(strain_pct, stress, 'b-', lw=0.5)
axes[0].set_xlabel('工程应变 ε (%)'); axes[0].set_ylabel('工程应力 σ (MPa)')
axes[0].set_title('52组 低碳钢拉伸 应力-应变曲线'); axes[0].grid(True, alpha=0.3)
axes[0].annotate(f'$R_{{eH}}$={ReH:.0f}MPa', xy=(strain_pct[FeH_idx], ReH),
    xytext=(strain_pct[FeH_idx]+3, ReH+20), arrowprops=dict(arrowstyle='->', color='red'),
    fontsize=9, color='red')
axes[0].annotate(f'$R_m$={Rm:.0f}MPa', xy=(strain_pct[Fm_idx], Rm),
    xytext=(strain_pct[Fm_idx]-8, Rm+20), arrowprops=dict(arrowstyle='->', color='darkred'),
    fontsize=9, color='darkred')

# 右: 弹性段放大
zoom_end = min(ye + 2000, N)
axes[1].plot(strain_pct[:zoom_end], stress[:zoom_end], 'b-', lw=0.8)
axes[1].set_xlabel('工程应变 ε (%)'); axes[1].set_ylabel('工程应力 σ (MPa)')
axes[1].set_title('弹性段与屈服平台'); axes[1].grid(True, alpha=0.3)
axes[1].axhline(y=ReH, color='r', ls='--', alpha=0.5, label=f'$R_{{eH}}$={ReH:.0f}MPa')
axes[1].axhline(y=ReL, color='orange', ls='--', alpha=0.5, label=f'$R_{{eL}}$={ReL:.0f}MPa')
axes[1].legend(fontsize=9)

plt.tight_layout()
plt.savefig('52_steel_stress_strain.png', dpi=200, bbox_inches='tight')
print("\n52_steel_stress_strain.png saved")

# 弹性模量循环
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
