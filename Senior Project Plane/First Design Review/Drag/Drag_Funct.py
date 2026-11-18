import numpy as np
import matplotlib.pyplot as plt
from ambiance import Atmosphere

def get_Cf(Mach, altitude, length):
    density_SI = Atmosphere(altitude).density[0]  # kg/m^3
    density = density_SI * 0.062428  # kg/m^3 to lb/ft^3
    viscosity_SI = Atmosphere(altitude).dynamic_viscosity[0]  # Pa
    viscosity = viscosity_SI * 0.020885  # Pa*s to lb/(ft*s)
    velocity = Mach * Atmosphere(altitude).speed_of_sound[0]
    Re = (density * velocity * length) / viscosity
    Cf = 0.455 / (np.log10(Re)**2.58)
    return Cf

def CDminFunct(Mach, Altitude, Fuselage, Wing, Tail):

    ## Fuselage FF and IF ## (16-135 book reference)
    Fuselage.FinenessRatio = Fuselage.Mac / Fuselage.Diameter
    Fuselage.FormFactor = 1.0 + (60 / (Fuselage.FinenessRatio**3)) + (Fuselage.FinenessRatio / 400)
    Fuselage.InterferenceFactor = 1.0

    ## Wing FF and IF ## (16-127 book reference)
    Wing.FormFactor = (1 + ((0.6 * Wing.tc) / Wing.xc) + (100 * (Wing.tc**4))) * (1.34 * (Mach**0.18) * (np.cos(Wing.Sweep)**0.28))
    Wing.InterferenceFactor = 1.0 # Table 16-12 (For High Wing Only)

    ## Tail FF and IF ## (15-66 pdf reference)
    Tail.FormFactor = ((3.52 * Tail.tc)*np.cos(Tail.SweepMidChord)**2 )+ 1
    Tail.InterferenceFactor = 1.2 # Explanation in equation

    ## Cf Calculation ##
    Fuselage.Cf = get_Cf(Mach, Altitude, Fuselage.Length)
    Wing.Cf = get_Cf(Mach, Altitude, Wing.Mac)
    Tail.Cf = get_Cf(Mach, Altitude, Tail.Mac)

    ## Wet Area Calculation ##
    Fuselage.WetArea = np.pi * Fuselage.Diameter * Fuselage.Length
    Wing.WetArea = 2 * Wing.Span * Wing.Mac
    Tail.WetArea = 2 * Tail.Span * Tail.Mac

    ## Referance Area (Wing Area) ##
    Sref = Wing.Area

    ## CDmin ##
    CDmin = (Fuselage.Cf * Fuselage.FormFactor * Fuselage.InterferenceFactor * (Fuselage.WetArea / Sref)) + \
            (Wing.Cf * Wing.FormFactor * Wing.InterferenceFactor * (Wing.WetArea / Sref)) + \
            (Tail.Cf * Tail.FormFactor * Tail.InterferenceFactor * (Tail.WetArea / Sref))

    return CDmin