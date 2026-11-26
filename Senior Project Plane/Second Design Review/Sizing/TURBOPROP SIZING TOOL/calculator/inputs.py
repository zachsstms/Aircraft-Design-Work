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
    Length=87,       # ft
    Diameter=9.0,      # ft
)

Wing = SimpleNamespace(
    AspectRatio=12,          # dimensionless
    taper_ratio=0.5,          # dimensionless
    OswaldEfficiency=0.85,     # dimensionless
    tc=0.15,                   # thickness/chord ratio
    xc=0.35,                   # location of max thickness / chord
    Sweep=0,                # radians; value expected by aerodynamics.py
)

HorizontalTail = SimpleNamespace(
    AspectRatio=4.4,           # aspect ratio of horizontal tail
    V=1.2,                     # dimensionless tail volume coefficient
    taper_ratio=0.6,         # taper ratio of horizontal tail
    Length=40.6,               # ft, moment arm
    tc=0.09,                   # thickness/chord ratio
    SweepMidChord=0,        # radians
)

VerticalTail = SimpleNamespace(
    AspectRatio=1.76,         # aspect ratio of vertical tail
    V=0.12,                    # dimensionless tail volume coefficient
    taper_ratio=0.55,         # taper ratio of vertical tail
    Length=37,               # ft
    tc=0.09,                   # thickness/chord ratio
    SweepMidChord=0,        # radians
)

# Mission and operating inputs
mach = 0.48                   # dimensionless
cruise_altitude = 20_000 * ureg.ft

Range = 825                   # nmi
BSFC = 0.476                   # lb/(hp*hr), NOTE: Based off the PW127XT-M engine
eta_p_cruise = 0.85            # propeller efficiency; dimensionless
Payload_weight = 250*69       # lbf

