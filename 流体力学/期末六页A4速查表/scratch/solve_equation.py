import numpy as np

# Coefficients of the polynomial: m^6 + 15m^4 + 75m^2 - 176.4m + 125 = 0
# Order of coefficients in numpy.roots: from highest degree to lowest (m^6, m^5, m^4, m^3, m^2, m^1, m^0)
coeffs = [1, 0, 15, 0, 75, -176.4, 125]

roots = np.roots(coeffs)

print("All roots:")
for i, r in enumerate(roots):
    print(f"Root {i+1}: {r}")

print("\nReal roots:")
for r in roots:
    if np.isreal(r) or abs(r.imag) < 1e-9:
        print(r.real)
