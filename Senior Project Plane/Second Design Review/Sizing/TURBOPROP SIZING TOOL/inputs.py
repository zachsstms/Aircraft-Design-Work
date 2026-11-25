"""
THIS IS THE INPUT SECTION OF THE SIZING TOOL

To use: simply place values where they belong,
then run the script.

Running the script will call the solver to iterate through the
sizing loop. All plots from the tool should be in the `Plots` subfolder. In the future, 
trade studies and parameter sweeps will be implemented in `TradeStudies.py
"""
from types import SimpleNamespace
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
    Area=None,                 # Set by solver each iteration; ft^2
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

# Initial guesses
initial_MTOW = None            # lbf
initial_wing_area = None       # ft^2

# Relative convergence tolerances; adjust as needed
tol_LD = 0.01
tol_MTOW = 0.01
tol_S = 0.01
max_iterations = 100

# Mission and operating inputs
cruiseWeight = 48_000.0        # lbf
mach = None                    # dimensionless
cruise_altitude = 20_000 * ureg.ft

EWF_initial = None             # empty-weight fraction; dimensionless
Range = None                   # nmi
BSFC = None                    # lb/(hp*hr)
eta_p_cruise = None            # propeller efficiency; dimensionless
Payload_weight = None          # lbf

# Constraint inputs
landing_distance = None        # ft; empirical correlation input
landing_altitude = None        # altitude quantity
takeoff_distance = None        # ft; empirical correlation input
takeoff_altitude = None        # altitude quantity
sigma_TO = None                # takeoff density ratio; dimensionless
CL_max_TO = None               # dimensionless
CL_max_L = None                # dimensionless
alpha_P_cruise = None          # cruise power correction; dimensionless


def validate_inputs(cfg):
    required = {
        "initial_MTOW": cfg.initial_MTOW,
        "initial_wing_area": cfg.initial_wing_area,
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
        "EWF_initial": cfg.EWF_initial,
        "Range": cfg.Range,
        "BSFC": cfg.BSFC,
        "eta_p_cruise": cfg.eta_p_cruise,
        "Payload_weight": cfg.Payload_weight,
        "landing_distance": cfg.landing_distance,
        "landing_altitude": cfg.landing_altitude,
        "takeoff_distance": cfg.takeoff_distance,
        "takeoff_altitude": cfg.takeoff_altitude,
        "sigma_TO": cfg.sigma_TO,
        "CL_max_TO": cfg.CL_max_TO,
        "CL_max_L": cfg.CL_max_L,
        "alpha_P_cruise": cfg.alpha_P_cruise,
    }

    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise ValueError(
            "Fill in these required inputs before solving: "
            + ", ".join(missing)
        )

    if not hasattr(cfg.cruise_altitude, "to"):
        raise ValueError("cruise_altitude must be a Pint quantity, such as 20_000 * ureg.ft.")

    cfg.cruise_altitude.to("meters")
