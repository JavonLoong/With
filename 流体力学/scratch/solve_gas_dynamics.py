import numpy as np

# Given parameters
gamma = 1.4

# Step 1: Incoming flow Mach number M1
# Mach wave angle mu_1 = 30 degrees
mu_1 = np.radians(30.0)
M1 = 1.0 / np.sin(mu_1)
print(f"M1 = {M1:.4f}")

# Step 2: Oblique shock at B
# Shock angle beta = 50 degrees
beta = np.radians(50.0)

# Check if M1 * sin(beta) > 1
Mn1 = M1 * np.sin(beta)
print(f"Mn1 = {Mn1:.4f}")

# Deflection angle theta from theta-beta-M relation
# tan(theta) = 2 * cot(beta) * (M1^2 * sin^2(beta) - 1) / (M1^2 * (gamma + cos(2*beta)) + 2)
numerator = 2.0 * (1.0 / np.tan(beta)) * (M1**2 * np.sin(beta)**2 - 1.0)
denominator = M1**2 * (gamma + np.cos(2.0 * beta)) + 2.0
tan_theta = numerator / denominator
theta = np.arctan(tan_theta)
theta_deg = np.degrees(theta)
print(f"theta = {theta_deg:.4f} degrees")

# Downstream of shock: State 2
# Normal Mach number before shock: Mn1 = M1 * sin(beta)
# Normal Mach number after shock: Mn2
Mn2 = np.sqrt((1.0 + 0.5 * (gamma - 1.0) * Mn1**2) / (gamma * Mn1**2 - 0.5 * (gamma - 1.0)))
print(f"Mn2 = {Mn2:.4f}")

# M2 = Mn2 / sin(beta - theta)
M2 = Mn2 / np.sin(beta - theta)
print(f"M2 = {M2:.4f}")

# Stagnation pressure ratio across shock: p02 / p01
# p02 / p01 = ( ((gamma+1)*Mn1^2 / ((gamma-1)*Mn1^2 + 2))^(gamma/(gamma-1)) ) * ( (gamma+1) / (2*gamma*Mn1^2 - (gamma-1)) )^(1/(gamma-1))
term1 = ((gamma + 1.0) * Mn1**2) / ((gamma - 1.0) * Mn1**2 + 2.0)
term2 = (gamma + 1.0) / (2.0 * gamma * Mn1**2 - (gamma - 1.0))
p02_p01 = (term1 ** (gamma / (gamma - 1.0))) * (term2 ** (1.0 / (gamma - 1.0)))
print(f"p02 / p01 = {p02_p01:.4f}")

# Static pressure ratio across shock: p2 / p1
p2_p1 = 1.0 + 2.0 * gamma / (gamma + 1.0) * (Mn1**2 - 1.0)
print(f"p2 / p1 = {p2_p1:.4f}")

# Step 3: Expansion fan at C
# Deflection angle is theta (flow turns back to horizontal)
# State 3 is after expansion. Stagnation pressure is conserved: p03 = p02.
# We have M2, and we expand by delta = theta.
# Prandtl-Meyer function nu(M) = sqrt((gamma+1)/(gamma-1)) * arctan(sqrt((gamma-1)/(gamma+1) * (M^2-1))) - arctan(sqrt(M^2-1))
def PM_func(M):
    l = np.sqrt((gamma + 1.0) / (gamma - 1.0))
    r = np.sqrt((gamma - 1.0) / (gamma + 1.0) * (M**2 - 1.0))
    return l * np.arctan(r) - np.arctan(np.sqrt(M**2 - 1.0))

nu_M2 = PM_func(M2)
nu_M3 = nu_M2 + theta
print(f"nu(M2) = {np.degrees(nu_M2):.4f} degrees")
print(f"nu(M3) = {np.degrees(nu_M3):.4f} degrees")

# Find M3 such that PM_func(M3) = nu_M3
# Simple numerical solver
from scipy.optimize import fsolve
def equation(M):
    return PM_func(M) - nu_M3

M3_guess = M2 + 0.5
M3 = fsolve(equation, M3_guess)[0]
print(f"M3 = {M3:.4f}")

# Stagnation pressure p03 / p3 for State 3:
# p03 / p3 = (1 + 0.5 * (gamma - 1) * M3^2) ^ (gamma / (gamma - 1))
p03_p3 = (1.0 + 0.5 * (gamma - 1.0) * M3**2) ** (gamma / (gamma - 1.0))
print(f"p03 / p3 = {p03_p3:.4f}")

# Since p3 = 1e5 Pa, we get p03
p3 = 1.0e5
p03 = p3 * p03_p3
print(f"p03 = {p03:.4f} Pa")

# Stagnation pressure of incoming flow: p01 = p03 / (p02/p01) since p03 = p02
p01 = p03 / p02_p01
print(f"p01 = {p01:.4f} Pa")
print(f"p01 = {p01 / 1e5:.4f} * 10^5 Pa")
