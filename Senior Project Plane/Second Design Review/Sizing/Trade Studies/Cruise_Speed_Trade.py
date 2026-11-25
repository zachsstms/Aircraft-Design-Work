from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from ambiance import Atmosphere

@dataclass
class Inputs:
    cruiseWeight: float = 48000 # lbs
    cruiseAltitude: float = 20000 # ft
    mach: float = 0.5 # Design cruise Mach number (drawn as a line on the plots)
    wingArea: float = 754.0 # ft^2
    aspectRatio: float = 12.0 # Wing aspect ratio
    CD0: float = 0.025 # Zero-lift drag coefficient (replace with your component buildup)
    oswaldEfficiency: float = 0.8 # Oswald efficiency factor
    CLmax: float = 2.0 # Maximum lift coefficient
    stallMargin: float = 1.2 # Stall margin factor

    n_engine: int = 2 # Number of engines
    hp: float = 4600 # shp AE 2100A
    lapseRate: float = 0.3 # Engine lapse rate: power available = hp*(rho/rho0)^(1 - lapseRate)
    cruiseRating: float = 0.85 # Engine cruise rating
    BSFc: float = 0.45 # Brake specific fuel consumption (lb/(hp*hr))
    eta_p_cruise: float = 0.85 # Propeller efficiency at cruise

    fuel_price: float = 8.0 # $/gal
    seats: int = 65 # Number of seats

    maxMach: float = 0.7 # Maximum Mach number
    nPoints: int = 100 # Number of points for analysis

inputs = Inputs()

# Unit conversions
ft2m = 0.3048
m2ft = 3.28084
kgm3_to_slugft3 = 0.00194032
kt2fps = 1.6878
lbPerGal = 6.7 # Jet-A
rhoSL = 0.002377 # slug/ft^3

# Atmosphere at cruise altitude
atm = Atmosphere(inputs.cruiseAltitude * ft2m)
rho = float(atm.density[0]) * kgm3_to_slugft3 # slug/ft^3
a = float(atm.speed_of_sound[0]) * m2ft # ft/s

# Mach sweep: from stall margin speed up to maxMach
vStall = np.sqrt(2 * inputs.cruiseWeight / (rho * inputs.wingArea * inputs.CLmax)) # ft/s
machMin = inputs.stallMargin * vStall / a
mach = np.linspace(machMin, inputs.maxMach, inputs.nPoints)

# Speed and dynamic pressure
V = mach * a # ft/s
Vkt = V / kt2fps # knots
q = 0.5 * rho * V**2 # psf

# Lift and drag
CL = inputs.cruiseWeight / (q * inputs.wingArea)
k = 1 / (np.pi * inputs.oswaldEfficiency * inputs.aspectRatio)
CD = inputs.CD0 + k * CL**2
drag = q * inputs.wingArea * CD # lbs

# Power required and available
powerRequired = drag * V / (550 * inputs.eta_p_cruise) # shp
powerAvailable = inputs.n_engine * inputs.hp * (rho / rhoSL)**(1 - inputs.lapseRate) * inputs.cruiseRating # shp
feasible = powerRequired <= powerAvailable

# Fuel flow, specific range, fuel cost
fuelFlow = inputs.BSFc * powerRequired # lb/hr
specificRange = Vkt / fuelFlow # nm/lb
fuelCostPerHr = fuelFlow * inputs.fuel_price / lbPerGal # $/hr
fuelCostPerSeatNm = fuelCostPerHr / Vkt / inputs.seats # $/seat-nm

# Plots
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
fig.suptitle(f"Cruise speed trade study at {inputs.cruiseAltitude:,.0f} ft")

plots = [
    (specificRange, "Specific range (nm/lb)"),
    (fuelFlow, "Fuel flow (lb/hr)"),
    (fuelCostPerSeatNm, "Fuel cost per seat-nm ($)"),
]

for ax, (y, label) in zip(axes, plots):
    ax.plot(mach[feasible], y[feasible], lw=2)
    ax.plot(mach[~feasible], y[~feasible], "--", color="gray", lw=1, label="power-limited")
    ax.axvline(inputs.mach, color="red", ls=":", label="design Mach")
    ax.set_xlabel("Mach number")
    ax.set_ylabel(label)
    ax.grid(alpha=0.3)

axes[0].legend(fontsize=8)
plt.show()