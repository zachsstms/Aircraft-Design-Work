"""
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

"""


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from ambiance import Atmosphere
import pint
ureg = pint.UnitRegistry()


