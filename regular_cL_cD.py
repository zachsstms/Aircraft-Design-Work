import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

CD_min = 0.009649090909
t = 640/(6940+540)
u = 1
AR = 20.45  
r = 0.38

denom_frac = 1 / ((1+0.03*t - 2*t**2)*u)
e = 0.85
#1 / (np.pi*AR*r*CD_min + denom_frac)
rho = 1.225
WL = 408 *9.81 /11

V = np.linspace(1, 600, 10000)

CL = WL/(0.5*rho*V**2)

CD = CD_min + (CL**2)/(np.pi*AR*e)

L_D = CL/CD
best_index_1 = np.argmax(L_D)
best_V1 = V[best_index_1]
best_CL1 = CL[best_index_1]
best_CD1 = CD[best_index_1]
best_L_D1 = L_D[best_index_1]

plt.figure(figsize=(10, 6))
plt.plot(CD,CL, label='Drag Coefficient (CD)', color='blue')
plt.plot(
    [0, best_CD1],
    [0, best_CL1],
    '--',
    color='black',
    label=f'Tangent from origin (L/D = {best_L_D1:.2f})',
)
plt.scatter(best_CD1, best_CL1, color='black', zorder=3)
plt.xlabel('$C_D$')
plt.ylabel('$C_L$')
plt.xlim(0, 0.1)
plt.ylim(0, 1.5)
plt.grid()
plt.legend()
plt.show(block=False)

# part 2

CD_min2 = 0.0106468693
WL2 = 352*9.81/8
AR2 = 15
e2 = .85
# 1 / (np.pi*AR2*r*CD_min2 + denom_frac)
CL2 = WL2/(0.5*rho*V**2)

CD2 = CD_min2 + (CL2**2)/(np.pi*AR2*e2)

L_D2 = CL2/CD2
best_index = np.argmax(L_D2)
best_V2 = V[best_index]
best_CL2 = CL2[best_index]
best_CD2 = CD2[best_index]
best_L_D2 = L_D2[best_index]

plt.figure(figsize=(10, 6))
plt.plot(CD2,CL2, label='Drag Coefficient (CD) - Part 2', color='red')
plt.plot(
    [0, best_CD2],
    [0, best_CL2],
    '--',
    color='black',
    label=f'Tangent from origin (L/D = {best_L_D2:.2f})',
)
plt.scatter(best_CD2, best_CL2, color='black', zorder=3)
plt.xlabel('$C_D$')
plt.ylabel('$C_L$')
plt.xlim(0, 0.1)
plt.ylim(0, 1.5)
plt.grid()
plt.legend()
plt.show(block=False)

print(f'Part 1 best L/D: {best_L_D1:.3f}')
print(f'Part 1 at V = {best_V1:.3f}, CL = {best_CL1:.5f}, CD = {best_CD1:.5f}')
print(f'Part 2 best L/D: {best_L_D2:.3f}')
print(f'Part 2 at V = {best_V2:.3f}, CL = {best_CL2:.5f}, CD = {best_CD2:.5f}')

plt.show()
