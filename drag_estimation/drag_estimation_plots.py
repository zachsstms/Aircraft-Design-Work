import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

CD_min = 0.009712727273
t = 640/(6940+540)
u = 1
AR = 20.45  
r = 0.38

denom_frac = 1 / ((1+0.03*t - 2*t**2)*u)
e = 1 / (np.pi*AR*r*CD_min + denom_frac)
rho = 1.225
WL = 37.1 * 9.81 

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
plt.savefig('part1_drag_polar.png', dpi=300, bbox_inches='tight')

# part 2

CD_min2 = 0.0107343693
WL2 = 352*9.81/8
AR2 = 15
e2 = 1 / (np.pi*AR2*r*CD_min2 + denom_frac)
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
plt.savefig('part2_drag_polar.png', dpi=300, bbox_inches='tight')
plt.show(block=False)

print(f'Part 1 best L/D: {best_L_D1:.3f}')
print(f'Part 1 at V = {best_V1:.3f}, CL = {best_CL1:.5f}, CD = {best_CD1:.5f}')
print(f'Part 2 best L/D: {best_L_D2:.3f}')
print(f'Part 2 at V = {best_V2:.3f}, CL = {best_CL2:.5f}, CD = {best_CD2:.5f}')

def sink_rate_curve(CD0, AR, e, mass_kg, S, rho=1.225, CL_max=1.5):
    W = mass_kg * 9.81
    V = np.linspace(10, 65, 2000)       # m/s
    CL = W / (0.5 * rho * V**2 * S)
    CD = CD0 + CL**2 / (np.pi * AR * e)

    # Only show the pre-stall portion of the curve.
    valid = CL <= CL_max
    V, CL, CD = V[valid], CL[valid], CD[valid]

    # Vertical speed required to balance the drag (positive downward).
    sink = V * CD / CL  # m/s
    i_sink = np.argmin(sink)
    i_glide = np.argmax(CL / CD)

    return V, sink, i_sink, i_glide


V1, sink1, i_sink1, i_glide1 = sink_rate_curve(
    CD_min, AR, e, mass_kg=408, S=11
)

V2, sink2, i_sink2, i_glide2 = sink_rate_curve(
    CD_min2, AR2, e2, mass_kg=352, S=8
)

plt.figure(figsize=(10, 6))
plt.plot(V1 * 3.6, sink1, label="Part 1: ASW-19 baseline", color="blue")


data = pd.read_csv("asw19_digitized_speed_polar.csv")

polar31 = data[data["wing_loading_kg_m2"] == 31]
polar37 = data[data["wing_loading_kg_m2"] == 37]

plt.plot(
    polar31["speed_kmh"],
    polar31["sink_ms"],
    "--",
    label="Published ASW 19 - 31 kg/m²"
)

plt.plot(
    polar37["speed_kmh"],
    polar37["sink_ms"],
    "-",
    label="Published ASW 19 - 37 kg/m²"
)

best_speed_1_kmh = V1[i_glide1] * 3.6
best_sink_1 = sink1[i_glide1]
plt.scatter(best_speed_1_kmh, best_sink_1, color='black', zorder=3)
plt.annotate(
    f'Best L/D = {best_L_D1:.2f}',
    (best_speed_1_kmh, best_sink_1),
    textcoords='offset points',
    xytext=(8, 8),
    fontsize=9,
)

plt.gca().yaxis.set_inverted(True)
plt.xlabel("True airspeed, V (km/h)")
plt.ylabel("Sink rate (m/s downward)")
plt.grid(True)
plt.legend()
plt.savefig("part1_speed_polar.png", dpi=300, bbox_inches="tight")
plt.show(block=False)

plt.figure(figsize=(10, 6))
plt.plot(V1 * 3.6, sink1, label="Part 1: ASW-19 baseline", color="blue")
plt.plot(V2 * 3.6, sink2, label="Part 2: S = 8 m², AR = 15", color="red")

best_speed_1_kmh = V1[i_glide1] * 3.6
best_sink_1 = sink1[i_glide1]
best_speed_2_kmh = V2[i_glide2] * 3.6
best_sink_2 = sink2[i_glide2]

plt.scatter(best_speed_1_kmh, best_sink_1, color='black', zorder=3)
plt.annotate(
    f'Part 1 best L/D = {best_L_D1:.2f}',
    (best_speed_1_kmh, best_sink_1),
    textcoords='offset points',
    xytext=(8, 8),
    fontsize=9,
)

plt.scatter(best_speed_2_kmh, best_sink_2, color='black', zorder=3)
plt.annotate(
    f'Part 2 best L/D = {best_L_D2:.2f}',
    (best_speed_2_kmh, best_sink_2),
    textcoords='offset points',
    xytext=(8, 8),
    fontsize=9,
)

plt.gca().yaxis.set_inverted(True)
plt.xlabel("True airspeed, V (km/h)")
plt.ylabel("Sink rate (m/s downward)")
plt.grid(True)
plt.legend()
plt.savefig("part2_speed_polar.png", dpi=300, bbox_inches="tight")
plt.show(block=False)

print(f"Part 1 minimum sink: {sink1[i_sink1]:.3f} m/s "
    f"at {V1[i_sink1] * 3.6:.1f} km/h")
print(f"Part 1 best glide speed: {V1[i_glide1] * 3.6:.1f} km/h")

print(f"Part 2 minimum sink: {sink2[i_sink2]:.3f} m/s "
    f"at {V2[i_sink2] * 3.6:.1f} km/h")
print(f"Part 2 best glide speed: {V2[i_glide2] * 3.6:.1f} km/h")

plt.show()