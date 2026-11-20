from types import SimpleNamespace
import numpy as np

Fuselage = SimpleNamespace()
Wing = SimpleNamespace()
HorizontalTail = SimpleNamespace()
VerticalTail = SimpleNamespace()

## Inputs ##
cruiseWeight = 48000 #lbs
cruiseAltitude = 20000 #ft
mach = ...
altitude = ...
Wing.oswaldEfficiency = ...
Wing.AspectRatio = ...
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
