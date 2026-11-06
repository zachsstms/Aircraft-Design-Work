import numpy as np
import matplotlib.pyplot as plt
import warnings
from types import SimpleNamespace
from ambiance import Atmosphere


# 1. Flight condition and reference aircraft
flight = SimpleNamespace(
    altitude_ft=20000,
    TAS_kts=294.871,
    weight_lbf=48000,  # Provisional; only used for cruise marker
)

aircraft = SimpleNamespace(
    Sref_ft2=1074,
    Swing_ft2=1074,
    span_ft=103.6,
    SHT_ft2=260.6,
    SVT_ft2=257,
    fuselageLength_ft=86,
    fuselageDmax_ft=9,
)

aircraft.AR = aircraft.span_ft**2 / aircraft.Sref_ft2

# 2. Geometry and component assumptions
wing = SimpleNamespace(
    tcRoot=0.15,
    tcTip=0.15,
    sweepC4_deg=0,
    exposedPlanformFraction=1.00,
    wetAreaMultiplier=1.07,
)

wing.tcMean = 0.5 * (wing.tcRoot + wing.tcTip)
wing.meanChord_ft = aircraft.Swing_ft2 / aircraft.span_ft  # Mean-chord proxy

tail = SimpleNamespace(
    tcHT=0.09,
    tcVT=0.09,
    sweepC4_HT_deg=0,
    sweepC4_VT_deg=0,
    exposedFractionHT=1.00,
    exposedFractionVT=1.00,
    wetAreaMultiplierHT=1.05,
    wetAreaMultiplierVT=1.05,
    meanChordHT_ft=8.04,
    meanChordVT_ft=12.6,
)

# Interference factors: provisional low-wing / T-tail assumptions
IF = SimpleNamespace(
    wing=1.20,
    fuselage=1.00,
    HT=1.04,
    VT=1.04,
)

fuselage = SimpleNamespace(
    stationX_ft=np.array([], dtype=float),
    stationD_ft=np.array([], dtype=float),
    IF=IF.fuselage,
)

# 3. Skin-friction model selection
skin = SimpleNamespace(
    method="fullyTurbulent",  # "fullyTurbulent" or "mixed"
    XtrOverC=np.array([np.nan, np.nan, np.nan, np.nan]),
    roughnessDescription="smooth paint (assumed)",
    k_ft=2.08e-5,
)

formFactor = SimpleNamespace(
    liftingSurfaceMethod="Eq15-62",  # "Eq15-62" or "Eq15-63"
)

# 4. Standard-atmosphere state and Reynolds numbers
# ambiance requires altitude in meters and returns SI properties.
# Convert those properties immediately to consistent imperial units.
FT_TO_M = 0.3048
LBF_TO_N = 4.4482216152605
SLUG_TO_KG = LBF_TO_N / FT_TO_M
PA_TO_PSF = FT_TO_M**2 / LBF_TO_N

try:
    atmosphere = Atmosphere(flight.altitude_ft * FT_TO_M)
except ValueError as exc:
    raise ValueError(
        f"Altitude {flight.altitude_ft:g} ft is outside ambiance's supported range."
    ) from exc

T_R = atmosphere.temperature.item() * 1.8                   # degrees Rankine
p_psf = atmosphere.pressure.item() * PA_TO_PSF              # lbf/ft^2
rho = atmosphere.density.item() * FT_TO_M**3 / SLUG_TO_KG    # slug/ft^3
mu = atmosphere.dynamic_viscosity.item() * PA_TO_PSF        # lbf*s/ft^2
a = atmosphere.speed_of_sound.item() / FT_TO_M              # ft/s

V = flight.TAS_kts * 0.514444 / FT_TO_M  # ft/s; preserves original kt conversion
Mach = V / a
q = 0.5 * rho * V**2  # lbf/ft^2

component = [
    "Wing",
    "Fuselage",
    "Horizontal tail",
    "Vertical tail",
]

Lref_ft = np.array([
    wing.meanChord_ft,
    aircraft.fuselageLength_ft,
    tail.meanChordHT_ft,
    tail.meanChordVT_ft,
])

ReActual = rho * V * Lref_ft / mu

# Roughness-based cutoff Reynolds number
ReCutoff = 38.21 * (Lref_ft / skin.k_ft)**1.053
ReUsed = np.minimum(ReActual, ReCutoff)

# 5. Estimate wetted areas (all in ft^2)
SwetWing = (
    2 * wing.wetAreaMultiplier
    * aircraft.Swing_ft2
    * wing.exposedPlanformFraction
)

SwetHT = (
    2 * tail.wetAreaMultiplierHT
    * aircraft.SHT_ft2
    * tail.exposedFractionHT
)

SwetVT = (
    2 * tail.wetAreaMultiplierVT
    * aircraft.SVT_ft2
    * tail.exposedFractionVT
)

# Station-based conical-frustum sum if station data are provided
x = np.asarray(fuselage.stationX_ft, dtype=float).ravel()
diameters = np.asarray(fuselage.stationD_ft, dtype=float).ravel()

