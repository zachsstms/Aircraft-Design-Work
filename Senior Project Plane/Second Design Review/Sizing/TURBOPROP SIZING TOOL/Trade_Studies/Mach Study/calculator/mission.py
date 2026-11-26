# Mission Breakdown (can add fidelity as needed)
'''
mission.py
READ ME YO
All units in: nmi, knots, lb/(hp hr)
'''
import numpy as np

# Mission segment assumptions shared with the constraint diagram.
takeoff_weight_fraction = 0.97 # values from roskam
climb_weight_fraction = 0.985
landing_weight_fraction = 0.995

def MTOW_convergence(MTOW_guess, 
                     L_D_cruise, 
                     Range,
                     BSFC,
                     eta_p_cruise,
                     Payload_weight):
    # nested mission breakdown function
    # For now, using Roskam:
    # This function calculates how much weight is lost during each stage of the mission     
    def mission_breakdown(Range, BSFC,eta_p_cruise,L_D_cruise):
        cruise_weight_fraction=np.exp(-Range*BSFC/(L_D_cruise*eta_p_cruise*325.9)) #breguet range, 325.9 to get nmi
        #calculate fuel weight fraction:
        fuel_weight_fraction=(1-takeoff_weight_fraction*
                            climb_weight_fraction*cruise_weight_fraction*
                            landing_weight_fraction)
        
        return fuel_weight_fraction, cruise_weight_fraction
    
    [fuel_weight_fraction, cruise_weight_fraction] = mission_breakdown(Range, BSFC, eta_p_cruise, L_D_cruise) #call breakdown function, giving W_f/MTOW
    if cruise_weight_fraction < 1e-8:
        raise ValueError("The mission fuel fraction is too large; check range, BSFC, efficiency, and L/D.")
    # This is running the MTOW guess convergence, as shown in "Mission Breakdown" in Excel
    # The result is the converged weights


    for iterations in range(500):
        W_empty = MTOW_guess*(0.96*MTOW_guess**(-0.05)) # empirical relationship from Raymer MTOW*EWF=W_E
        W_fuel = MTOW_guess*fuel_weight_fraction
        MTOW_new=W_empty+W_fuel+Payload_weight
        difference=np.abs(MTOW_new-MTOW_guess)/MTOW_guess
        if not np.isfinite(MTOW_new) or MTOW_new > 1e10:
            raise RuntimeError("Mission weights diverged; check the mission inputs.")
        if difference < 1e-9: # this is the weight loop tolerance
            break
        MTOW_guess = MTOW_new
    else:
        raise RuntimeError("MTOW did not converge within 500 mission iterations.")

    W_empty = MTOW_new * (0.96 * MTOW_new**(-0.05)) # empirical equation from Raymer
    W_fuel = MTOW_new * fuel_weight_fraction
    # Start and end of cruise include the preceding takeoff and climb burns.
    start_cruise_weight = takeoff_weight_fraction * climb_weight_fraction * MTOW_new # weight at the start of cruise
    exponent = -np.log(cruise_weight_fraction)
    mean_fraction = -np.expm1(-exponent) / exponent if exponent > 0 else 1.0  # effectively weight_cruise_start/weight_cruise_end
    cruise_weight = start_cruise_weight  * mean_fraction # weight bascially in the middle of cruise
    return MTOW_new, W_empty, W_fuel, cruise_weight, cruise_weight_fraction


