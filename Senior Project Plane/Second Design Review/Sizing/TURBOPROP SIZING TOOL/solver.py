"""
This file is the looping workhorse. It takes in the inputs (requirements)
and runs each function.
"""

from copy import deepcopy
import numpy as np
from aerodynamics import CDminFunct
from constraints import constraint_analysis
from geometry import planeGeometry
from mission import (MTOW_convergence, takeoff_weight_fraction,
                     climb_weight_fraction, landing_weight_fraction)
import inputs

# this is the overall change between iterations
def _relative_change(new, old):
    return abs(new - old) / max(abs(old), 1e-12)
# This is the main looping workhorse 
def solve(cfg=inputs, plot=False): 
    inputs.validate_inputs(cfg) # pulls from the inputs.py file which ran logic to make sure the inputs are sensible

    # STARTING "GUESSES" USED BY THE SOLVER
    mtow = 3.0 * cfg.Payload_weight # example guess, pretty robust
    ld_cruise = 15.0 # L/D starting guess
    cd0 = 0.025 # C_D0 initial guess
    tolerance = 1e-5 # the tolerance  for every parameter
    max_iterations = 200 # such that it doesn't spiral
    relaxation = 0.5 # relaxation is a parameter that handles oscillations to force convergence
    previous_area = None # area gets calculated 

    # THIS IS THE SIZING LOOP: mission -> constraints -> geometry -> drag.
    for iteration in range(1, max_iterations + 1):
        # 1. Mission: estimate weights using the previous cruise L/D.
        mtow_new, empty_weight, fuel_weight, cruise_weight, cruise_fraction = MTOW_convergence(
            mtow, ld_cruise, cfg.Range, cfg.BSFC, cfg.eta_p_cruise, cfg.Payload_weight
        )

        # Constraints: calculate wing area and installed power.
        k = 1 / (np.pi * cfg.Wing.AspectRatio * cfg.Wing.OswaldEfficiency)
        constraint_inputs = (
            mtow_new, cd0, cfg.Wing.AspectRatio, cfg.Wing.OswaldEfficiency,
            cfg.mach, cfg.cruise_altitude, cfg.landing_distance, cfg.landing_altitude,
            cfg.takeoff_distance, cfg.takeoff_altitude, cfg.CL_max_TO, cfg.CL_max_L,
            cfg.eta_p_cruise, k, cruise_fraction, takeoff_weight_fraction * climb_weight_fraction, # the multiplication is for the weight at the start of cruise (heaviest)
            takeoff_weight_fraction, climb_weight_fraction, landing_weight_fraction,
            cfg.alpha_P_cruise
        )
        constraints = constraint_analysis(*constraint_inputs, plot=False)
        wing_area = constraints["S_design"]

        #Geometry: use copies so the inputs stay unchanged for trade studies.
        fuselage = deepcopy(cfg.Fuselage)
        wing = deepcopy(cfg.Wing)
        horizontal_tail = deepcopy(cfg.HorizontalTail)
        vertical_tail = deepcopy(cfg.VerticalTail)
        wing.Area = wing_area
        fuselage, wing, horizontal_tail, vertical_tail = planeGeometry(
            fuselage, wing, horizontal_tail, vertical_tail
        )

        # Aerodynamics: calculate new CD0 and cruise L/D from that geometry.
        aero_inputs = (cfg.mach, cfg.cruise_altitude, cruise_weight,
                       fuselage, wing, horizontal_tail, vertical_tail)
        cd0_new, _, ld_new, wing, fuselage, horizontal_tail, vertical_tail = CDminFunct(*aero_inputs)

        errors = {
            "L_D": _relative_change(ld_new, ld_cruise),
            "CD0": _relative_change(cd0_new, cd0),
            "MTOW": _relative_change(mtow_new, mtow),
            "S": _relative_change(wing_area, previous_area) if previous_area is not None else float("inf"),
        }
        if max(errors.values()) <= tolerance:
            if plot:
                constraint_analysis(*constraint_inputs, plot=True)
                CDminFunct(*aero_inputs, plot=True)
            return {
                "converged": True, "iterations": iteration,
                "L_D": ld_new, "CD0": cd0_new, "MTOW": mtow_new, "S": wing_area,
                "relative_changes": errors, "empty_weight": empty_weight,
                "fuel_weight": fuel_weight, "cruise_weight": cruise_weight,
                "constraints": constraints,
                "geometry": (fuselage, wing, horizontal_tail, vertical_tail),
            }

        # Under-relax the feedback to reduce oscillation (this is the iteration step)
        ld_cruise += relaxation * (ld_new - ld_cruise)
        cd0 += relaxation * (cd0_new - cd0)
        mtow = mtow_new
        previous_area = wing_area

    raise RuntimeError(f"Sizing did not converge within {max_iterations} iterations: {errors}")
