"""
constraints.py
This code runs the constraint diagram. It is split into
stages of flight. 
Inputs:
MTOW
C_D0
AR
e
M_cruise
cruise alt
landing distance
landing altitude
takeoff distance
takeoff altitude
cruise prop efficiency
k

Outputs:
P/W
W/S
P
S
Diagram
"""


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from ambiance import Atmosphere
import pint
ureg = pint.UnitRegistry()
from pathlib import Path
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
plt.rcParams.update({
    'font.family': 'times new roman',
    'font.serif': ['STIX Two Text', 'Times New Roman', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 12,
    'axes.labelsize': 10,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'axes.linewidth': 0.8,
}) # plotting code (consistent)

    
def cruise_constraint(cruise_alt, M_cruise, alpha_P_cruise, cruise_weight_ratio,
                      eta_p_cruise, C_D0, k, W_S,):
    a_cruisealt = (Atmosphere(cruise_alt.to("meters").magnitude).speed_of_sound)*ureg("m/s").to("ft/s").magnitude # ISA to find speed of sound, convert to (ft/s)
    rho_cruisealt=Atmosphere(cruise_alt.to("meters").magnitude).density*ureg("kg/m^3").to("slug/ft^3").magnitude # ISA to find density at cruise altitude (slug/ft^3)
    V_cruise=M_cruise*a_cruisealt #ft/sec
    alpha_P_cruise=alpha_P_cruise # at altitude, there is a power penalty compared to takeoff
    q_cruise=0.5*rho_cruisealt*V_cruise**2 # dynamic pressure at cruise
    P_W_cruise =((V_cruise / (550 * eta_p_cruise * alpha_P_cruise))*
    (q_cruise*C_D0/W_S +(k*(W_S/q_cruise)*cruise_weight_ratio**2))) # the 550 is to get horsepower
    return P_W_cruise

# NOTES: Takeoff efficiency imbedded in reference values (constant of 1.5334) 
#ROSAKM PART 23 Correlation
def takeoff_constraint(takeoff_distance, sigma_TO, CL_max_TO, W_S):
    S_TOG = takeoff_distance/1.5334 # based on fig 3.4 and eqn 3.5 Roskam; constant from only dual prop references
    # Solve: 0.009*TOP_23**2 + 4.9*TOP_23 - S_TOG = 0 (eqn 3.4)
    a = 0.009
    b = 4.9
    c = -S_TOG
    TOP_23 = (-b + np.sqrt(b**2 - 4*a*c)) / (2*a)  
    P_W_takeoff = 1/((TOP_23 * sigma_TO * CL_max_TO) / W_S) #fit P_W_TO to wing loading sweep
    return P_W_takeoff 

def landing_constraint(landing_distance, rho_landing, CL_max_L, takeoff_weight_fraction,
                       climb_weight_fraction, cruise_weight_fraction, landing_weight_fraction):
    # LANDING CONSTRAINT LINE PART 25 ROSKAM
    #V_SL = np.sqrt(landing_distance / 0.3) * 1.68781  # kts to ft/sec, this is for part 23
    V_approach=np.sqrt(landing_distance/0.3)
    V_SL=V_approach/1.3 * 1.68791 # kts to ft/s 
    weight_ratio = (takeoff_weight_fraction * climb_weight_fraction * cruise_weight_fraction * landing_weight_fraction)
    W_S_landing = (0.5 * rho_landing * V_SL**2 * CL_max_L) * (1 / weight_ratio)
    return float(np.squeeze(W_S_landing))

# need to find the design points
def design_point(W_S, W_S_landing, P_W_cruise, P_W_takeoff, MTOW):
    # Select the highest wing loading allowed by the landing constraint.
    feasible = W_S <= W_S_landing
    if not np.any(feasible):
        raise ValueError("Landing constraint lies outside the W/S grid.")

    # At each wing loading, satisfy both the cruise and takeoff constraints.
    P_W_required = np.maximum(P_W_cruise, P_W_takeoff)

    i_design = np.argmax(np.where(feasible, W_S, -np.inf))
    W_S_design = W_S[i_design]
    P_W_design = P_W_required[i_design]

    MTOW_val = MTOW.to("lbf").magnitude if hasattr(MTOW, "to") else MTOW
    P_design = MTOW_val * P_W_design
    S_design = MTOW_val / W_S_design

    return W_S_design, P_W_design, P_design, S_design, P_W_required

# ---------------------------------------------------------------------

# PULLING EVERYTHING TOGETHER
def constraint_analysis(MTOW, C_D0, AR, e, M_cruise,
                        cruise_alt,
                        landing_distance,
                        landing_altitude,
                        takeoff_distance,
                        takeoff_altitude, CL_max_TO, CL_max_L, eta_p_cruise,
                        k,
                        cruise_weight_fraction,
                        cruise_weight_ratio,
                        takeoff_weight_fraction,
                        climb_weight_fraction,
                        landing_weight_fraction,
                        alpha_P_cruise,
                        plot=True):
    sealevel = Atmosphere(0) # gives SI
    takeoff_atmosphere = Atmosphere(takeoff_altitude.to("meters").magnitude) # compute the takeoff and landing atmospheric parameters 
    landing_atmosphere = Atmosphere(landing_altitude.to("meters").magnitude)
    sigma_TO = takeoff_atmosphere.density.item() / sealevel.density.item()
    rho_landing = (landing_atmosphere.density.item() * ureg("kg/m^3")).to("slug/ft^3").magnitude # convert to Imperial units
    W_S_landing = landing_constraint(
        landing_distance, rho_landing, CL_max_L, takeoff_weight_fraction,
        climb_weight_fraction, cruise_weight_fraction, landing_weight_fraction # call landing constraint function
    )
    # dynamic linspace for wing loading
    W_S = np.unique(np.append(np.linspace(W_S_landing / 2000, 1.2 * W_S_landing, 2000), W_S_landing)) 

    # Assign outputs from each stage
    P_W_cruise = cruise_constraint(
        cruise_alt, M_cruise, alpha_P_cruise, cruise_weight_ratio,
        eta_p_cruise, C_D0, k, W_S
    )
    P_W_takeoff = takeoff_constraint(
        takeoff_distance, sigma_TO, CL_max_TO, W_S
    )
    W_S_design, P_W_design, P_design, S_design, P_W_required = design_point(
        W_S, W_S_landing, P_W_cruise, P_W_takeoff, MTOW
    )

    fig = None
    if plot: #if the plot is enabled it will call the plotting function (which is at the end of the script)
        fig = constraint_diagram(
            W_S, W_S_design, P_W_design, P_W_takeoff, P_W_cruise, W_S_landing, MTOW, P_W_required
        )

    return {
        "W_S_design": W_S_design,
        "P_W_design": P_W_design,
        "P_design": P_design,
        "S_design": S_design,
        "W_S_landing": W_S_landing,
        "fig": fig,
    }

#-------------------------------------------------------------------

# plotting function (taken from our old plots)
 
def constraint_diagram(W_S, W_S_design, P_W_design, P_W_takeoff, P_W_cruise, W_S_landing, MTOW, P_W_required):
    fig = Figure(figsize=(7.0, 4.5), dpi=200, constrained_layout=True)
    FigureCanvasAgg(fig)
    ax = fig.subplots()

    cruise_line, = ax.plot(W_S, P_W_cruise, color="green", lw=1.6)
    takeoff_line, = ax.plot(W_S, P_W_takeoff, color="tab:blue", lw=1.6, zorder=3)
    landing_line = ax.axvline(W_S_landing, color="black", lw=1.6, zorder=3)

    for line, color in [
        (cruise_line, "green"),
        (takeoff_line, "tab:blue"),
        (landing_line, "black"),
    ]:
        line.set_path_effects([
            pe.withTickedStroke(spacing=10, angle=585, length=0.6, foreground=color)
        ])

    ax.scatter(
        W_S_design, P_W_design, s=80, marker="o",
        facecolor="red", edgecolor="black", linewidth=1.1, zorder=6,
        label=rf"Design point: $W/S = {W_S_design:.1f}\ \mathrm{{lbf/ft^2}}, \ P/W = {P_W_design:.2f}\ \mathrm{{hp/lbf}}$"
    )

    x_min = min(0.2 * W_S_landing, 0.5 * W_S_design)
    x_visible = (W_S >= x_min) & (W_S <= 1.05 * W_S_landing)
    y_top = 1.12 * np.max(P_W_required[x_visible])

    ax.set_xlim(x_min, 1.05 * W_S_landing)
    ax.set_ylim(0, y_top)
    ax.set_xlabel(r"Wing loading, $W_{TO}/S$ [$\mathrm{lbf/ft^2}$]")
    ax.set_ylabel(r"Installed shaft-power loading, $P_{SL}/W_{TO}$ [$\mathrm{shp/lbf}$]")
    ax.tick_params(which="both", direction="in", top=True, right=True, width=0.8, length=4)
    ax.grid(True, which="major", color="0.87", linewidth=0.6, zorder=0)

    x_label = 0.78 * W_S_landing
    ax.annotate("Cruise Limit", xy=(x_label, np.interp(x_label, W_S, P_W_cruise)),
                xytext=(6, 5), textcoords="offset points", color="green", va="center")
    ax.annotate("Takeoff Limit", xy=(x_label, np.interp(x_label, W_S, P_W_takeoff)),
                xytext=(6, -10), textcoords="offset points", color="tab:blue", va="center")
    ax.annotate("Landing Limit", xy=(W_S_landing, 0.75 * y_top),
                xytext=(10, -76), textcoords="offset points", rotation=90, color="black", va="center")
    output_dir = Path(__file__).resolve().parent / "Plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "constraint_diagram.png")

    return fig
