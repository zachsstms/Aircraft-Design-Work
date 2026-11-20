"""
This file is the looping workhorse. It takes in the inputs (requirements)
and runs each function. 
"""
# loading each function
from types import SimpleNamespace
from aerodynamics import CDminFunct
from geometry import planeGeometry
from mission import MTOW_convergence
from constraint import constraint_analysis
import inputs

tolerance=0.01 #this could change, we could also implement multiple tolerances
Fuselage = SimpleNamespace()
Wing = SimpleNamespace()
HorizontalTail = SimpleNamespace()
VerticalTail = SimpleNamespace()







[Fuselage, Wing, HorizontalTail, VerticalTail] = planeGeometry(Wing)
[CDmin, CDtotal, Cl_Cd_cruise, Wing, Fuselage, HorizontalTail, VerticalTail] = CDminFunct(mach, cruiseAltitude, cruiseWeight, Fuselage, Wing, HorizontalTail, VerticalTail)

if (1 - np.abs(Cl_Cd_cruise[-1] / Cl_Cd_cruise[-2])) > tolerance:
