"""
This code runs the constraint diagram. It is split into
stages of flight. 
Inputs:
MTOW
C_D0
AR
e
0.85
M_cruise
cruise alt
landing distance
landing altitude
takeoff distance
takeoff altitude
cruise prop efficiency
k

Outputs:
P/W
W/S
P
S
Diagram
"""


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from ambiance import Atmosphere
import pint
ureg = pint.UnitRegistry()

def constraint_analysis(MTOW, C_D0, AR, e, M_cruise, 
                       cruise_alt, landing_distance, landing_altitude,
                       takeoff_distance, takeoff_altitude, CL_max_TO,eta_p_cruise,k,beta_cruise):
    
    sealevel = Atmosphere(0) # gives SI 
    rho_sl=sealevel.density*ureg("kg/m^3").to("slug/ft^3").magnitude # sea-level slug/ft^3
    #------------------------------
    # CRUISE CONSTRAINT
    #----------------------------
    a_cruisealt = (Atmosphere(cruise_alt.to("meters").magnitude).speed_of_sound)*ureg("m/s").to("ft/s").magnitude # ISA to find speed of sound, convert to (ft/s)
    rho_cruisealt=Atmosphere(cruise_alt.to("meters").magnitude).density*ureg("kg/m^3").to("slug/ft^3").magnitude # ISA to find density at cruise altitude (slug/ft^3)
    V_cruise=M_cruise*a_cruisealt #ft/sec
    alpha_P_cruise=0.85 # we want to cruise at 85% of max power (usual value)
    

    W_S=np.linspace(1, 200, 1000) # linspace for wingload
    q_cruise=0.5*rho_cruisealt*V_cruise**2 # dynamic pressure at cruise

    P_W_cruise =( 
    (V_cruise / 
    (550 * eta_p_cruise * alpha_P_cruise))*
    (q_cruise*C_D0/W_S +(k*(W_S/q_cruise)*beta_cruise**2)) # the 550 is to get horsepower
    )

    #-------------------------
    # TAKEOFF CONSTRAINT
    #-------------------------
    # NOTES: Takeoff efficiency imbedded in reference values (constant of 1.5334) 
    #ROSAKM PART 23 Correlation
    
    sigma_TO = 1.0 # assuming sea level, standard day condtions
    S_TOG = takeoff_distance/1.5334 # based on fig 3.4 and eqn 3.5 Roskam; constant from only dual prop references

    # Solve: 0.009*TOP_23**2 + 4.9*TOP_23 - S_TOG = 0 (eqn 3.4)
    a = 0.009
    b = 4.9
    c = -S_TOG

    TOP_23 = (-b + np.sqrt(b**2 - 4*a*c)) / (2*a)  

    P_W_takeoff = 1/((TOP_23 * sigma_TO * CL_max_TO) / W_S) #fit P_W_TO to wing loading sweep 
    #-------------------------------

    # LANDING CONSTRAIN DIAGRAM LINE PART 23 ROSKAM
    S_L = 3500; #ft; landing distance requirement
    V_SL = np.sqrt(S_L / 0.5316) # stall speed (kts) from eqn 3.14 
    V_SL = V_SL * 1.68781 # convert kt to ft/sec
    C_L_max_L = 2.5 # pg 91 roskam; agressive typical value for prop

    W_S_landing = (0.5 * rho_sl * V_SL**2 * C_L_max_L )*(1/0.95) #landing wing loading constraint; 0.95 comes from assumptioption landing weight = 0.95 takeoff weight mentioned pg 111
    W_S_landing = float(np.squeeze(W_S_landing))
    print(f"W_S_landing: {W_S_landing}")

    #-------------------------------

    return W_S, # P_W, P, S

