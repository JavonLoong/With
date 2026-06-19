# Nozzle bolt calculation
import math
D1 = 0.20
D2 = 0.10
p1_abs = 345.0 * 1000
p_a = 103.4 * 1000
V2 = 22.0
rho = 1000

# 1. Areas
A1 = math.pi * D1**2 / 4
A2 = math.pi * D2**2 / 4

# 2. V1 by continuity
V1 = A2 * V2 / A1
Q = A2 * V2
m_dot = rho * Q

# 3. Pressures
p1_g = p1_abs - p_a # gauge pressure at inlet
p2_g = 0.0 # gauge pressure at outlet

# 4. Momentum equation: R_x + p1_g*A1 - p2_g*A2 = m_dot * (V2 - V1)
# Wall force on fluid:
R_x = m_dot * (V2 - V1) - p1_g * A1

# Fluid force on wall:
F_fluid = -R_x

print(f"A1: {A1:.5f}, A2: {A2:.5f}")
print(f"V1: {V1:.4f}")
print(f"Q: {Q:.5f}")
print(f"p1_g: {p1_g/1000:.1f} kPa")
print(f"R_x: {R_x:.1f} N")
print(f"F_fluid: {F_fluid:.1f} N")
