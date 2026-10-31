import numpy as np

# Raymer Book give trapezoidal wing geomtry stuff

# Nomenclature:
# b = span
# S = area
# AR = aspect ratio (assumed)
# C_root = root chord
# C_tip = tip chord
# C_bar = MAC
# Y_bar = spanwise location of MAC starting from the root chord/datum
# X_bar = longitudinal location of MAC starting from the datum

S_wing = 471.3 #ft^2

# assume 0.5 for dash 8
taper_ratio = 0.5 # assumed

# can decide sweep later, assume no additional sweep

def trapezoidal_wing_geometry(AR, S=S_wing, taper_ratio=taper_ratio):
    b = (AR * S) ** 0.5
    C_root = (2*S) / (b * (1 + taper_ratio))
    C_tip = C_root * taper_ratio
    initial_sweep = np.atan((C_root - C_tip) / (b / 2)) # sweep caused by taper, not an additional design sweep
    C_bar = (2/3) * C_root * ((1 + taper_ratio + taper_ratio**2) / (1 + taper_ratio)) # also MGC in gudmunsson book
    Y_bar = (b / 6) * ((1 + 2*taper_ratio) / (1 + taper_ratio))
    X_bar = Y_bar * np.tan(initial_sweep)  # initial_sweep is already in radians , can either be from the leading edge of the wing or front of plane, this is leading edge
    
    return b, C_root, C_tip, C_bar, Y_bar, float(X_bar), np.rad2deg(float(initial_sweep))

b, C_root, C_tip, C_bar, Y_bar, X_bar, initial_sweep = (
    trapezoidal_wing_geometry(AR=10, S=S_wing, taper_ratio=taper_ratio)
)

# Nomenclature:
# V_ht = horizontal tail volume coefficient
# AR_ht = horizontal tail aspect ratio
# taper_ratio_ht = horizontal tail taper ratio
# l_ht = horizontal tail length (distance from wing mac to aerodynamic center of horizontal tail)


AR_ht = 4.4
V_ht = 0.914
taper_ratio_ht = 0.462
l_ht = 40.47 # ft (can change this to anything, but this is just avg from comp ass)
AR_vt = 1.766
V_vt = 0.0934
taper_ratio_vt = 0.463
l_vt = l_ht # ft 

def horizontal_tail_geometry(V_ht, AR_ht, l_ht, taper_ratio_ht):
    # assume conventional tail (trapezoidal) with no additional sweep
    # can either solve for S_ht or l_ht, will solve for S_ht since we want more control over length
    S_ht = V_ht * S_wing * C_bar / l_ht

    b_ht = (AR_ht * S_ht) ** 0.5
    C_root_ht = (2*S_ht) / (b_ht * (1 + taper_ratio_ht))
    C_tip_ht = C_root_ht * taper_ratio_ht
    initial_sweep_ht = np.atan((C_root_ht - C_tip_ht) / (b_ht / 2)) # sweep caused by taper, not an additional design sweep
    C_bar_ht = (2/3) * C_root_ht * ((1 + taper_ratio_ht + taper_ratio_ht**2) / (1 + taper_ratio_ht))
    Y_bar_ht = (b_ht / 6) * ((1 + 2*taper_ratio_ht) / (1 + taper_ratio_ht))
    X_bar_ht = Y_bar_ht * np.tan(initial_sweep_ht)  # initial_sweep is already in radians

    return S_ht, b_ht, C_root_ht, C_tip_ht, C_bar_ht, Y_bar_ht, float(X_bar_ht), np.rad2deg(float(initial_sweep_ht))

