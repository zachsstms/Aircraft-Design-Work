"""Preliminary AeroSandbox sizing model for the 60-seat Part 25 turboprop.

Model scope
-----------
* Fixed MTOW from the external mission / empty-weight sizing loop.
* Parabolic clean cruise polar: CD = CD0 + CL^2 / (pi * e * AR).
* Cruise power constraint at the start-of-cruise mission weight.
* Roskam-style preliminary Part 25 TOFL screening correlation, mapped to
  shaft power at a representative takeoff speed.
* Roskam-style landing wing-loading limit used in the current notebook.

The takeoff power conversion is deliberately exposed as `eta_eff_to`; it is a
placeholder for a later propeller/engine-deck model, not a propeller map.
All calculations internal to AeroSandbox are SI.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import aerosandbox as asb
import aerosandbox.numpy as np
import casadi as cas
import matplotlib.pyplot as plt


# Unit conversions used only at the model boundary.
LBF_TO_N = 4.4482216152605
FT_TO_M = 0.3048
FT2_TO_M2 = FT_TO_M**2
PSF_TO_PA = LBF_TO_N / FT2_TO_M2
HP_TO_W = 745.6998715822702
KT_TO_MPS = 0.514444


@dataclass(frozen=True)
class SizingInputs:
    """Inputs for one preliminary constraint-analysis case."""

    # Converged mass-sizing result; this script does not rerun the Raymer loop.
    mtow_lbf: float = 50696.72136

    # Cruise condition and clean polar.
    cruise_altitude_ft: float = 20000.0
    cruise_mach: float = 0.48
    cd0_clean: float = 0.020
    aspect_ratio: float = 10.0
    oswald_efficiency: float = 0.85
    eta_prop_cruise: float = 0.90
    alpha_power_cruise: float = 1.0

    # Mission-weight schedule.
    f_takeoff: float = 0.970
    f_climb: float = 0.985
    f_cruise: float = 0.932134858
    f_landing: float = 0.995

    # Part 25 takeoff-field-length screening model.
    tofl_required_ft: float = 5000.0
    sigma_takeoff: float = 1.0              # SL/standard-day baseline
    clmax_takeoff: float = 1.70
    eta_eff_takeoff: float = 0.75           # sensitivity variable; not a prop map
    alpha_power_takeoff: float = 1.0        # engine-deck power fraction
    v_ref_factor_takeoff: float = 1.20

    # Landing model. This is the *unfactored* distance used by the current
    # Roskam-style relation. Set it deliberately from your runway definition.
    landing_distance_unfactored_ft: float = 0.60 * 4500.0
    clmax_landing: float = 2.15

    # Practical numerical bounds; they are not aircraft requirements.
    wing_area_bounds_m2: tuple[float, float] = (50.0, 220.0)
    installed_power_bounds_MW: tuple[float, float] = (0.5, 12.0)

    @property
    def beta_cruise(self) -> float:
        """Start-of-cruise weight fraction, where cruise power is largest."""
        return self.f_takeoff * self.f_climb

    @property
    def beta_landing(self) -> float:
        return self.f_takeoff * self.f_climb * self.f_cruise * self.f_landing


def solve_sizing(inputs: SizingInputs) -> dict[str, float]:
    """Minimize installed shaft power subject to cruise, TOFL, and landing.

    Returns a plain numerical dictionary so it is convenient to tabulate,
    plot, or feed into a parameter sweep.
    """
    mtow_N = inputs.mtow_lbf * LBF_TO_N
    k = 1.0 / (np.pi * inputs.oswald_efficiency * inputs.aspect_ratio)

    # AeroSandbox's differentiable 1976-COESA atmosphere model.
    atmo_cruise = asb.Atmosphere(altitude=inputs.cruise_altitude_ft * FT_TO_M)
    rho_cruise = atmo_cruise.density()
    v_cruise = inputs.cruise_mach * atmo_cruise.speed_of_sound()
    q_cruise = 0.5 * rho_cruise * v_cruise**2

    atmo_sl = asb.Atmosphere(altitude=0.0)
    rho_sl = atmo_sl.density()

    # Existing preliminary landing relationship, evaluated as a scalar limit.
    v_app_mps = np.sqrt(inputs.landing_distance_unfactored_ft / 0.30) * KT_TO_MPS
    v_stall_landing = v_app_mps / 1.30
    ws_landing_limit = (
        0.5 * rho_sl * v_stall_landing**2 * inputs.clmax_landing
        / inputs.beta_landing
    )

    opti = asb.Opti()
    wing_area_m2 = opti.variable(
        init_guess=110.0,
        lower_bound=inputs.wing_area_bounds_m2[0],
        upper_bound=inputs.wing_area_bounds_m2[1],
        scale=100.0,
        category="Geometry",
    )
    installed_power_W = opti.variable(
        init_guess=4.0e6,
        lower_bound=inputs.installed_power_bounds_MW[0] * 1e6,
        upper_bound=inputs.installed_power_bounds_MW[1] * 1e6,
        scale=1.0e6,
        category="Propulsion",
    )

    ws = mtow_N / wing_area_m2                       # N/m^2
    pw = installed_power_W / mtow_N                  # W/N

    # Clean, start-of-cruise power required, normalized by MTOW.
    pw_cruise = (
        v_cruise
        / (inputs.eta_prop_cruise * inputs.alpha_power_cruise)
        * (
            q_cruise * inputs.cd0_clean / ws
            + k * inputs.beta_cruise**2 * ws / q_cruise
        )
    )

    # Roskam preliminary Part 25 takeoff-field-length relation gives T/W:
    # TOFL = 37.5 (W/S)_psf / [sigma CLmax_TO (T/W)_TO].
    # Map the required thrust to shaft power at a stated equivalent speed.
    ws_psf = ws / PSF_TO_PA
    tw_takeoff = (
        37.5 * ws_psf
        / (inputs.sigma_takeoff * inputs.clmax_takeoff * inputs.tofl_required_ft)
    )
    v_stall_takeoff = np.sqrt(2.0 * ws / (rho_sl * inputs.clmax_takeoff))
    v_ref_takeoff = inputs.v_ref_factor_takeoff * v_stall_takeoff
    pw_takeoff = (
        tw_takeoff * v_ref_takeoff
        / (inputs.eta_eff_takeoff * inputs.alpha_power_takeoff)
    )

    opti.subject_to([
        pw >= pw_cruise,
        pw >= pw_takeoff,
        ws <= ws_landing_limit,
    ])
    opti.minimize(installed_power_W)

    sol = opti.solve(verbose=False)

    wing_area_solution = float(sol(wing_area_m2))
    installed_power_solution = float(sol(installed_power_W))
    ws_solution = float(sol(ws))
    pw_solution = float(sol(pw))
    pw_cruise_solution = float(sol(pw_cruise))
    pw_takeoff_solution = float(sol(pw_takeoff))

    cl_cruise = inputs.beta_cruise * ws_solution / float(q_cruise)
    cd_cruise = inputs.cd0_clean + float(k) * cl_cruise**2

    return {
        "mtow_lbf": inputs.mtow_lbf,
        "wing_area_m2": wing_area_solution,
        "wing_area_ft2": wing_area_solution / FT2_TO_M2,
        "span_m": float(np.sqrt(inputs.aspect_ratio * wing_area_solution)),
        "span_ft": float(np.sqrt(inputs.aspect_ratio * wing_area_solution) / FT_TO_M),
        "wing_loading_N_m2": ws_solution,
        "wing_loading_psf": ws_solution / PSF_TO_PA,
        "installed_power_W": installed_power_solution,
        "installed_power_shp": installed_power_solution / HP_TO_W,
        "power_loading_W_N": pw_solution,
        "power_loading_shp_lbf": pw_solution * LBF_TO_N / HP_TO_W,
        "landing_wing_loading_limit_psf": float(ws_landing_limit / PSF_TO_PA),
        "cruise_power_required_shp_lbf": pw_cruise_solution * LBF_TO_N / HP_TO_W,
        "takeoff_power_required_shp_lbf": pw_takeoff_solution * LBF_TO_N / HP_TO_W,
        "cl_cruise": cl_cruise,
        "cd_cruise": cd_cruise,
        "ld_cruise": cl_cruise / cd_cruise,
    }


def sweep_one_factor(
    baseline: SizingInputs,
    field_name: str,
    values: Iterable[float],
) -> list[dict[str, float]]:
    """Resolve one optimization per value of one SizingInputs field."""
    rows = []
    for value in values:
        case = replace(baseline, **{field_name: float(value)})
        result = solve_sizing(case)
        result[field_name] = float(value)
        rows.append(result)
    return rows


def plot_sweep(rows: list[dict[str, float]], x_key: str, x_label: str) -> None:
    """Plot the three most useful constraint-sizing sweep outputs."""
    x = [row[x_key] for row in rows]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.3), constrained_layout=True)

    axes[0].plot(x, [row["installed_power_shp"] for row in rows], "o-")
    axes[0].set_ylabel("Installed shaft power [shp]")

    axes[1].plot(x, [row["wing_loading_psf"] for row in rows], "o-")
    axes[1].set_ylabel(r"Selected $W_{TO}/S$ [lbf/ft$^2$]")

    axes[2].plot(x, [row["span_ft"] for row in rows], "o-")
    axes[2].set_ylabel("Wing span [ft]")

    for ax in axes:
        ax.set_xlabel(x_label)
        ax.grid(True, alpha=0.3)

    plt.show()


def adjoint_installed_power_sensitivities(
    inputs: SizingInputs,
) -> dict[str, float]:
    """Return local log sensitivities of optimal installed shaft power.

    Each returned value is d(ln(P_installed*)) / d(ln(parameter)). The
    derivative includes the re-optimization of wing area, so this is more
    informative than differentiating a single constraint curve at fixed W/S.

    Parameters associated only with inactive constraints will have near-zero
    sensitivities. Results are local: a sensitivity can change sharply when
    the governing constraint changes.
    """
    opti = asb.Opti()

    # Expose the assumptions whose uncertainty is useful to rank. They are
    # Opti parameters, rather than Python floats, so the Lagrangian can be
    # differentiated with respect to them after solution.
    p = {
        "MTOW": opti.parameter(inputs.mtow_lbf),
        "Cruise Mach": opti.parameter(inputs.cruise_mach),
        "Clean CD0": opti.parameter(inputs.cd0_clean),
        "Aspect ratio": opti.parameter(inputs.aspect_ratio),
        "Oswald efficiency": opti.parameter(inputs.oswald_efficiency),
        "Cruise prop efficiency": opti.parameter(inputs.eta_prop_cruise),
        "Cruise power lapse": opti.parameter(inputs.alpha_power_cruise),
        "TOFL requirement": opti.parameter(inputs.tofl_required_ft),
        "Takeoff density ratio": opti.parameter(inputs.sigma_takeoff),
        "Takeoff CLmax": opti.parameter(inputs.clmax_takeoff),
        "TO thrust-to-power factor": opti.parameter(inputs.eta_eff_takeoff),
        "TO power lapse": opti.parameter(inputs.alpha_power_takeoff),
        "Landing distance": opti.parameter(inputs.landing_distance_unfactored_ft),
        "Landing CLmax": opti.parameter(inputs.clmax_landing),
        "Takeoff weight fraction": opti.parameter(inputs.f_takeoff),
        "Climb weight fraction": opti.parameter(inputs.f_climb),
        "Cruise weight fraction": opti.parameter(inputs.f_cruise),
        "Landing weight fraction": opti.parameter(inputs.f_landing),
    }

    mtow_N = p["MTOW"] * LBF_TO_N
    beta_cruise = p["Takeoff weight fraction"] * p["Climb weight fraction"]
    beta_landing = (
        p["Takeoff weight fraction"]
        * p["Climb weight fraction"]
        * p["Cruise weight fraction"]
        * p["Landing weight fraction"]
    )
    k = 1.0 / (np.pi * p["Oswald efficiency"] * p["Aspect ratio"])

    atmo_cruise = asb.Atmosphere(altitude=inputs.cruise_altitude_ft * FT_TO_M)
    rho_cruise = atmo_cruise.density()
    v_cruise = p["Cruise Mach"] * atmo_cruise.speed_of_sound()
    q_cruise = 0.5 * rho_cruise * v_cruise**2
    rho_sl = asb.Atmosphere(altitude=0.0).density()

    wing_area_m2 = opti.variable(
        init_guess=110.0,
        lower_bound=inputs.wing_area_bounds_m2[0],
        upper_bound=inputs.wing_area_bounds_m2[1],
        scale=100.0,
        category="Geometry",
    )
    installed_power_W = opti.variable(
        init_guess=4.0e6,
        lower_bound=inputs.installed_power_bounds_MW[0] * 1e6,
        upper_bound=inputs.installed_power_bounds_MW[1] * 1e6,
        scale=1.0e6,
        category="Propulsion",
    )

    ws = mtow_N / wing_area_m2
    pw = installed_power_W / mtow_N

    pw_cruise = (
        v_cruise
        / (p["Cruise prop efficiency"] * p["Cruise power lapse"])
        * (
            q_cruise * p["Clean CD0"] / ws
            + k * beta_cruise**2 * ws / q_cruise
        )
    )

    # Roskam Part 25 screening relation, then the same declared conversion
    # from equivalent takeoff thrust to installed shaft power as solve_sizing.
    tw_takeoff = (
        37.5 * (ws / PSF_TO_PA)
        / (
            p["Takeoff density ratio"]
            * p["Takeoff CLmax"]
            * p["TOFL requirement"]
        )
    )
    v_stall_takeoff = np.sqrt(2.0 * ws / (rho_sl * p["Takeoff CLmax"]))
    pw_takeoff = (
        tw_takeoff
        * inputs.v_ref_factor_takeoff
        * v_stall_takeoff
        / (p["TO thrust-to-power factor"] * p["TO power lapse"])
    )

    v_app_mps = np.sqrt(p["Landing distance"] / 0.30) * KT_TO_MPS
    v_stall_landing = v_app_mps / 1.30
    ws_landing_limit = (
        0.5 * rho_sl * v_stall_landing**2 * p["Landing CLmax"] / beta_landing
    )

    opti.subject_to([
        pw >= pw_cruise,
        pw >= pw_takeoff,
        ws <= ws_landing_limit,
    ])
    opti.minimize(installed_power_W)
    sol = opti.solve(verbose=False)

    # This is the envelope-theorem / adjoint derivative of the *optimized*
    # objective, including active constraints and their Lagrange multipliers.
    lagrangian = opti.f + cas.dot(opti.lam_g, opti.g)
    return {
        name: float(sol(cas.gradient(lagrangian, parameter) * parameter / opti.f))
        for name, parameter in p.items()
    }


def plot_adjoint_sensitivities(
    sensitivities: dict[str, float],
    objective_label: str = r"Parameter Sensitivity $\frac{\text{d}\ln(P^*)}{\text{d}\ln(p)}$  [-]",
) -> None:
    """Draw a signed local-sensitivity (tornado) chart."""
    names, values = zip(*sorted(sensitivities.items(), key=lambda item: abs(item[1])))
    colors = ["tab:red" if value > 0 else "tab:blue" for value in values]
    x_limit = 1.15 * max(abs(value) for value in values)
    fig, ax = plt.subplots(
        figsize=(7, 5.2),
        dpi=300,
        constrained_layout=True,
    )
    ax.barh(names, values, color=colors, height=0.65)
    for i, value in enumerate(values):
        offset = 0.03 * x_limit
        ax.text(
            value + (offset if value > 0 else -offset),
            i,
            f"{value:+.2f}",
            va="center",
            ha="left" if value > 0 else "right",
            fontsize=8,
        )

    ax.axvline(0, color="0.35", lw=0.8)
    ax.set_xlim(-x_limit, x_limit+1)
    ax.set_xlabel(objective_label)
    ax.grid(True, axis="x", alpha=0.25)
    plt.savefig("Sensitivities", dpi=300)
    plt.show()


if __name__ == "__main__":
    baseline = SizingInputs()
    design = solve_sizing(baseline)

    print("Baseline AeroSandbox constraint-sizing result")
    for name in [
        "wing_area_ft2",
        "span_ft",
        "wing_loading_psf",
        "installed_power_shp",
        "power_loading_shp_lbf",
        "ld_cruise",
    ]:
        print(f"{name:35s}: {design[name]:.3f}")

    # Start with the sensitivities most likely to move your current design.
    cd0_cases = sweep_one_factor(
        baseline,
        field_name="cd0_clean",
        values=np.linspace(0.018, 0.024, 7),
    )
    plot_sweep(cd0_cases, "cd0_clean", r"Clean $C_{D0}$")

    ar_cases = sweep_one_factor(
        baseline,
        field_name="aspect_ratio",
        values=np.linspace(7.0, 11.0, 9),
    )
    plot_sweep(ar_cases, "aspect_ratio", "Aspect ratio")

    sensitivities = adjoint_installed_power_sensitivities(baseline)
    print("\nLocal log sensitivities of minimum installed power")
    for name, sensitivity in sorted(
        sensitivities.items(), key=lambda item: -abs(item[1])
    ):
        print(f"{name:28s} {sensitivity:+7.3f}")
    plot_adjoint_sensitivities(sensitivities)
