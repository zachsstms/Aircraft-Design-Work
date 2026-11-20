import numpy as np
from ambiance import Atmosphere

'''
    Needs to use SimpleNamespace for Fuselage, Wing, and Tail inputs. Needs Mach, Altitude, and Cruise Weight inputs as well.

    Fuselage Needs: Fuselage.Length, Fuselage.Diameter
    Wing Needs: Wing.tc, Wing.xc, Wing.Sweep, Wing.Mac, Wing.Span, Wing.Area
    HorizontalTail Needs: HorizontalTail.tc, HorizontalTail.SweepMidChord, HorizontalTail.Mac, HorizontalTail.Span
    VerticalTail Needs: VerticalTail.tc, VerticalTail.SweepMidChord, VerticalTail.Mac, VerticalTail.Span

    Outputs CDmin.
'''

def CDminFunct(Mach, Altitude, cruiseWeight, Fuselage, Wing, HorizontalTail, VerticalTail):

    def get_Cf(Mach, altitude, length):
        density_SI = Atmosphere(altitude).density[0]  # kg/m^3
        density = density_SI * 0.062428  # kg/m^3 to lb/ft^3
        viscosity_SI = Atmosphere(altitude).dynamic_viscosity[0]  # Pa
        viscosity = viscosity_SI * 0.020885  # Pa*s to lb/(ft*s)
        velocity = Mach * Atmosphere(altitude).speed_of_sound[0]
        Re = (density * velocity * length) / viscosity
        Cf = 0.455 / (np.log10(Re)**2.58)
        return Cf

    ## Fuselage FF and IF ## (16-135 book reference)
    Fuselage.FinenessRatio = Fuselage.Length / Fuselage.Diameter
    Fuselage.FormFactor = 1.0 + (60 / (Fuselage.FinenessRatio**3)) + (Fuselage.FinenessRatio / 400)
    Fuselage.InterferenceFactor = 1.0

    ## Wing FF and IF ## (16-127 book reference)
    Wing.FormFactor = (1 + ((0.6 * Wing.tc) / Wing.xc) + (100 * (Wing.tc**4))) * (1.34 * (Mach**0.18) * (np.cos(Wing.Sweep)**0.28))
    Wing.InterferenceFactor = 1.0 # Table 16-12 (For High Wing Only)

    ## Tail FF and IF ## (15-66 pdf reference)
    HorizontalTail.FormFactor = ((3.52 * HorizontalTail.tc)*np.cos(HorizontalTail.SweepMidChord)**2 )+ 1
    HorizontalTail.InterferenceFactor = 1.2 # Explanation in equation
    VerticalTail.FormFactor = ((3.52 * VerticalTail.tc)*np.cos(VerticalTail.SweepMidChord)**2 )+ 1
    VerticalTail.InterferenceFactor = 1.2 # Explanation in equation

    ## Cf Calculation ##
    Fuselage.Cf = get_Cf(Mach, Altitude, Fuselage.Length)
    Wing.Cf = get_Cf(Mach, Altitude, Wing.Mac)
    HorizontalTail.Cf = get_Cf(Mach, Altitude, HorizontalTail.Mac)
    VerticalTail.Cf = get_Cf(Mach, Altitude, VerticalTail.Mac)

    ## Wet Area Calculation ##
    Fuselage.WetArea = np.pi * Fuselage.Diameter * Fuselage.Length
    Wing.WetArea = 2 * Wing.Span * Wing.Mac
    HorizontalTail.WetArea = 2 * HorizontalTail.Span * HorizontalTail.Mac
    VerticalTail.WetArea = 2 * VerticalTail.Span * VerticalTail.Mac

    ## Referance Area (Wing Area) ##
    Sref = Wing.Area

    ## Crud Factor ## (From Book, cant find which page rn)
    crudFactor = 1.25

    ## CDmin ##
    CDmin = crudFactor * ((Fuselage.Cf * Fuselage.FormFactor * Fuselage.InterferenceFactor * (Fuselage.WetArea / Sref)) + \
            (Wing.Cf * Wing.FormFactor * Wing.InterferenceFactor * (Wing.WetArea / Sref)) + \
            (HorizontalTail.Cf * HorizontalTail.FormFactor * HorizontalTail.InterferenceFactor * (HorizontalTail.WetArea / Sref)) + \
            (VerticalTail.Cf * VerticalTail.FormFactor * VerticalTail.InterferenceFactor * (VerticalTail.WetArea / Sref)))

    Cl = np.linspace(0, 2.5, 250)
    CdTotal = CDmin + ((Cl**2) / (np.pi * Wing.AspectRatio * Wing.OswaldEfficiency))

    Cl_cruise = cruiseWeight / (0.5 * (Atmosphere(Altitude).density[0] * 0.062428) * (Mach * (Atmosphere(Altitude).speed_of_sound[0] / 0.3048)**2) * Sref)
    Cd_cruise = CDmin + ((Cl_cruise**2) / (np.pi * Wing.AspectRatio * Wing.OswaldEfficiency))

    Cl_Cd_cruise = Cl_cruise / Cd_cruise

    return CDmin, CdTotal, Cl_Cd_cruise, Wing, Fuselage, HorizontalTail, VerticalTail