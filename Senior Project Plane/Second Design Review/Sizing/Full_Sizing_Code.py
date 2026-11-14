"""Run constraint sizing -> wing/tail geometry -> component drag buildup.

Install: python -m pip install numpy matplotlib ambiance
Run:     python integrated_aircraft_design.py

Imperial working units: ft, s, lbf, slug, shaft horsepower (550 ft*lbf/s).
The constraint equations and empirical assumptions are retained from the supplied
scripts; this integration does not validate their regulatory applicability.
Constraint sizing, geometry, and drag repeat until the CDmin feedback residual
and changes in cruise L/D, wing area, and required installed power converge.
MTOW and mission weight fractions remain the supplied fixed inputs.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import warnings
import csv

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from ambiance import Atmosphere


# SHARED INPUTS: change aircraft and mission assumptions here.
inputs = NS(
    MTOW_lbf=50319,
    AR=9.0,
    e=0.85,
    M_cruise=0.55,
    cruise_altitude_ft=28000.0,
    CD0_constraint=0.020,       # Initial guess; updated by the convergence loop
    eta_prop_cruise=0.90,
    alpha_power_cruise=1.0,    # Available cruise power / installed sea-level power
    total_engine_power_hp=8000.0,  # TOTAL across both engines; representative limit
    takeoff_altitude_ft=0.0,
    takeoff_field_length_ft=4500.0,
    landing_distance_ft=3500.0,
    CLmax_TO=2.0,
    CLmax_landing=2.5,
    eta_eff_TO=0.65,            # Representative thrust-to-shaft-power conversion
    Vref_TO_factor=1.10,
    f_TO=0.970,
    f_climb=0.985,
    f_cruise=0.932134858,
    f_land=0.995,
    beta_takeoff=1.0,
    taper_ratio=0.5,
    AR_ht=4.4,
    V_ht=0.914,
    taper_ratio_ht=0.462,
    l_ht_ft=40.47,
    AR_vt=1.766,
    V_vt=0.0934,
    taper_ratio_vt=0.463,
    l_vt_ft=40.47,
    fuselage_length_ft=86.0,
    fuselage_diameter_ft=9.0,
)

# CONVERGENCE SETTINGS: 1e-4 means 0.01% relative tolerance.
convergence = NS(
    relative_tolerance=1e-4,
    max_iterations=100,
    relaxation=0.5,  # 1.0 = full update; smaller values damp changes
)

# Drag assumptions, separate from the geometry calculated below.
wing = NS(tcRoot=0.15, tcTip=0.15, exposedPlanformFraction=1.0,
          wetAreaMultiplier=1.07)
tail = NS(tcHT=0.09, tcVT=0.09, exposedFractionHT=1.0,
          exposedFractionVT=1.0, wetAreaMultiplierHT=1.05,
          wetAreaMultiplierVT=1.05)
IF = NS(wing=1.20, fuselage=1.00, HT=1.04, VT=1.04)  # Provisional supplied factors
fuselage = NS(stationX_ft=np.array([], dtype=float),
              stationD_ft=np.array([], dtype=float))
skin = NS(method="fullyTurbulent", XtrOverC=np.full(4, np.nan), k_ft=2.08e-5)
formFactor = NS(liftingSurfaceMethod="Eq15-62")
crud = NS(enabled=True, factor=1.25)
polar = NS(CLminD=0.0, CLmin=0.0, CLmax=1.4, numPoints=201)
CDmisc = 0.0

FT_TO_M = 0.3048
LBF_TO_N = 4.4482216152605
SLUG_TO_KG = LBF_TO_N / FT_TO_M
PA_TO_PSF = FT_TO_M**2 / LBF_TO_N
KNOT_TO_FPS = 1852.0 / 3600.0 / FT_TO_M
OUTPUT_DIR = Path(__file__).resolve().parent / "aircraft_outputs"


def atmosphere_imperial(altitude_ft):
    """Return scalar ISA properties in consistent imperial units."""
    atm = Atmosphere(altitude_ft * FT_TO_M)
    return NS(
        rho=atm.density.item() * FT_TO_M**3 / SLUG_TO_KG,
        mu=atm.dynamic_viscosity.item() * PA_TO_PSF,
        a=atm.speed_of_sound.item() / FT_TO_M,
        T_R=atm.temperature.item() * 1.8,
        p_psf=atm.pressure.item() * PA_TO_PSF,
    )


def trapezoidal_geometry(AR, S, taper_ratio, vertical=False):
    """Geometry relative to root leading edge; original unswept trailing edge.

    Horizontal b is full span; vertical b is the height of one fin.
    LE sweep caused by taper is distinct from quarter-chord sweep.
    """
    if AR <= 0 or S <= 0 or taper_ratio <= 0:
        raise ValueError("Aspect ratio, area, and taper ratio must be positive.")
    b = np.sqrt(AR * S)
    root = 2.0 * S / (b * (1.0 + taper_ratio))
    tip = root * taper_ratio
    panel_span = b if vertical else b / 2.0
    sweep_LE = np.arctan((root - tip) / panel_span)
    sweep_C4 = np.arctan(0.75 * (root - tip) / panel_span)
    mac = 2.0 / 3.0 * root * (1.0 + taper_ratio + taper_ratio**2) / (1.0 + taper_ratio)
    y_mac = panel_span / 3.0 * (1.0 + 2.0 * taper_ratio) / (1.0 + taper_ratio)
    return NS(S_ft2=S, span_ft=b, root_ft=root, tip_ft=tip, MAC_ft=mac,
              y_MAC_ft=y_mac, x_MAC_ft=y_mac * np.tan(sweep_LE),
              sweep_LE_deg=np.rad2deg(sweep_LE), sweep_C4_deg=np.rad2deg(sweep_C4))


# CONVERGENCE LOOP: constraints -> geometry -> drag -> updated CDmin.
if (not np.isfinite(convergence.relative_tolerance)
        or convergence.relative_tolerance <= 0
        or not 0 < convergence.relaxation <= 1
        or not isinstance(convergence.max_iterations, int)
        or convergence.max_iterations < 2):
    raise ValueError("Use positive tolerance, relaxation in (0, 1], and at least 2 iterations.")
if not np.isfinite(inputs.CD0_constraint) or inputs.CD0_constraint <= 0:
    raise ValueError("The initial CD0 guess must be finite and positive.")
CDmin_guess = inputs.CD0_constraint
previous = None
history = []
converged = False
print("\nIteration  CDmin used  CDmin buildup  Cruise L/D  S [ft^2]  Max relative error")
for iteration in range(1, convergence.max_iterations + 1):
    # 1. CONSTRAINT SIZING
    sl = atmosphere_imperial(0.0)
    to_atm = atmosphere_imperial(inputs.takeoff_altitude_ft)
    cruise_atm = atmosphere_imperial(inputs.cruise_altitude_ft)
    beta_takeoff = inputs.beta_takeoff
    beta_cruise = inputs.f_TO * inputs.f_climb
    beta_landing = beta_cruise * inputs.f_cruise * inputs.f_land
    fuel_fraction_mission = 1.0 - beta_landing
    fuel_fraction_sized = 1.06 * fuel_fraction_mission

    # This same condition and weight fraction are used in the drag calculation.
    flight = NS(altitude_ft=inputs.cruise_altitude_ft,
                Mach=inputs.M_cruise,
                weight_lbf=inputs.MTOW_lbf * beta_cruise)
    V_cruise = flight.Mach * cruise_atm.a
    flight.TAS_kts = V_cruise / KNOT_TO_FPS
    q_cruise = 0.5 * cruise_atm.rho * V_cruise**2
    K = 1.0 / (np.pi * inputs.AR * inputs.e)
    W_S = np.linspace(1.0, 200.0, 1000)  # MTOW / wing area [lbf/ft^2]

    # Rebuild cruise L/D at EVERY candidate wing loading using the updated polar.
    # A single L/D from the previous design point is not valid across this curve.
    CL_candidates = beta_cruise * W_S / q_cruise
    CD_candidates = CDmin_guess + K * (CL_candidates - polar.CLminD)**2
    LD_candidates = CL_candidates / CD_candidates
    P_W_cruise = (V_cruise * beta_cruise
                  / (550.0 * inputs.eta_prop_cruise * inputs.alpha_power_cruise * LD_candidates))
    sigma_TO = to_atm.rho / sl.rho
    V_stall_TO = np.sqrt(2.0 * beta_takeoff * W_S / (to_atm.rho * inputs.CLmax_TO))
    V_ref_TO = inputs.Vref_TO_factor * V_stall_TO
    T_W_takeoff = (37.5 * beta_takeoff**2 * W_S
                   / (sigma_TO * inputs.CLmax_TO * inputs.takeoff_field_length_ft))
    P_W_takeoff = T_W_takeoff * V_ref_TO / (550.0 * inputs.eta_eff_TO)

    # Supplied Roskam landing-distance correlation: distance in ft, speed in knots.
    # Landing remains evaluated at sea level, independently of takeoff altitude.
    V_approach_kts = np.sqrt(inputs.landing_distance_ft / 0.3)
    V_stall_landing_fps = V_approach_kts / 1.3 * KNOT_TO_FPS
    W_S_landing = (0.5 * sl.rho * V_stall_landing_fps**2
                   * inputs.CLmax_landing / beta_landing)
    P_W_required = np.maximum(P_W_cruise, P_W_takeoff)
    engine_limit = inputs.total_engine_power_hp / inputs.MTOW_lbf
    feasible = (W_S <= W_S_landing) & (P_W_required <= engine_limit)
    if not np.any(feasible):
        raise ValueError("No feasible point: review landing, cruise, takeoff, or engine inputs.")
    i_design = np.flatnonzero(feasible)[-1]
    W_S_design = float(W_S[i_design])
    P_W_design = float(P_W_required[i_design])
    S_wing = inputs.MTOW_lbf / W_S_design
    P_shaft_hp = P_W_design * inputs.MTOW_lbf


    # 2. GEOMETRY: all areas come from the selected constraint design point.


    wing_geom = trapezoidal_geometry(inputs.AR, S_wing, inputs.taper_ratio)
    S_ht = inputs.V_ht * S_wing * wing_geom.MAC_ft / inputs.l_ht_ft
    S_vt = inputs.V_vt * S_wing * wing_geom.span_ft / inputs.l_vt_ft
    ht_geom = trapezoidal_geometry(inputs.AR_ht, S_ht, inputs.taper_ratio_ht)
    vt_geom = trapezoidal_geometry(inputs.AR_vt, S_vt, inputs.taper_ratio_vt, vertical=True)

    aircraft = NS(Sref_ft2=S_wing, Swing_ft2=S_wing, span_ft=wing_geom.span_ft,
                  AR=inputs.AR, SHT_ft2=S_ht, SVT_ft2=S_vt,
                  fuselageLength_ft=inputs.fuselage_length_ft,
                  fuselageDmax_ft=inputs.fuselage_diameter_ft)
    wing.tcMean = 0.5 * (wing.tcRoot + wing.tcTip)
    wing.meanChord_ft = wing_geom.MAC_ft
    wing.sweepC4_deg = wing_geom.sweep_C4_deg
    tail.meanChordHT_ft = ht_geom.MAC_ft
    tail.meanChordVT_ft = vt_geom.MAC_ft
    tail.sweepC4_HT_deg = ht_geom.sweep_C4_deg
    tail.sweepC4_VT_deg = vt_geom.sweep_C4_deg


    # 3. DRAG: uses calculated geometry, shared cruise state, AR, and e.
    rho, mu, a = cruise_atm.rho, cruise_atm.mu, cruise_atm.a
    V, Mach, q = V_cruise, flight.Mach, q_cruise
    component = ["Wing", "Fuselage", "Horizontal tail", "Vertical tail"]
    Lref_ft = np.array([wing.meanChord_ft, aircraft.fuselageLength_ft,
                        tail.meanChordHT_ft, tail.meanChordVT_ft])
    ReActual = rho * V * Lref_ft / mu
    ReCutoff = 38.21 * (Lref_ft / skin.k_ft)**1.053
    ReUsed = np.minimum(ReActual, ReCutoff)
    SwetWing = 2 * wing.wetAreaMultiplier * S_wing * wing.exposedPlanformFraction
    SwetHT = 2 * tail.wetAreaMultiplierHT * S_ht * tail.exposedFractionHT
    SwetVT = 2 * tail.wetAreaMultiplierVT * S_vt * tail.exposedFractionVT
    x = np.asarray(fuselage.stationX_ft, dtype=float).ravel()
    diameters = np.asarray(fuselage.stationD_ft, dtype=float).ravel()
    if x.size or diameters.size:
        if (x.size < 2 or x.size != diameters.size or not np.all(np.isfinite(x))
                or not np.all(np.isfinite(diameters))
                or np.any(np.diff(x) <= 0) or np.any(diameters < 0)):
            raise ValueError("Provide matching finite fuselage stations, increasing x, and nonnegative diameters.")
        r = diameters / 2.0
        SwetFuselage = np.sum(np.pi * (r[:-1] + r[1:])
                              * np.sqrt(np.diff(x)**2 + np.diff(r)**2))
    else:
        SwetFuselage = np.pi * aircraft.fuselageDmax_ft * aircraft.fuselageLength_ft
    Swet = np.array([SwetWing, SwetFuselage, SwetHT, SwetVT])
    IFvec = np.array([IF.wing, IF.fuselage, IF.HT, IF.VT])
    Cf_turbulent = 0.455 / (np.log10(ReUsed)**2.58 * (1 + 0.144 * Mach**2)**0.65)
    if skin.method.lower() == "fullyturbulent":
        Cf = Cf_turbulent
    elif skin.method.lower() == "mixed":
        xtr = np.asarray(skin.XtrOverC, dtype=float)
        if (xtr.shape != (4,) or np.any(~np.isfinite(xtr))
                or np.any(xtr < 0) or np.any(xtr > 1)):
            raise ValueError("Mixed flow requires four XtrOverC values between 0 and 1.")
        if Mach > 0.5:
            raise ValueError("Mixed flow above Mach 0.5 requires the book's additional correction.")
        x0 = 36.9 * xtr**0.625 * (1.0 / ReUsed)**0.375
        Cf = 0.074 / ReUsed**0.2 * (1 - (xtr - x0))**0.8
    else:
        raise ValueError("skin.method must be 'fullyTurbulent' or 'mixed'.")

    tcLift = np.array([wing.tcMean, tail.tcHT, tail.tcVT])
    sweepC4_deg = np.array([wing.sweepC4_deg, tail.sweepC4_HT_deg, tail.sweepC4_VT_deg])
    if formFactor.liftingSurfaceMethod.lower() == "eq15-62":
        if np.any(tcLift > 0.21):
            warnings.warn("Eq. 15-62 exceeds its stated t/c <= 0.21 range.")
        FF_lift = 1 + 2.7 * tcLift + 100 * tcLift**4
    elif formFactor.liftingSurfaceMethod.lower() == "eq15-63":
        sweep = np.deg2rad(sweepC4_deg)
        radicand = 1 - Mach**2 * np.cos(sweep)**2
        if np.any(radicand <= 0):
            raise ValueError("Eq. 15-63 is outside its subsonic domain.")
        sweepTerm = (2 - Mach**2) * np.cos(sweep) / np.sqrt(radicand)
        FF_lift = 1 + sweepTerm * tcLift + 100 * tcLift**4
    else:
        raise ValueError("Choose formFactor 'Eq15-62' or 'Eq15-63'.")
    finenessRatio = aircraft.fuselageLength_ft / aircraft.fuselageDmax_ft
    FF_fuselage = 1 + 60 / finenessRatio**3 + finenessRatio / 400
    FF = np.array([FF_lift[0], FF_fuselage, FF_lift[1], FF_lift[2]])
    CD_component = Cf * FF * IFvec * Swet / S_wing
    CDminBeforeCRUD = np.sum(CD_component) + CDmisc
    CDmin = CDminBeforeCRUD * (crud.factor if crud.enabled else 1.0)
    CL = np.linspace(polar.CLmin, polar.CLmax, polar.numPoints)
    CD = CDmin + K * (CL - polar.CLminD)**2
    CLcruise = flight.weight_lbf / (q * S_wing)
    CDcruise = CDmin + K * (CLcruise - polar.CLminD)**2
    LDcruise = CLcruise / CDcruise
    Dcruise_lbf = q * S_wing * CDcruise
    P_cruise_shaft_hp = Dcruise_lbf * V / (550.0 * inputs.eta_prop_cruise)
    P_cruise_installed_hp = P_cruise_shaft_hp / inputs.alpha_power_cruise

    # Check the actual feedback residual BEFORE applying relaxation. This prevents
    # small relaxation factors from falsely indicating convergence.
    current = np.array([LDcruise, S_wing, P_shaft_hp])
    if not np.all(np.isfinite(current)) or not np.isfinite(CDmin) or CDmin <= 0:
        raise ValueError(f"Non-finite or nonphysical result at iteration {iteration}.")
    cd_error = abs(CDmin - CDmin_guess) / max(abs(CDmin), 1e-12)
    changes = (np.full(3, np.inf) if previous is None else
               np.abs(current - previous) / np.maximum(np.abs(current), 1e-12))
    max_error = max(cd_error, float(np.max(changes)))
    history.append(dict(iteration=iteration, CDmin_used=CDmin_guess, CDmin=CDmin,
                        LDcruise=LDcruise, S_wing_ft2=S_wing,
                        P_shaft_hp=P_shaft_hp, CDmin_relative_error=cd_error,
                        LD_relative_change=changes[0], area_relative_change=changes[1],
                        power_relative_change=changes[2], max_relative_error=max_error))
    print(f"{iteration:9d}  {CDmin_guess:.6f}    {CDmin:.6f}       "
          f"{LDcruise:7.3f}  {S_wing:8.3f}  {max_error:.3e}")
    if previous is not None and max_error <= convergence.relative_tolerance:
        converged = True
        break
    previous = current.copy()
    CDmin_guess += convergence.relaxation * (CDmin - CDmin_guess)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
with (OUTPUT_DIR / "convergence_history.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(history[0]))
    writer.writeheader()
    writer.writerows(history)
if not converged:
    raise RuntimeError(
        f"No convergence after {convergence.max_iterations} iterations. "
        f"Final relative error={max_error:.3e}; required={convergence.relative_tolerance:.3e}. "
        "See convergence_history.csv; consider smaller relaxation or reviewing the sizing inputs."
    )
print(f"Converged in {iteration} iterations (relative tolerance {convergence.relative_tolerance:.1e}).")
if CLcruise > polar.CLmax:
    warnings.warn("Cruise CL exceeds the specified polar CLmax.")
if P_cruise_installed_hp > P_shaft_hp * (1 + convergence.relative_tolerance):
    warnings.warn("Calculated cruise power exceeds the sized installed power beyond tolerance.")
if P_cruise_installed_hp > inputs.total_engine_power_hp * (1 + convergence.relative_tolerance):
    warnings.warn("Calculated cruise power exceeds the representative engine limit beyond tolerance.")


# 4. RESULTS AND PLOTS
print("\nCONSTRAINT SIZING")
print(f"Cruise: Mach {Mach:.3f}, {flight.altitude_ft:,.0f} ft, {flight.TAS_kts:.2f} KTAS")
print(f"MTOW: {inputs.MTOW_lbf:,.2f} lbf; cruise weight: {flight.weight_lbf:,.2f} lbf")
print(f"Landing W/S limit: {W_S_landing:.3f} lbf/ft^2")
print(f"Selected W/S: {W_S_design:.3f} lbf/ft^2; P/W: {P_W_design:.4f} hp/lbf")
print(f"Required installed power (converged constraints): {P_shaft_hp:,.2f} hp total")
print(f"Mission fuel fraction: {fuel_fraction_mission:.5f}; with sizing factor: {fuel_fraction_sized:.5f}")
print("\nGEOMETRY")
for name, geom in [("Wing", wing_geom), ("Horizontal tail", ht_geom), ("Vertical tail", vt_geom)]:
    print(f"{name}: area={geom.S_ft2:.3f} ft^2; span/height={geom.span_ft:.3f} ft")
    print(f"  Root={geom.root_ft:.3f} ft; tip={geom.tip_ft:.3f} ft; MAC={geom.MAC_ft:.3f} ft")
    print(f"  MAC location: x={geom.x_MAC_ft:.3f} ft, y/height={geom.y_MAC_ft:.3f} ft")
    print(f"  LE sweep={geom.sweep_LE_deg:.3f} deg; quarter-chord sweep={geom.sweep_C4_deg:.3f} deg")
print("\nDRAG AT START OF CRUISE")
print(f"Initial CD0 guess: {inputs.CD0_constraint:.6f}; final sizing CDmin: {CDmin_guess:.6f}; buildup CDmin: {CDmin:.6f}")
print(f"Cruise CL={CLcruise:.5f}; CD={CDcruise:.5f}; L/D={LDcruise:.2f}")
print(f"Cruise drag={Dcruise_lbf:,.2f} lbf; required shaft power={P_cruise_shaft_hp:,.2f} hp")
print(f"Equivalent installed sea-level power at cruise: {P_cruise_installed_hp:,.2f} hp")

plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 10, "axes.linewidth": 0.8})
fig_constraint, ax = plt.subplots(figsize=(7, 4.5), dpi=150, constrained_layout=True)
cruise_line, = ax.plot(W_S, P_W_cruise, color="green", lw=1.6, label="Cruise limit (converged polar)")
takeoff_line, = ax.plot(W_S, P_W_takeoff, color="tab:blue", lw=1.6, label="Takeoff limit")
landing_line = ax.axvline(W_S_landing, color="black", lw=1.6, label="Landing limit")
engine_line = ax.axhline(engine_limit, color="gray", lw=1.6,
                        label=f"Representative engine limit ({inputs.total_engine_power_hp:,.0f} hp total)")
for line, color in [(cruise_line, "green"), (takeoff_line, "tab:blue"), (landing_line, "black")]:
    line.set_path_effects([pe.withTickedStroke(spacing=10, angle=585, length=0.6, foreground=color)])
engine_line.set_path_effects([pe.withTickedStroke(spacing=10, angle=505, length=0.6, foreground="gray")])
ax.scatter(W_S_design, P_W_design, s=65, c="red", edgecolors="black", zorder=6,
           label=f"Design: W/S={W_S_design:.2f}, P/W={P_W_design:.4f}")
ax.fill_between(W_S, P_W_required, engine_limit, where=feasible, color="green", alpha=0.10)
x_max = 1.05 * W_S_landing
x_min = min(20.0, 0.8 * W_S_design)
visible = (W_S >= x_min) & (W_S <= x_max)
y_top = 1.18 * max(engine_limit, np.max(P_W_required[visible]))
ax.set(xlim=(x_min, x_max), ylim=(0, y_top),
       xlabel=r"Wing loading, $W_{TO}/S$ [$\mathrm{lbf/ft^2}$]",
       ylabel=r"Installed shaft-power loading, $P_{SL}/W_{TO}$ [hp/lbf]")
ax.tick_params(direction="in", top=True, right=True)
ax.grid(True, color="0.87", lw=0.6)
ax.legend(loc="upper left", fontsize=8)

fig_polar, ax = plt.subplots(figsize=(6, 4.5), constrained_layout=True)
ax.plot(CD, CL, lw=1.8, label="Component-build-up polar")
ax.plot(CDcruise, CLcruise, "ro", label=f"Cruise L/D = {LDcruise:.2f}")
ax.set(xlabel=r"$C_D$", ylabel=r"$C_L$")
ax.grid(True, alpha=0.4)
ax.legend()

fig_components, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
ax.bar(component, CD_component)
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
ax.grid(True, axis="y", alpha=0.4)
ax.set_axisbelow(True)
ax.set_ylabel(r"Contribution to $C_D$ (common $S_{\mathrm{ref}}$; before CRUD)")
fig_convergence, axes = plt.subplots(2, 1, figsize=(6, 6), sharex=True, constrained_layout=True)
iterations = [row["iteration"] for row in history]
axes[0].plot(iterations, [row["CDmin_used"] for row in history], "o--", label="Sizing CDmin")
axes[0].plot(iterations, [row["CDmin"] for row in history], ".-", label="Buildup CDmin")
axes[0].set_ylabel(r"$C_{D\min}$")
axes[0].legend()
axes[1].plot(iterations, [row["LDcruise"] for row in history], "o-")
axes[1].set(xlabel="Iteration", ylabel="Cruise L/D")
for axis in axes:
    axis.grid(True, alpha=0.4)
for figure, filename in [(fig_constraint, "sizing_constraint_diagram_AIAA.png"),
                         (fig_polar, "drag_polar.png"),
                         (fig_components, "component_drag.png"),
                         (fig_convergence, "convergence.png")]:
    figure.savefig(OUTPUT_DIR / filename, dpi=300, facecolor="white", bbox_inches="tight")
print(f"\nPlots saved in: {OUTPUT_DIR}")
plt.show()
