# Pump calculation
g = 9.81
rho = 1000
Q = 50.0 / 3600
D = 0.1
A = 3.1415926535 * D**2 / 4
V = Q / A
Re = V * D / 1e-6
# Haaland for lambda
import math
inv_sqrt_lambda = -1.8 * math.log10((0.0015/3.7)**1.11 + 6.9/Re)
lmbda = 1.0 / inv_sqrt_lambda**2
hf = lmbda * (6.0/D) * (V**2 / (2*g))
h_local = (0.29 + 2.5) * (V**2 / (2*g)) # Wait, is entrance loss zeta_in = 0.5 or something included? 
# In extracted text: "弯头 \zeta=0.29，入口阀 \zeta=2.5"
# Let's see:
p_a = 101.3 * 1000
p_v = 19.6 * 1000
p_safe = 20.0 * 1000
p_B = p_v + p_safe
h_max = (p_a - p_B)/(rho * g) - (V**2 / (2*g)) - hf - h_local
print(f"V: {V:.4f}")
print(f"Re: {Re:.1f}")
print(f"lambda: {lmbda:.5f}")
print(f"hf: {hf:.4f}")
print(f"h_local: {h_local:.4f}")
print(f"V^2/(2g): {V**2 / (2*g):.4f}")
print(f"h_max: {h_max:.4f}")
