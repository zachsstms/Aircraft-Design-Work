# Mission Breakdown (can add fidelity as needed)
'''
READ ME YO
All units in: nmi, knots, lb/(hp hr)
'''
import numpy as np

def MTOW_convergence(MTOW_guess, EWF_initial, L_D_cruise, fuel_weight_fraction, Payload_weight):
    # nested mission breakdown function
    # For now, using Roskam:
    # This function calculates how much weight is lost during each stage of the mission     
    def mission_breakdown(Range, BSFC,eta_p_cruise,L_D_cruise):
        takeoff_weight_fraction=0.97 # value from Roskam
        climb_weight_fraction=0.985
        cruise_weight_fraction=np.exp(-Range*BSFC/(L_D_cruise*eta_p_cruise*375)) #breguet range, 375 to keep units
        landing_weight_fraction=0.995
        #calculate fuel weight fraction:
        fuel_weight_fraction=(1-takeoff_weight_fraction*
                            climb_weight_fraction*cruise_weight_fraction*
                            landing_weight_fraction)
        return fuel_weight_fraction
    # This is running the MTOW guess convergence, as shown in "Mission Breakdown" in Excel
    # The result is the converged weights
    W_empty=MTOW_guess*EWF_initial
    W_fuel=MTOW_guess*fuel_weight_fraction
    MTOW_new=W_empty+W_fuel+Payload_weight
    difference=np.abs(MTOW_new-MTOW_guess)/MTOW_guess
    #run the sizing convergence loop
    while difference>0.001:
        MTOW_guess=MTOW_new
        W_empty=MTOW_guess*EWF_initial
        W_fuel=MTOW_guess*fuel_weight_fraction
        MTOW_new=W_empty+W_fuel+Payload_weight
        difference=np.abs(MTOW_new-MTOW_guess)/MTOW_guess
    return MTOW_new, W_empty, W_fuel


