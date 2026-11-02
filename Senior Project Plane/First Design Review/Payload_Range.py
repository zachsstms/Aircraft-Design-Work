# vibe coded payload range diagram using the values
# from the sizing excel spreadsheet

import numpy as np
import matplotlib.pyplot as plt
from ambiance import Atmosphere
import pint

ureg = pint.UnitRegistry()

# Aircraft weights [lb]
MTOW = 50696.72136
W_E = 28314.05772
W_pl_max = 16250
W_f = 6117.851136

# Mission / cruise assumptions
R_design = 825                 # design range [nmi]
M_cruise = 0.48
alt = 20000 * ureg.feet
L_D = 16
BSFC = 0.46                    # [lb/(hp·hr)]
eta = 0.90                     # propulsive efficiency
reserve_fraction = 0.06

# Cruise speed from ISA atmosphere
a_cruisealt = (
    Atmosphere(alt.to("meters").magnitude).speed_of_sound.item()
    * ureg("m/s").to("ft/s").magnitude
)
V_cruise = a_cruisealt * M_cruise       # [ft/s]
V_cruise_kts = V_cruise * 0.592484      # [knots]

# Fuel available for cruise after reserves
W_f_burn = W_f * (1 - reserve_fraction)

# Verify MTOW condition
W_TO_max_payload = W_E + W_pl_max + W_f
fuel_allowed_at_max_payload = MTOW - W_E - W_pl_max

print(f"Cruise speed: {V_cruise_kts:.1f} knots")
print(f"Takeoff weight at max payload/full fuel: {W_TO_max_payload:,.1f} lb")
print(f"MTOW margin: {MTOW - W_TO_max_payload:,.1f} lb")
print(f"Fuel allowed at max payload: {fuel_allowed_at_max_payload:,.1f} lb")

# Payload values from max payload to ferry condition
payload = np.linspace(W_pl_max, 0, 250)

# Initial and final cruise weights
W_initial = W_E + payload + W_f
W_final = W_initial - W_f_burn

# Propeller Breguet range equation:
# R [ft] = (550 * 3600 * eta / BSFC) * (L/D) * ln(Wi/Wf)
# Convert feet to nautical miles.
range_nm = (
    (550 * 3600 * eta / BSFC)
    * L_D
    * np.log(W_initial / W_final)
    / 6076.12
)

# Key points
R_max_payload = range_nm[0]
R_ferry = range_nm[-1]

# Include zero-range / maximum-payload starting point
plot_range = np.concatenate(([0], range_nm))
plot_payload = np.concatenate(([W_pl_max], payload))

plt.figure(figsize=(10, 6))
plt.plot(plot_range, plot_payload, color="blue", linewidth=2.5,
         label="Payload-range envelope")

# Design-range reference
plt.axvline(R_design, color="red", linestyle="--",
            label=f"Design range: {R_design} nmi")

# Key points
plt.scatter([R_max_payload, R_ferry],
            [W_pl_max, 0],
            color="crimson", zorder=3)

plt.annotate(
    f"Maximum payload range\n{R_max_payload:.0f} nmi",
    xy=(R_max_payload, W_pl_max),
    xytext=(12, -45),
    textcoords="offset points"
)

plt.annotate(
    f"Ferry range\n{R_ferry:.0f} nmi",
    xy=(R_ferry, 0),
    xytext=(-90, 18),
    textcoords="offset points"
)

plt.xlabel("Range [nmi]")
plt.ylabel("Payload [lb]")
plt.title("Payload-Range Diagram")
plt.xlim(left=0)
plt.ylim(bottom=0)
plt.grid(True, linestyle="--", alpha=0.55)
plt.legend()
plt.tight_layout()
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
save_path = os.path.join(script_dir, "Payload_range.png")
plt.show()
