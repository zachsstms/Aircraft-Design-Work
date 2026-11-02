import numpy as np
import matplotlib.pyplot as plt


#### Component Drag Buildup ####

### Synthesis of Subsonic Airplane Design ###

## Vortex Drag Coefficients ##

# F-2.1 Untwisted plane wigns #
taper_ratio = 
Mach = 
AR = 
CL = np.linspace(0, 2, 100)

delta_wing = (0.0015 + 0.016*(taper_ratio - 0.4)**2) * (np.sqrt(1-Mach**2) * AR - 4.5)
CDv_wing = (1 + delta_wing) * (CL**2 / (np.pi * AR))

# F-2.4 Vortex drag induced by fuselage lift #
Volume_fuselage =
CL0 = 
CL_alpha_fuselage =
S_wing = 

alpha_fuselage = (CL - CL0) / CL_alpha_fuselage 
CDs_fuselage = (0.15 * alpha_fuselage**2 * Volume_fuselage**(2/3)) / S_wing

# F-2.6 Horizontal tailplane contribution #
Cm_ac = 
AR_horizontal_tail =
horizontal_tail_area =
wing_area =
horizontal_tail_length =
mean_aerodynamic_chord_length =

CD_horizontal_tail = 1.02 * (Cm_ac**2) / (np.pi * AR_horizontal_tail * (horizontal_tail_area / wing_area) * (horizontal_tail_length / mean_aerodynamic_chord_length)**2)

## Profile Drag Coefficients ##

# F-3.2 Wing Section #
# Need Help with this one, I dont know if I should use it ... #

# F-3.3 Wing # 
cdp_min_wing =
s_net =
s_wing =
delta_l =
cdp =
CL1 =
CLmax =


CDp_wing = cdp_min_wing * (s_net / s_wing) + 0.75 * (delta_l * cdp) * ((CL - CL1) / (CLmax - CL1))**2

# F-3.4 Fuselage # 
taperRatio_fuselage_eff =
shapeFactor_fuselage = (2.2 / (taperRatio_fuselage_eff**1.5)) + (3.8 / (taperRatio_fuselage_eff**3))
S_wet_fuselage =
S_ref =
CF_fuselage = 
CDp_fueslage = CF_fuselage * (S_wet_fuselage / S_ref) * (1 + shapeFactor_fuselage)

# F-3.6 Tailplane #
S = 
CF_HT =
CDS_hBasic = 2 * CF_HT * (1 + 2.75 * t_c_HT * np.cos(sweepback_angle_HT)**2) * (S_wet_HT / S)
delta_l_HT =
CDS_h =

CDp_HT = (CDS_hBasic + delta_l_HT * CDS_h)

CF_VT =
t_c_VT =
sweepback_angle_VT =
S_wet_VT =

CDp_VT = 2 * CF_VT * (1 + 2.75 * t_c_VT * np.cos(sweepback_angle_VT)**2) * (S_wet_VT / S)

