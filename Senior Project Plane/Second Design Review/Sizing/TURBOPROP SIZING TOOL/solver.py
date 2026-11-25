"""
This file is the looping workhorse. It takes in the inputs (requirements)
and runs each function. 
"""
# loading each function
import numpy as np
from aerodynamics import CDminFunct
from constraints import constraint_analysis
from geometry import planeGeometry
from mission import MTOW_convergence
import inputs

# this is the convergence difference function
def _relative_change(new, old):
    return abs(new - old) / max(abs(old), 1e-12)

# solver function, this pulls and runs each subsidiary function. 
def solve(cfg=inputs):
    # Initial guesses and independent relative tolerances
    mtow = cfg.initial_MTOW
    wing_area = cfg.initial_wing_area
    tol_ld = cfg.tol_LD
    tol_mtow = cfg.tol_MTOW
    tol_area = cfg.tol_S
    max_iterations = cfg.max_iterations
    previous = None

    # THIS IS THE SIZING LOOP
    for iteration in range(1, max_iterations + 1):
        cfg.Wing.Area = wing_area

        fuselage, wing, horizontal_tail, vertical_tail = planeGeometry(cfg.Wing)

        cd0, _, ld_cruise, wing, fuselage, horizontal_tail, vertical_tail = (
            CDminFunct(
                cfg.mach,
                cfg.altitude_m,
                cfg.cruiseWeight,
                fuselage,
                wing,
                horizontal_tail,
                vertical_tail,
            )
        )

        mtow_new, empty_weight, fuel_weight = MTOW_convergence(
            mtow,
            cfg.EWF_initial,
            ld_cruise,
            cfg.Range,
            cfg.BSFC,
            cfg.eta_p_cruise,
            cfg.Payload_weight,
        )

        # Keep the mission's cruise weight fraction consistent with its
        # Breguet-range calculation.
        cruise_weight_fraction = np.exp(
            -cfg.Range * cfg.BSFC
            / (ld_cruise * cfg.eta_p_cruise * 325.9)
        )
        takeoff_weight_fraction = 0.97
        climb_weight_fraction = 0.985
        landing_weight_fraction = 0.995
        k = 1 / (np.pi * wing.AspectRatio * wing.oswaldEfficiency)

        constraints = constraint_analysis(
            mtow_new,
            cd0,
            wing.AspectRatio,
            wing.oswaldEfficiency,
            cfg.mach,
            cfg.cruise_altitude,  # Pint quantity, convertible to meters
            cfg.landing_distance,
            cfg.landing_altitude,
            cfg.takeoff_distance,
            cfg.takeoff_altitude,
            cfg.sigma_TO,
            cfg.CL_max_TO,
            cfg.CL_max_L,
            cfg.eta_p_cruise,
            k,
            cruise_weight_fraction,
            takeoff_weight_fraction,
            climb_weight_fraction,
            landing_weight_fraction,
            cfg.alpha_P_cruise,
            plot=False,
        )

        wing_area_new = constraints["S_design"]
        current = (ld_cruise, mtow_new, wing_area_new)

        if previous is not None:
            errors = (
                _relative_change(current[0], previous[0]),
                _relative_change(current[1], previous[1]),
                _relative_change(current[2], previous[2]),
            )

            if (
                errors[0] <= tol_ld
                and errors[1] <= tol_mtow
                and errors[2] <= tol_area
            ):
                return {
                    "converged": True,
                    "iterations": iteration,
                    "L_D": ld_cruise,
                    "MTOW": mtow_new,
                    "S": wing_area_new,
                    "relative_changes": {
                        "L_D": errors[0],
                        "MTOW": errors[1],
                        "S": errors[2],
                    },
                    "empty_weight": empty_weight,
                    "fuel_weight": fuel_weight,
                    "constraints": constraints,
                }

        previous = current
        mtow = mtow_new
        wing_area = wing_area_new

    raise RuntimeError(
        f"Sizing did not converge within {max_iterations} iterations."
    )


