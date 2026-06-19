import numpy as np

# Coefficients: Ma^6 + 15 Ma^4 + 75 Ma^2 - 302.4 Ma + 125 = 0
# numpy.roots needs: [1, 0, 15, 0, 75, -302.4, 125]
coeffs = [1, 0, 15, 0, 75, -302.4, 125]

roots = np.roots(coeffs)

print("All roots:")
for i, r in enumerate(roots):
    print(f"Root {i+1}: {r}")

print("\nReal roots:")
real_roots = []
for r in roots:
    if np.isreal(r) or abs(r.imag) < 1e-9:
        real_roots.append(r.real)
        print(r.real)
