# Turbine calculation
import math
g = 9.81
rho = 1000
D1 = 0.20
L1 = 30.0
D2 = 0.30
L2 = 15.0
nu = 1.3e-6
e = 0.25e-3
V1 = 2.0 # inclined pipe velocity is 2.0 m/s
A1 = math.pi * D1**2 / 4
Q = A1 * V1
A2 = math.pi * D2**2 / 4
V2 = Q / A2

Re1 = V1 * D1 / nu
Re2 = V2 * D2 / nu

# Haaland for lambda
def get_lambda(Re, e_d):
    inv = -1.8 * math.log10((e_d/3.7)**1.11 + 6.9/Re)
    return 1.0 / inv**2

lmbda1 = get_lambda(Re1, e/D1)
lmbda2 = get_lambda(Re2, e/D2)

hf1 = lmbda1 * (L1/D1) * (V1**2 / (2*g))
hf2 = lmbda2 * (L2/D2) * (V2**2 / (2*g))
hf = hf1 + hf2

p_out_g = 70.0 * 1000 # 70 kPa gauge pressure at outlet
H_T = 15.0 - p_out_g/(rho*g) - (V2**2 / (2*g)) - hf # z1 - z2 = 15m. Wait, let's check: EGL_in - EGL_out - hf = H_T
# Inlet EGL = z1 = 15m (relative to outlet).
# Outlet EGL = z2 + p2/(rho g) + V2^2/(2g) = 0 + 70000/(1000*9.81) + V2^2/(2g)
# So H_T = 15 - 7.136 - V2^2/(2g) - hf

P_water = rho * g * Q * H_T
P_shaft = 0.85 * P_water # assuming efficiency 0.85

print(f"Q: {Q:.5f}")
print(f"V2: {V2:.4f}")
print(f"Re1: {Re1:.1f}, lambda1: {lmbda1:.5f}, hf1: {hf1:.4f}")
print(f"Re2: {Re2:.1f}, lambda2: {lmbda2:.5f}, hf2: {hf2:.4f}")
print(f"hf: {hf:.4f}")
print(f"H_T: {H_T:.4f}")
print(f"P_water: {P_water:.1f} W")
print(f"P_shaft: {P_shaft:.1f} W")
