import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace
from ambiance import Atmosphere
from DragCode import CDminFunct
from wing_tail_geometry import planeGeometry
import yaml

Fuselage = SimpleNamespace()
Wing = SimpleNamespace()
HorizontalTail = SimpleNamespace()
VerticalTail = SimpleNamespace()

## Inputs ##
cruiseWeight = 48000 #lbs
cruiseAltitude = 20000 #ft
mach = ...
altitude = ...
oswaldEfficiency = ...
aspectRatio = ...
Fuselage.Length = 81 # ft (can change this to anything, but this is just avg from comp ass)
Fuselage.Diameter = 9 # ft (can change this to anything, but this is just avg from comp ass)
HorizontalTail.AspectRatio = 4.4
HorizontalTail.V = 1.2
HorizontalTail.taper_ratio = 0.462
HorizontalTail.Length = 39 # ft (can change this to anything, but this is just avg from comp ass)
VerticalTail.AspectRatio = 1.766
VerticalTail.V = 0.13
VerticalTail.taper_ratio = 0.463
VerticalTail.Length = HorizontalTail.Length # ft
Cl = np.linspace(0, 2.5, 250)







[Fuselage, Wing, HorizontalTail, VerticalTail] = planeGeometry(Wing)
[CDmin, CDtotal, Cl_Cd_cruise, Wing, Fuselage, HorizontalTail, VerticalTail] = CDminFunct(mach, cruiseAltitude, cruiseWeight, Fuselage, Wing, HorizontalTail, VerticalTail)

if (1 - np.abs(Cl_Cd_cruise[-1] / Cl_Cd_cruise[-2])) > tolerance:
