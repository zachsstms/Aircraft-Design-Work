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
    initial_sweep = np.deg2rad(np.atan((C_root-C_tip) * (b/2))) # just the sweep you get from a traditional trapezoidal wing, not the leading edge sweep, which is a design choice
    C_bar = (2/3) * C_root * ((1 + taper_ratio + taper_ratio**2) / (1 + taper_ratio)) # also MGC in gudmunsson book
    Y_bar = (b / 6) * ((1 + 2*taper_ratio) / (1 + taper_ratio))
    X_bar = Y_bar*np.tan(np.deg2rad(initial_sweep)) + datumX  # Assuming 0 degrees of sweep, this is from the datum to the leading 
    
    return b, C_root, C_tip, C_bar, Y_bar, X_bar, initial_sweep

stuff = trapezoidal_wing_geometry(AR=10, S=S, taper_ratio=0.55)
print("b, C_root, C_tip, C_bar, Y_bar, X_bar, initial_sweep:", stuff)


