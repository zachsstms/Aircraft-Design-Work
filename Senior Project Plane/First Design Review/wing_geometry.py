import numpy as np

# Raymer Book give trapezoidal wing geomtry stuff

# Nomenclature:
# b = span
# S = area
# AR = aspect ratio
# C_root = root chord
# C_tip = tip chord
# C_bar = MAC
# Y_bar = spanwise location of MAC starting from the root chord/datum
# X_bar = longitudinal location of MAC starting from the datum

S = 600 #ft^2

# assume 0.55 for now, from gudmundsson book for atr
taper_ratio = 0.55

# can decide sweep later, assume no additional sweep
# assume the datum is at the front center of aircraft, so the root chord is at y = 0 and the tip chord is at y = +/- b/2
datumX = 0

def trapezoidal_wing_geometry(AR, S, taper_ratio):
    b = (AR * S) ** 0.5
    C_root = (2*S) / (b * (1 + taper_ratio))
    C_tip = C_root * taper_ratio
    initial_sweep = np.atan((C_root - C_tip) / (b / 2)) # sweep caused by taper, not an additional design sweep
    C_bar = (2/3) * C_root * ((1 + taper_ratio + taper_ratio**2) / (1 + taper_ratio)) # also MGC in gudmunsson book
    Y_bar = (b / 6) * ((1 + 2*taper_ratio) / (1 + taper_ratio))
    X_bar = Y_bar * np.tan(initial_sweep) + datumX  # initial_sweep is already in radians
    
    return b, C_root, C_tip, C_bar, Y_bar, float(X_bar), np.rad2deg(float(initial_sweep))

b, C_root, C_tip, C_bar, Y_bar, X_bar, initial_sweep = (
    trapezoidal_wing_geometry(AR=10, S=S, taper_ratio=taper_ratio)
)

print(f"Span (b): {b:.3f} ft")
print(f"Root chord (C_root): {C_root:.3f} ft")
print(f"Tip chord (C_tip): {C_tip:.3f} ft")
print(f"Mean aerodynamic chord (C_bar): {C_bar:.3f} ft")
print(f"MAC spanwise location (Y_bar): {Y_bar:.3f} ft")
print(f"MAC longitudinal location (X_bar): {X_bar:.3f} ft")
print(f"Leading edge sweep: {initial_sweep:.6f} degrees")



