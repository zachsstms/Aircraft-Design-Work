import numpy as np
import matplotlib.pyplot as plt
from ambiance import Atmosphere
from types import SimpleNamespace

Mach = 0.48
Altitude = 20000.0 #ft

def get_Cf(Mach, altitude, length):
    density_SI = Atmosphere(altitude).density[0]  # kg/m^3
    density = density_SI * 0.062428  # kg/m^3 to lb/ft^3
    viscosity_SI = Atmosphere(altitude).dynamic_viscosity[0]  # Pa
    viscosity = viscosity_SI * 0.020885  # Pa*s to lb/(ft*s)
    velocity = Mach * Atmosphere(altitude).speed_of_sound[0]
    Re = (density * velocity * length) / viscosity
    Cf = 0.455 / (np.log10(Re)**2.58)
    return Cf

## Fuselage FF and IF ## (16-135)
Fuselage = SimpleNamespace()
Fuselage.FinenessRatio = Fuselage.Mac / Fuselage.Diameter
Fuselage.FormFactor = 1.0 + (60 / (Fuselage.FinenessRatio**3)) + (Fuselage.FinenessRatio / 400)
Fuselage.InterferenceFactor = 1.0


## Wing FF and IF ## (16-127)
Wing = SimpleNamespace()
Wing.FormFactor = (1 + ((0.6 * Wing.tc) / Wing.xc) + (100 * (Wing.tc**4))) * (1.34 * (Mach**0.18) * (np.cos(Wing.Sweep)**0.28))
Wing.InterferenceFactor = 1.0 # Table 16-12 (For High Wing Only)

## Tail FF and IF ## (16-127)
Tail = SimpleNamespace()
Tail.FormFactor = (1 + ((0.6 * Tail.tc) / Tail.xc) + (100 * (Tail.tc**4))) * (1.34 * (Mach**0.18) * (np.cos(Tail.Sweep)**0.28))
Tail.InterferenceFactor = 1.04 # Table 16-12 (For T-Tail Only)

## Cf Calculation ##
Fuselage.Cf = get_Cf(Mach, Altitude, Fuselage.Length)
Wing.Cf = get_Cf(Mach, Altitude, Wing.Mac)
Tail.Cf = get_Cf(Mach, Altitude, Tail.Mac)

## Wet Area Calculation ##
Fuselage.WetArea = np.pi * Fuselage.Diameter * Fuselage.Mac
Wing.WetArea = 2 * Wing.Span * Wing.Mac
Tail.WetArea = 2 * Tail.Span * Tail.Mac