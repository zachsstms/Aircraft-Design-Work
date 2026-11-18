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

def constraint_diagram(MTOW, C_D0, AR, e, M_cruise, 
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



    return W_S, # P_W, P, S

