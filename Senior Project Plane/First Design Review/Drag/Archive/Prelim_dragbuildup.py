import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

### ALL VALUES ARE IN FREEDOM UNITS ###

## CD PI method for CDmin

Cdpi_wing = 0.0075 #0.005 to 0.009
Cdpi_HT = 0.007 #0.006 to 0.008
Cdpi_VT = 0.007 #0.006 to 0.008
Cdpi_fuselage = 0.085 #0.07 to 0.10
Cdpi_prop = 0.07 #0.05 to 0.09

WetA_wing = 471
WetA_HT = 100
WetA_VT = 240
WetA_fuselage = np.pi * 4**2
WetA_prop = np.pi * 6.5**2

Cd_min = (Cdpi_fuselage * WetA_fuselage + Cdpi_HT * WetA_HT + Cdpi_VT * WetA_VT + Cdpi_wing * WetA_wing + Cdpi_prop * WetA_prop) / WetA_wing

print("Cd_min = ", Cd_min)

AR = 11
e1 = 0.5
e = 0.7
e2 = 0.99
Cl = np.linspace(-2, 2, 100)

k1 = 1 / (np.pi * AR * e1)
k = 1 / (np.pi * AR * e)
k2 = 1 / (np.pi * AR * e2)

Cd1 = Cd_min + k1 * Cl**2
Cd = Cd_min + k * Cl**2
Cd2 = Cd_min + k2 * Cl**2


plt.figure()
plt.plot(Cd, Cl)
plt.plot(Cd1, Cl, '--')
plt.plot(Cd2, Cl, '--')
plt.title("Drag Polar")
plt.xlabel(r"Coefficient of Drag ($C_D$)")
plt.ylabel(r"Coefficient of Lift ($C_L$)")
plt.legend(["e = 0.7", "e = 0.5", "e = 0.99"])
plt.grid()
plt.show()