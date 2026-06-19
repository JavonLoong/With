import math

# 1. Pump Cavitation Problem
Q = 50 / 3600 # m3/s
D = 0.1 # m
A = math.pi * D**2 / 4
V = Q / A
g = 9.81
rho = 1000
nu = 1.0e-6 # m2/s
Re = V * D / nu
e_d = 0.15 / 100.0

# Haaland equation for Darcy friction factor
inv_sqrt_lambda = -1.8 * math.log10( (e_d / 3.7)**1.11 + 6.9 / Re )
lam = 1.0 / (inv_sqrt_lambda**2)

L = 6 # m
zeta_bend = 0.29
zeta_valve = 2.5
zeta_in = 0.5 # standard sharp entrance
sum_zeta = zeta_bend + zeta_valve + zeta_in

h_f = lam * (L / D) * (V**2 / (2 * g))
h_local = sum_zeta * (V**2 / (2 * g))
h_L = h_f + h_local

p_a = 101.3e3
p_v = 19.6e3
p_safe = 20.0e3

# p_2_min = p_v + p_safe
p_2_min = p_v + p_safe # 39.6e3 Pa

# Bernoulli from reservoir (z1=0, p1=p_a, V1=0) to pump inlet (z2=h, p2=p_2_min, V2=V)
# p_a / (rho*g) + 0 = p_2_min / (rho*g) + h + V^2/(2*g) + h_L
# h = (p_a - p_2_min) / (rho*g) - (1 + sum_zeta + lam * L / D) * V^2 / (2*g) + inlet? Wait, the h_L already contains entrance loss.
# Wait, water level to pump inlet:
# p_a / (rho*g) = p_2 / (rho*g) + h + V^2/(2*g) + h_L
# h = (p_a - p_2_min) / (rho*g) - V^2/(2*g) - h_L
# Let's compute:
h_max = (p_a - p_2_min) / (rho * g) - (V**2 / (2 * g)) - h_L

print("=== PUMP CAVITATION ===")
print(f"V = {V:.3f} m/s")
print(f"Re = {Re:.1e}")
print(f"lam = {lam:.4f}")
print(f"h_f = {h_f:.3f} m")
print(f"h_local = {h_local:.3f} m")
print(f"h_L = {h_L:.3f} m")
print(f"h_max = {h_max:.3f} m")

# 2. Hydraulic Turbine Problem
# D1 = 0.2 m, L1 = 30 m, V1 = 2 m/s
# D2 = 0.3 m, L2 = 15 m
# nu = 1.3e-6, e = 0.25 mm
D1 = 0.2
L1 = 30
V1 = 2
Q_t = (math.pi * D1**2 / 4) * V1
D2 = 0.3
L2 = 15
V2 = Q_t / (math.pi * D2**2 / 4)

Re1 = V1 * D1 / 1.3e-6
Re2 = V2 * D2 / 1.3e-6
e_d1 = 0.25e-3 / D1
e_d2 = 0.25e-3 / D2

lam1 = 1.0 / (-1.8 * math.log10( (e_d1 / 3.7)**1.11 + 6.9 / Re1 ))**2
lam2 = 1.0 / (-1.8 * math.log10( (e_d2 / 3.7)**1.11 + 6.9 / Re2 ))**2

h_f1 = lam1 * (L1 / D1) * (V1**2 / (2 * g))
h_f2 = lam2 * (L2 / D2) * (V2**2 / (2 * g))
h_L_tot = h_f1 + h_f2

# From upstream reservoir (z1 = H, p1 = 0, V1 = 0) to pressure gauge section (z2 = 0, p2 = 70 kPa, V2 = V2)
# Wait, what are the elevations? "斜管L=30m,水平管L=15m...下游压力表70kPa"
# Wait, let's assume the reservoir level is H above the pressure gauge section.
# Bernoulli: z_res + 0 + 0 = z_gauge + p2/(rho*g) + V2^2/(2*g) + H_T + h_L_tot
# If z_res - z_gauge = H_elevation? Or is it a known elevation difference?
# Wait! Let's check if there is an elevation difference in the problem. "斜管L=30m,水平管L=15m...斜管平均速度2m/s,压力表70kPa"
# Wait, let's see. Let's print the turbine problem from v21 with python search to check the details.
