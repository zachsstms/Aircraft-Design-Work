import numpy as np
from types import SimpleNamespace

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


def planeGeometry(Wing):

    '''
    This function needs inputs of the aspect ratio, wing area, and wing taper ratio.

    It will output the fuselage, wing, horizontal tail, and vertical tail geometries as SimpleNamespace objects.
    '''

    ## Creating Classes ##
    Fuselage = SimpleNamespace()
    HorizontalTail = SimpleNamespace()
    VerticalTail = SimpleNamespace()

    ## Trapezoidal wing geometry calculations ##
    Wing.Span = (Wing.AspectRatio * Wing.Area) ** 0.5
    Wing.C_root = (2*Wing.Area) / (Wing.Span * (1 + Wing.taper_ratio))
    Wing.C_tip = Wing.C_root * Wing.taper_ratio
    Wing.initial_sweep = np.atan((Wing.C_root - Wing.C_tip) / (Wing.Span / 2)) # sweep caused by taper, not an additional design sweep
    Wing.Mac = (2/3) * Wing.C_root * ((1 + Wing.taper_ratio + Wing.taper_ratio**2) / (1 + Wing.taper_ratio)) # also MGC in gudmunsson book
    Wing.Y_bar = (Wing.Span / 6) * ((1 + 2*Wing.taper_ratio) / (1 + Wing.taper_ratio))
    Wing.X_bar = Wing.Y_bar * np.tan(Wing.initial_sweep)  # initial_sweep is already in radians , can either be from the leading edge of the wing or front of plane, this is leading edge

    ## Horizontal Tail Geometry Calculations ##
    HorizontalTail.Area = HorizontalTail.V * Wing.Area * Wing.Mac / HorizontalTail.Length
    HorizontalTail.Span = (HorizontalTail.AspectRatio * HorizontalTail.Area) ** 0.5
    HorizontalTail.C_root = (2*HorizontalTail.Area) / (HorizontalTail.Span * (1 + HorizontalTail.taper_ratio))
    HorizontalTail.C_tip = HorizontalTail.C_root * HorizontalTail.taper_ratio
    HorizontalTail.initial_sweep = np.atan((HorizontalTail.C_root - HorizontalTail.C_tip) / (HorizontalTail.Span / 2)) # sweep caused by taper, not an additional design sweep
    HorizontalTail.Mac = (2/3) * HorizontalTail.C_root * ((1 + HorizontalTail.taper_ratio + HorizontalTail.taper_ratio**2) / (1 + HorizontalTail.taper_ratio))
    HorizontalTail.Y_bar = (HorizontalTail.Span / 6) * ((1 + 2*HorizontalTail.taper_ratio) / (1 + HorizontalTail.taper_ratio))
    HorizontalTail.X_bar = HorizontalTail.Y_bar * np.tan(HorizontalTail.initial_sweep)  # initial_sweep is already in radians

    ## Vertical Tail Geometry Calculations ##
    VerticalTail.Area = VerticalTail.V * Wing.Area * Wing.Mac / VerticalTail.Length
    VerticalTail.Span = (VerticalTail.AspectRatio * VerticalTail.Area) ** 0.5
    VerticalTail.C_root = (2*VerticalTail.Area) / (VerticalTail.Span * (1 + VerticalTail.taper_ratio))
    VerticalTail.C_tip = VerticalTail.C_root * VerticalTail.taper_ratio
    VerticalTail.initial_sweep = np.atan((VerticalTail.C_root - VerticalTail.C_tip) / (VerticalTail.Span / 2)) # sweep caused by taper, not an additional design sweep
    VerticalTail.Mac = (2/3) * VerticalTail.C_root * ((1 + VerticalTail.taper_ratio + VerticalTail.taper_ratio**2) / (1 + VerticalTail.taper_ratio))
    VerticalTail.Y_bar = (VerticalTail.Span / 3) * ((1 + 2*VerticalTail.taper_ratio) / (1 + VerticalTail.taper_ratio))
    VerticalTail.X_bar = VerticalTail.Y_bar * np.tan(VerticalTail.initial_sweep)  # initial_sweep is already in radians 

    return Fuselage, Wing, HorizontalTail, VerticalTail