# Constraint inputs
landing_distance = 3500        # ft; empirical correlation input
landing_altitude = 0*ureg.ft        # altitude quantity
takeoff_distance = 4500        # ft; empirical correlation input
takeoff_altitude = 0*ureg.ft        # altitude quantity
# sigma_TO = None              # takeoff density ratio; dimensionless (moved to solver.py)
CL_max_TO = 2               # dimensionless
CL_max_L = 2.5                # dimensionless
alpha_P_cruise = 1          # cruise power correction; dimensionless, NOTE: this represents the power loss as the engine climbs in altitude
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
    if __package__:
        from .solver import solve
    else:
        from solver import solve
    result = solve(sys.modules[__name__], plot=True)
    print(f"Converged in {result['iterations']} iterations")
    print(f"MTOW = {result['MTOW']:,.1f} lbf, S = {result['S']:,.1f} ft^2")
    print(f"Installed power = {result['constraints']['P_design']:,.1f} shp")
    print(f"Cruise L/D = {result['L_D']:.2f}, CD0 = {result['CD0']:.5f}")
    
    from ambiance import Atmosphere

    fuselage, wing, horizontal_tail, vertical_tail = result["geometry"]

    atmosphere = Atmosphere(cruise_altitude.to("meters").magnitude)
    density = (atmosphere.density[0] * ureg("kg/m^3")).to("slug/ft^3").magnitude
    velocity = (mach * atmosphere.speed_of_sound[0] * ureg("m/s")).to("ft/s").magnitude
    q_cruise = 0.5 * density * velocity**2

    cl_cruise = result["cruise_weight"] / (q_cruise * wing.Area)
    k = 1 / (math.pi * wing.AspectRatio * wing.OswaldEfficiency)
    cd_induced = k * cl_cruise**2
    cl_max_ld = math.sqrt(result["CD0"] / k)
    max_ld = 1 / (2 * math.sqrt(result["CD0"] * k))

    def print_table(title, rows):
        print(f"\n{title}")
        print(f"{'Component':<14} {'Property':<32} {'Value':>18}  Units")
        print("-" * 88)
        for component, prop, value, units in rows:
            print(f"{component:<14} {prop:<32} {value:>18}  {units}")


    print_table("Design summary", [
            ("Aircraft", "Iterations", f"{result['iterations']}", "-"),
            ("Aircraft", "MTOW", f"{result['MTOW']:.1f}", "lbf"),
            ("Aircraft", "Installed power", f"{result['constraints']['P_design']:.1f}", "shp"),
            ("Aircraft", "Cruise L/D", f"{result['L_D']:.2f}", "-"),
            ("Aircraft", "CD0", f"{result['CD0']:.5f}", "-"),
            ("Aircraft", "Fuel weight fraction",
            f"{result['fuel_weight'] / result['MTOW']:.4f}", "-"),
            ("Cruise", "Lift coefficient (CL)", f"{cl_cruise:.3f}", "-"),
            ("Cruise", "Induced drag coefficient (CD)", f"{cd_induced:.5f}", "-"),
            ("Cruise", "Maximum L/D", f"{max_ld:.2f}", "-"),
            ("Cruise", "CL at maximum L/D", f"{cl_max_ld:.3f}", "-"),
        ])

    print_table("Geometry inputs", [
        ("Fuselage", "Length", f"{Fuselage.Length:.2f}", "ft"),
        ("Fuselage", "Diameter", f"{Fuselage.Diameter:.2f}", "ft"),

        ("Wing", "Aspect ratio", f"{Wing.AspectRatio:.3f}", "-"),
        ("Wing", "Taper ratio", f"{Wing.taper_ratio:.3f}", "-"),
        ("Wing", "Input sweep", f"{Wing.Sweep:.4f}", "rad"),
        ("Wing", "Thickness/chord (t/c)", f"{Wing.tc:.3f}", "-"),
        ("Wing", "Max-thickness location (x/c)", f"{Wing.xc:.3f}", "-"),
        ("Wing", "Oswald efficiency", f"{Wing.OswaldEfficiency:.3f}", "-"),

        ("Horizontal tail", "Aspect ratio", f"{HorizontalTail.AspectRatio:.3f}", "-"),
        ("Horizontal tail", "Tail volume coefficient", f"{HorizontalTail.V:.3f}", "-"),
        ("Horizontal tail", "Taper ratio", f"{HorizontalTail.taper_ratio:.3f}", "-"),
        ("Horizontal tail", "Moment arm", f"{HorizontalTail.Length:.2f}", "ft"),
        ("Horizontal tail", "Input mid-chord sweep", f"{HorizontalTail.SweepMidChord:.4f}", "rad"),
        ("Horizontal tail", "Thickness/chord (t/c)", f"{HorizontalTail.tc:.3f}", "-"),

        ("Vertical tail", "Aspect ratio", f"{VerticalTail.AspectRatio:.3f}", "-"),
        ("Vertical tail", "Tail volume coefficient", f"{VerticalTail.V:.3f}", "-"),
        ("Vertical tail", "Taper ratio", f"{VerticalTail.taper_ratio:.3f}", "-"),
        ("Vertical tail", "Moment arm", f"{VerticalTail.Length:.2f}", "ft"),
        ("Vertical tail", "Input mid-chord sweep", f"{VerticalTail.SweepMidChord:.4f}", "rad"),
        ("Vertical tail", "Thickness/chord (t/c)", f"{VerticalTail.tc:.3f}", "-"),
    ])

    print_table("Calculated geometry", [
            ("Fuselage", "Fineness ratio", f"{fuselage.FinenessRatio:.3f}", "-"),
            ("Fuselage", "Wetted area", f"{fuselage.WetArea:.1f}", "ft^2"),

            ("Wing", "Area", f"{wing.Area:.1f}", "ft^2"),
            ("Wing", "Span", f"{wing.Span:.2f}", "ft"),
            ("Wing", "Root chord", f"{wing.C_root:.2f}", "ft"),
            ("Wing", "Tip chord", f"{wing.C_tip:.2f}", "ft"),
            ("Wing", "Mean aerodynamic chord", f"{wing.Mac:.2f}", "ft"),
            ("Wing", "MAC spanwise location (Y)", f"{wing.Y_bar:.2f}", "ft"),
            ("Wing", "MAC longitudinal location (X)", f"{wing.X_bar:.2f}", "ft"),
            ("Wing", "Taper-induced initial sweep", f"{wing.initial_sweep:.4f}", "rad"),
            ("Wing", "Wetted area", f"{wing.WetArea:.1f}", "ft^2"),

            ("Horizontal tail", "Area", f"{horizontal_tail.Area:.1f}", "ft^2"),
            ("Horizontal tail", "Span", f"{horizontal_tail.Span:.2f}", "ft"),
            ("Horizontal tail", "Root chord", f"{horizontal_tail.C_root:.2f}", "ft"),
            ("Horizontal tail", "Tip chord", f"{horizontal_tail.C_tip:.2f}", "ft"),
            ("Horizontal tail", "Mean aerodynamic chord", f"{horizontal_tail.Mac:.2f}", "ft"),
            ("Horizontal tail", "MAC spanwise location (Y)", f"{horizontal_tail.Y_bar:.2f}", "ft"),
            ("Horizontal tail", "MAC longitudinal location (X)", f"{horizontal_tail.X_bar:.2f}", "ft"),
            ("Horizontal tail", "Taper-induced initial sweep", f"{horizontal_tail.initial_sweep:.4f}", "rad"),
            ("Horizontal tail", "Wetted area", f"{horizontal_tail.WetArea:.1f}", "ft^2"),

            ("Vertical tail", "Area", f"{vertical_tail.Area:.1f}", "ft^2"),
            ("Vertical tail", "Span", f"{vertical_tail.Span:.2f}", "ft"),
            ("Vertical tail", "Root chord", f"{vertical_tail.C_root:.2f}", "ft"),
            ("Vertical tail", "Tip chord", f"{vertical_tail.C_tip:.2f}", "ft"),
            ("Vertical tail", "Mean aerodynamic chord", f"{vertical_tail.Mac:.2f}", "ft"),
            ("Vertical tail", "MAC spanwise location (Y)", f"{vertical_tail.Y_bar:.2f}", "ft"),
            ("Vertical tail", "MAC longitudinal location (X)", f"{vertical_tail.X_bar:.2f}", "ft"),
            ("Vertical tail", "Taper-induced initial sweep", f"{vertical_tail.initial_sweep:.4f}", "rad"),
            ("Vertical tail", "Wetted area", f"{vertical_tail.WetArea:.1f}", "ft^2"),
    ])
