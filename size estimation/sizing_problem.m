clc; clear all;

% Inputs
L_D = 10.3;          % Lift-to-drag ratio
V = 576.418603;           % Cruise speed [nm/hr]
R_jet = 1500;      % Required range [nm]
EWF = 0.58;        % Empty weight fraction, WE/WTO
TSFC = 0.52;       % Thrust specific fuel consumption [1/hr]
W_pl = 31775;      % Payload weight [lb]

% Fuel weight fraction from the Breguet range equation
Wf_Wto = 1 - exp((-R_jet * TSFC) / (L_D * V));

% Takeoff, empty, and fuel weights
W_TO = W_pl / (1 - EWF - Wf_Wto);
W_E = EWF * W_TO;
W_F = Wf_Wto * W_TO;

% Display results
fprintf('Takeoff Weight, W_TO = %.0f lb\n', W_TO)
fprintf('Empty Weight,   W_E  = %.0f lb\n', W_E)
fprintf('Fuel Weight,    W_F  = %.0f lb\n', W_F)
Takeoff Weight, W_TO = 95727 lb
Empty Weight,   W_E  = 53607 lb
Fuel Weight,    W_F  = 10960 lb
Takeoff Weight, W_TO = 105235 lb
Empty Weight,   W_E  = 61036 lb
Fuel Weight,    W_F  = 13039 lb
