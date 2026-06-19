import numpy as np

# Inputs
T0 = 400.0       # K
p0 = 300.0 * 10**3 # Pa (300 kPa)
At = 0.05        # m^2
A1 = 0.07        # m^2
R = 287.0        # J/(kg*K)
gamma = 1.4

# 1. Mach number before shock (Ma1 = 1.7632)
Ma1 = 1.7632

# 2. Static temperature before shock T1
T1 = T0 / (1 + 0.2 * Ma1**2)
print(f"1. 波前静温 T1 = 400 / (1 + 0.2 * 1.7632^2) = {T1:.4f} K")

# 3. Static pressure before shock p1
p1 = p0 / ((1 + 0.2 * Ma1**2)**3.5)
print(f"2. 波前静压 p1 = 300000 / (1 + 0.2 * 1.7632^2)^3.5 = {p1:.2f} Pa (即 {p1/1000:.3f} kPa)")

# 4. Density before shock rho1
rho1 = p1 / (R * T1)
print(f"3. 波前密度 rho1 = p1 / (R * T1) = {rho1:.4f} kg/m^3")

# Alternate formula for rho1: rho1 = rho0 / (1 + 0.2 * Ma1^2)^2.5
rho0 = p0 / (R * T0)
rho1_alt = rho0 / ((1 + 0.2 * Ma1**2)**2.5)
print(f"   验证直接计算波前密度 rho1 = {rho1_alt:.4f} kg/m^3")

# 5. User's sub-expressions:
# Sub-expression 1: 300 * (7 * 1.7632^2 - 1) / 6
p2_ratio = (7 * Ma1**2 - 1) / 6
p2 = p1 * p2_ratio
print(f"\n4. 波后静压比 p2/p1 = (7 * 1.7632^2 - 1) / 6 = {p2_ratio:.4f}")
print(f"   波后静压 p2 = p1 * {p2_ratio:.4f} = {p2/1000:.3f} kPa")

# Sub-expression 2: Ma2 calculation
Ma2_sq = (1 + 0.2 * Ma1**2) / (1.4 * Ma1**2 - 0.2)
Ma2 = np.sqrt(Ma2_sq)
print(f"5. 波后马赫数 Ma2 = sqrt((1 + 0.2 * 1.7632^2)/(1.4 * 1.7632^2 - 0.2)) = {Ma2:.4f}")

# Sub-expression 3: Total pressure after shock p02
p02 = p2 * (1 + 0.2 * Ma2**2)**3.5
print(f"6. 波后总压 p02 = p2 * (1 + 0.2 * Ma2^2)^3.5 = {p02/1000:.3f} kPa")

# Let's compute the user's expression:
# 248.6 * 10^3 / (287 * T1)
# Wait, user said: "248点6×10的三次方除以一个数，这个数是287同意。26.69。" (287乘以某个数，那个数是 T1 = 246.69?)
# Let's print out 287 * T1
print(f"7. 287 * T1 = {287 * T1:.2f}")
print(f"   248.6 * 10^3 / (287 * T1) = {248600.0 / (287 * T1):.4f}")
