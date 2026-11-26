"""
THIS IS THE INPUT SECTION OF THE SIZING TOOL

To use: simply place values where they belong,
then run the script.

Running the script will call the solver to iterate through the
sizing loop. All plots from the tool should be in the `Plots` subfolder. In the future, 
trade studies and parameter sweeps will be implemented in `TradeStudies.py

NOTE: The weight guess and convergence criteria are in `solver.py`.
"""
from types import SimpleNamespace
import math
import pint
ureg = pint.UnitRegistry() # handles units robustly

# Internal numeric convention:
#   geometry: ft, ft^2
#   weights: lbf (plain numeric values)
#   distances: ft
#   range: nmi
#   BSFC: lb/(hp*hr)
#   efficiencies, Mach, and aerodynamic coefficients: dimensionless
#   altitudes: ft, converted to meters for Atmosphere

Fuselage = SimpleNamespace(
    Length=81.0,       # ft
    Diameter=9.0,      # ft
)

Wing = SimpleNamespace(
    AspectRatio=None,          # dimensionless
    taper_ratio=None,          # dimensionless
    OswaldEfficiency=None,     # dimensionless
    tc=None,                   # thickness/chord ratio
    xc=None,                   # location of max thickness / chord
    Sweep=None,                # radians; value expected by aerodynamics.py
)

HorizontalTail = SimpleNamespace(
    AspectRatio=4.4,           # aspect ratio of horizontal tail
    V=1.2,                     # dimensionless tail volume coefficient
    taper_ratio=0.462,         # taper ratio of horizontal tail
    Length=39.0,               # ft
    tc=None,                   # thickness/chord ratio
    SweepMidChord=None,        # radians
)

VerticalTail = SimpleNamespace(
    AspectRatio=1.766,         # aspect ratio of vertical tail
    V=0.13,                    # dimensionless tail volume coefficient
    taper_ratio=0.463,         # taper ratio of vertical tail
    Length=39.0,               # ft
    tc=None,                   # thickness/chord ratio
    SweepMidChord=None,        # radians
)

# Mission and operating inputs
mach = None                    # dimensionless
cruise_altitude = 20_000 * ureg.ft

Range = None                   # nmi
BSFC = None                    # lb/(hp*hr)
eta_p_cruise = None            # propeller efficiency; dimensionless
Payload_weight = None          # lbf

# Constraint inputs
landing_distance = None        # ft; empirical correlation input
landing_altitude = None        # altitude quantity
takeoff_distance = None        # ft; empirical correlation input
takeoff_altitude = None        # altitude quantity
# sigma_TO = None              # takeoff density ratio; dimensionless (moved to solver.py)
CL_max_TO = None               # dimensionless
CL_max_L = None                # dimensionless
alpha_P_cruise = None          # cruise power correction; dimensionless
#------------------------------------------------------------------------------------------------------------






# below is essentially just some logic to make sure the tool does not accept non-physical inputs, and makes it such that you can run this thing using this file. 
# saves geometry to a configuration class ("cfg")
def validate_inputs(cfg):
    required = {
        "mach": cfg.mach,
        "Wing.AspectRatio": cfg.Wing.AspectRatio,
        "Wing.taper_ratio": cfg.Wing.taper_ratio,
        "Wing.OswaldEfficiency": cfg.Wing.OswaldEfficiency,
        "Wing.tc": cfg.Wing.tc,
        "Wing.xc": cfg.Wing.xc,
        "Wing.Sweep": cfg.Wing.Sweep,
        "HorizontalTail.tc": cfg.HorizontalTail.tc,
        "HorizontalTail.SweepMidChord": cfg.HorizontalTail.SweepMidChord,
        "VerticalTail.tc": cfg.VerticalTail.tc,
        "VerticalTail.SweepMidChord": cfg.VerticalTail.SweepMidChord,
        "Range": cfg.Range,
        "BSFC": cfg.BSFC,
        "eta_p_cruise": cfg.eta_p_cruise,
        "Payload_weight": cfg.Payload_weight,
        "landing_distance": cfg.landing_distance,
        "landing_altitude": cfg.landing_altitude,
        "takeoff_distance": cfg.takeoff_distance,
        "takeoff_altitude": cfg.takeoff_altitude,
        #"sigma_TO": cfg.sigma_TO, moved to solver.py
        "CL_max_TO": cfg.CL_max_TO,
        "CL_max_L": cfg.CL_max_L,
        "alpha_P_cruise": cfg.alpha_P_cruise,
    }
# basically need these to run the solver or else it will error
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise ValueError(
            "Fill in these required inputs before solving: "
            + ", ".join(missing)
        )
    # this code basically ensures that an error will be thrown for non-physical inputs. 
    for name in ("cruise_altitude", "takeoff_altitude", "landing_altitude"):
        altitude = getattr(cfg, name)
        if not hasattr(altitude, "to"):
            raise ValueError(f"{name} must be a Pint length, such as 20_000 * ureg.ft.")
        altitude.to("meters")

    positive = ("mach", "Range", "BSFC", "eta_p_cruise", "Payload_weight",
                "landing_distance", "takeoff_distance", "CL_max_TO", "CL_max_L", "alpha_P_cruise")
    for name in positive:
        if not 0 < getattr(cfg, name) < float("inf"):
            raise ValueError(f"{name} must be finite and positive.")
    if cfg.mach >= 1 or cfg.eta_p_cruise > 1 or cfg.alpha_P_cruise > 1:
        raise ValueError("Use subsonic Mach and efficiencies/power ratios no greater than 1.")
    for surface in (cfg.Wing, cfg.HorizontalTail, cfg.VerticalTail):
        if not (surface.AspectRatio > 0 and 0 < surface.taper_ratio <= 1 and 0 < surface.tc <= 0.21):
            raise ValueError("Check surface aspect ratio, taper ratio, and thickness ratio.")
    if not (0 < cfg.Wing.OswaldEfficiency <= 1 and 0 < cfg.Wing.xc <= 1):
        raise ValueError("Check wing Oswald efficiency and location of maximum thickness.")
    for sweep in (cfg.Wing.Sweep, cfg.HorizontalTail.SweepMidChord, cfg.VerticalTail.SweepMidChord):
        if not math.isfinite(sweep) or abs(sweep) >= math.pi / 2:
            raise ValueError("Sweep angles must be finite radians between -pi/2 and pi/2.")
    if min(cfg.Fuselage.Length, cfg.Fuselage.Diameter, cfg.HorizontalTail.V,
           cfg.HorizontalTail.Length, cfg.VerticalTail.V, cfg.VerticalTail.Length) <= 0:
        raise ValueError("Fuselage dimensions, tail volume coefficients, and tail arms must be positive.")
# run this with `python inputs.py`
if __name__ == "__main__":
    import sys
    from solver import solve
    result = solve(sys.modules[__name__], plot=True)
    print(f"Converged in {result['iterations']} iterations")
    print(f"MTOW = {result['MTOW']:,.1f} lbf, S = {result['S']:,.1f} ft^2")
    print(f"Installed power = {result['constraints']['P_design']:,.1f} shp")
    print(f"Cruise L/D = {result['L_D']:.2f}, CD0 = {result['CD0']:.5f}")