def vertical_tail_geometry(V_vt, AR_vt, l_vt, taper_ratio_vt):
    # assume conventional tail (trapezoidal) with no additional sweep
    # can either solve for S_vt or l_vt, will solve for S_vt since we want more control over length
    S_vt = V_vt * S_wing * b / l_vt
    b_vt = (AR_vt * S_vt) ** 0.5
    C_root_vt = (2*S_vt) / (b_vt * (1 + taper_ratio_vt))
    C_tip_vt = C_root_vt * taper_ratio_vt
    initial_sweep_vt = np.atan((C_root_vt - C_tip_vt) / (b_vt)) # sweep caused by taper, not an additional design sweep
    C_bar_vt = (2/3) * C_root_vt * ((1 + taper_ratio_vt + taper_ratio_vt**2) / (1 + taper_ratio_vt))
    Y_bar_vt = (b_vt / 3) * ((1 + 2*taper_ratio_vt) / (1 + taper_ratio_vt))
    X_bar_vt = Y_bar_vt * np.tan(initial_sweep_vt)  # initial_sweep is already in radians

    return S_vt, b_vt, C_root_vt, C_tip_vt, C_bar_vt, Y_bar_vt, float(X_bar_vt), np.rad2deg(float(initial_sweep_vt))

S_ht, b_ht, C_root_ht, C_tip_ht, C_bar_ht, Y_bar_ht, X_bar_ht, initial_sweep_ht = (
    horizontal_tail_geometry(
        V_ht=V_ht,
        AR_ht=AR_ht,
        l_ht=l_ht,
        taper_ratio_ht=taper_ratio_ht,
    )
)

S_vt, b_vt, C_root_vt, C_tip_vt, C_bar_vt, Y_bar_vt, X_bar_vt, initial_sweep_vt = (
    vertical_tail_geometry(
        V_vt=V_vt,
        AR_vt=AR_vt,
        l_vt=l_vt,
        taper_ratio_vt=taper_ratio_vt,
    )
)

print(f"Span (b): {b:.3f} ft") 
print(f"Root chord (C_root): {C_root:.3f} ft")
print(f"Tip chord (C_tip): {C_tip:.3f} ft")
print(f"Mean aerodynamic chord (C_bar): {C_bar:.3f} ft")
print(f"MAC spanwise location (Y_bar): {Y_bar:.3f} ft")
print(f"MAC longitudinal location (X_bar): {X_bar:.3f} ft")
print(f"Leading edge sweep: {initial_sweep:.6f} degrees")

print(f"Horizontal Tail Area (S_ht): {S_ht:.3f} ft^2")
print(f"Horizontal Tail Span (b_ht): {b_ht:.3f} ft")
print(f"Horizontal Tail Root chord (C_root_ht): {C_root_ht:.3f} ft")
print(f"Horizontal Tail Tip chord (C_tip_ht): {C_tip_ht:.3f} ft")
print(f"Horizontal Tail Mean aerodynamic chord (C_bar_ht): {C_bar_ht:.3f} ft")
print(f"Horizontal Tail MAC spanwise location (Y_bar_ht): {Y_bar_ht:.3f} ft")
print(f"Horizontal Tail MAC longitudinal location (X_bar_ht): {X_bar_ht:.3f} ft")
print(f"Horizontal Tail Leading edge sweep: {initial_sweep_ht:.6f} degrees")

print(f"Vertical Tail Area (S_vt): {S_vt:.3f} ft^2")
print(f"Vertical Tail Span (b_vt): {b_vt:.3f} ft")
print(f"Vertical Tail Root chord (C_root_vt): {C_root_vt:.3f} ft")
print(f"Vertical Tail Tip chord (C_tip_vt): {C_tip_vt:.3f} ft")
print(f"Vertical Tail Mean aerodynamic chord (C_bar_vt): {C_bar_vt:.3f} ft")
print(f"Vertical Tail MAC spanwise location (Y_bar_vt): {Y_bar_vt:.3f} ft")
print(f"Vertical Tail MAC longitudinal location (X_bar_vt): {X_bar_vt:.3f} ft")
print(f"Vertical Tail Leading edge sweep: {initial_sweep_vt:.6f} degrees")
