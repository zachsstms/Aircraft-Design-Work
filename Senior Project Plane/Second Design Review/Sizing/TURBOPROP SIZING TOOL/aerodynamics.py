import numpy as np
from ambiance import Atmosphere
import pint
ureg = pint.UnitRegistry()

'''
    Needs to use SimpleNamespace for Fuselage, Wing, and Tail inputs. Needs Mach, Altitude, and Cruise Weight inputs as well.

    Fuselage Needs: Fuselage.Length, Fuselage.Diameter
    Wing Needs: Wing.tc, Wing.xc, Wing.Sweep, Wing.Mac, Wing.Span, Wing.Area
    HorizontalTail Needs: HorizontalTail.tc, HorizontalTail.SweepMidChord, HorizontalTail.Mac, HorizontalTail.Span
    VerticalTail Needs: VerticalTail.tc, VerticalTail.SweepMidChord, VerticalTail.Mac, VerticalTail.Span

    Outputs CDmin, L/D, drag polar
'''

def CDminFunct(Mach, Altitude, cruiseWeight, Fuselage, Wing, HorizontalTail, VerticalTail, plot=False):

    def get_Cf(Mach, Altitude, length): # provide altitude, length in ft. 
        alt_m = Altitude.to("meters").magnitude
        atm = Atmosphere(alt_m) # convert the altitude to meters for the Atmosphere tool
        density = (atm.density[0] * ureg("kg/m^3")).to("slug/ft^3").magnitude # kg/m^3 to slug/ft^3
        viscosity = (atm.dynamic_viscosity[0] * ureg("Pa * s")).to("slug/(ft*s)").magnitude # Pa*s to slug/(ft*s)
        velocity = (Mach * atm.speed_of_sound[0] * ureg("m/s")).to("ft/s").magnitude # m/s to ft/s

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
    Wing.WetArea = 2 * Wing.Area
    HorizontalTail.WetArea = 2 * HorizontalTail.Area
    VerticalTail.WetArea = 2 * VerticalTail.Area

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

    # Atmosphere returns SI; use slug/ft^3 and ft/s so q is in lbf/ft^2.
    atmosphere = Atmosphere(Altitude.to("meters").magnitude)
    density = (atmosphere.density[0] * ureg("kg/m^3")).to("slug/ft^3").magnitude
    velocity = (Mach * atmosphere.speed_of_sound[0] * ureg("m/s")).to("ft/s").magnitude
    q_cruise = 0.5 * density * velocity**2
    Cl_cruise = cruiseWeight / (q_cruise * Sref)
    Cd_cruise = CDmin + ((Cl_cruise**2) / (np.pi * Wing.AspectRatio * Wing.OswaldEfficiency))

    Cl_Cd_cruise = Cl_cruise / Cd_cruise
    if plot:
        from pathlib import Path
        import matplotlib as mpl
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        mpl.rcParams.update({
            'font.family': 'serif',
            'font.serif': ['STIX Two Text', 'Times New Roman', 'DejaVu Serif'],
            'mathtext.fontset': 'stix',
            'font.size': 12,
            'axes.labelsize': 10,
            'legend.fontsize': 10,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'axes.linewidth': 0.8,
        })
        output_dir = Path(__file__).resolve().parent / "Plots"
        output_dir.mkdir(parents=True, exist_ok=True)
        names = ["Fuselage", "Wing", "Horizontal tail", "Vertical tail"]
        surfaces = [Fuselage, Wing, HorizontalTail, VerticalTail]
        components = [s.Cf * s.FormFactor * s.InterferenceFactor * s.WetArea / Sref for s in surfaces]
        names.append("Misc. allowance")
        components.append((crudFactor - 1) * sum(components))

        # 1. Drag Polar
        fig = Figure(figsize=(7, 4.5), constrained_layout=True)
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        ax.plot(CdTotal, Cl, label="Drag polar")
        ax.plot(Cd_cruise, Cl_cruise, "ro", label=f"Cruise L/D = {Cl_Cd_cruise:.2f}")
        ax.set_xlabel("$C_D$"); ax.set_ylabel("$C_L$"); ax.grid(True); ax.legend()
        fig.savefig(output_dir / "drag_polar.png", dpi=200)

        # 2. Parasite Drag Breakdown
        fig = Figure(figsize=(7, 4.5), constrained_layout=True)
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        ax.bar(names, components)
        ax.set_ylabel("Contribution to $C_{D0}$"); ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.3)
        fig.savefig(output_dir / "drag_breakdown.png", dpi=200)

    return CDmin, CdTotal, Cl_Cd_cruise, Wing, Fuselage, HorizontalTail, VerticalTail