if x.size >= 2 and x.size == diameters.size:
    r = diameters / 2

    if np.any(np.diff(x) <= 0) or np.any(r < 0):
        raise ValueError(
            "Fuselage stations must increase in x "
            "and diameters must be nonnegative."
        )

    dx = np.diff(x)
    dr = np.diff(r)

    SwetFuselage = np.sum(
        np.pi * (r[:-1] + r[1:]) * np.sqrt(dx**2 + dr**2)
    )

    fuselageAreaMethod = "station-based frustum estimate"

else:
    SwetFuselage = (
        np.pi * aircraft.fuselageDmax_ft * aircraft.fuselageLength_ft
    )

    fuselageAreaMethod = "constant-diameter capsule/cylinder proxy"

Swet = np.array([SwetWing, SwetFuselage, SwetHT, SwetVT])
IFvec = np.array([IF.wing, IF.fuselage, IF.HT, IF.VT])

# 6. Component skin-friction coefficients
Cf_turbulent = 0.455 / (
    np.log10(ReUsed)**2.58
    * (1 + 0.144 * Mach**2)**0.65
)

if skin.method.lower() == "fullyturbulent":
    Cf = Cf_turbulent

elif skin.method.lower() == "mixed":
    xtr = np.asarray(skin.XtrOverC, dtype=float)

    if (
        xtr.shape != (4,)
        or np.any(~np.isfinite(xtr))
        or np.any(xtr < 0)
        or np.any(xtr > 1)
    ):
        raise ValueError(
            "For mixed flow, set skin.XtrOverC to four values from 0 to 1."
        )

    if Mach > 0.5:
        raise ValueError(
            "For mixed flow above Mach 0.5, apply the book's "
            "Frankl-Voishel correction before using this model."
        )

    x0 = 36.9 * xtr**0.625 * (1 / ReUsed)**0.375
    Cf = 0.074 / ReUsed**0.2 * (1 - (xtr - x0))**0.8

else:
    raise ValueError(
        "skin.method must be 'fullyTurbulent' or 'mixed'."
    )

# 7. Form factors
tcLift = np.array([wing.tcMean, tail.tcHT, tail.tcVT])

sweepC4_deg = np.array([
    wing.sweepC4_deg,
    tail.sweepC4_HT_deg,
    tail.sweepC4_VT_deg,
])

if np.any(tcLift > 0.21):
    warnings.warn(
        "Eq. 15-62 is outside its stated t/c <= 0.21 range "
        "for at least one surface."
    )

if formFactor.liftingSurfaceMethod.lower() == "eq15-62":
    FF_lift = 1 + 2.7 * tcLift + 100 * tcLift**4

elif formFactor.liftingSurfaceMethod.lower() == "eq15-63":
    sweep = np.deg2rad(sweepC4_deg)

    sweepTerm = (
        (2 - Mach**2) * np.cos(sweep)
        / np.sqrt(1 - Mach**2 * np.cos(sweep)**2)
    )

    FF_lift = 1 + sweepTerm * tcLift + 100 * tcLift**4

else:
    raise ValueError(
        "Use formFactor.liftingSurfaceMethod = 'Eq15-62' or 'Eq15-63'."
    )

finenessRatio = aircraft.fuselageLength_ft / aircraft.fuselageDmax_ft
FF_fuselage = 1 + 60 / finenessRatio**3 + finenessRatio / 400

FF = np.array([
    FF_lift[0],
    FF_fuselage,
    FF_lift[1],
    FF_lift[2],
])

# 8. Component buildup to CDmin and CRUD correction
CD_component = Cf * FF * IFvec * Swet / aircraft.Sref_ft2

CDmisc = 0
CDminBeforeCRUD = np.sum(CD_component) + CDmisc

crud = SimpleNamespace(
    enabled=True,
    factor=1.25,
)

if crud.enabled:
    CDmin = crud.factor * CDminBeforeCRUD
else:
    CDmin = CDminBeforeCRUD

# 9. Preliminary drag polar and cruise operating point
polar = SimpleNamespace(
    e=0.8,
    CLminD=0.0,
    CLmin=0.0,
    CLmax=1.4,
    numPoints=201,
)

K = 1 / (np.pi * aircraft.AR * polar.e)

CL = np.linspace(polar.CLmin, polar.CLmax, polar.numPoints)
CD = CDmin + K * (CL - polar.CLminD)**2

CLcruise = flight.weight_lbf / (q * aircraft.Sref_ft2)
CDcruise = CDmin + K * (CLcruise - polar.CLminD)**2

# 10. Plots
fig, ax = plt.subplots(facecolor="white")

ax.plot(
    CD, CL,
    linewidth=1.8,
    label="Component-build-up polar",
)

idx = np.argmax(CL / CD)
CL_best = CL[idx]
CD_best = CD[idx]

ax.plot(CD_best, CL_best, "ko", label="Max L/D point")

ax.grid(True)
ax.set_xlabel(r"$C_D$")
ax.set_ylabel(r"$C_L$")
ax.legend(loc="best")
fig.tight_layout()

fig, ax = plt.subplots(facecolor="white")

ax.bar(component, CD_component)
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")

ax.grid(True, axis="y")
ax.set_axisbelow(True)
ax.set_ylabel(r"Contribution to $C_D$ (based on common $S_{\mathrm{ref}}$)")
fig.tight_layout()

plt.show()

print(f"CDmin = {CDmin:.5f}")
print(f"Max L/D = {np.max(CL/CD)}")
