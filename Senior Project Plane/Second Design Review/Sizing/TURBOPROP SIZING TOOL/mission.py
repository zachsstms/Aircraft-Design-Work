# Mission Breakdown (can add fidelity as needed)
'''
mission.py
READ ME YO
All units in: nmi, knots, lb/(hp hr)
'''
import numpy as np

def MTOW_convergence(MTOW_guess, 
                     EWF_initial, 
                     L_D_cruise, 
                     Range,
                     BSFC,
                     eta_p_cruise,
                     Payload_weight):
    # nested mission breakdown function
    # For now, using Roskam:
    # This function calculates how much weight is lost during each stage of the mission     
    def mission_breakdown(Range, BSFC,eta_p_cruise,L_D_cruise):
        takeoff_weight_fraction=0.97 # value from Roskam
        climb_weight_fraction=0.985
        cruise_weight_fraction=np.exp(-Range*BSFC/(L_D_cruise*eta_p_cruise*325.9)) #breguet range, 325.9 to get nmi
        landing_weight_fraction=0.995
        #calculate fuel weight fraction:
        fuel_weight_fraction=(1-takeoff_weight_fraction*
                            climb_weight_fraction*cruise_weight_fraction*
                            landing_weight_fraction)
        
        return fuel_weight_fraction, cruise_weight_fraction
    
    [fuel_weight_fraction, cruise_weight_fraction] = mission_breakdown(Range, BSFC, eta_p_cruise, L_D_cruise) #call breakdown function, giving W_f/MTOW
    # This is running the MTOW guess convergence, as shown in "Mission Breakdown" in Excel
    # The result is the converged weights
    W_empty=MTOW_guess*EWF_initial
    W_fuel=MTOW_guess*fuel_weight_fraction
    MTOW_new=W_empty+W_fuel+Payload_weight
    difference=np.abs(MTOW_new-MTOW_guess)/MTOW_guess
    #run the sizing convergence loop
    iterations=0
    while difference>0.001 and iterations<100:
        MTOW_guess=MTOW_new
        W_empty=MTOW_guess*(0.96*MTOW_guess**(-0.05)) # empirical relationship from Raymer MTOW*EWF=W_E
        W_fuel=MTOW_guess*fuel_weight_fraction
        MTOW_new=W_empty+W_fuel+Payload_weight
        cruise_weight=cruise_weight_fraction*MTOW_new # needed for `aerodynamics.py`
        difference=np.abs(MTOW_new-MTOW_guess)/MTOW_guess
        iterations+=1 # basically this is a cap to make sure the thing doesn't get stuck
    return MTOW_new, W_empty, W_fuel, cruise_weight


