"""
Physical Constants for Permanent Magnet Generator Design
=========================================================
All values in SI units unless otherwise specified.
"""

import numpy as np

# Fundamental Constants
MU_0 = 4 * np.pi * 1e-7          # Vacuum permeability (H/m)
EPSILON_0 = 8.854187817e-12      # Vacuum permittivity (F/m)
E_CHARGE = 1.602176634e-19       # Elementary charge (C)
C_LIGHT = 299792458              # Speed of light (m/s)

# Material Properties - NdFeB N52 Magnets (Best permanent magnets)
BR_NEODYMIUM = 1.45              # Remanent flux density (T)
HC_NEODYMIUM = 1115000           # Coercivity (A/m)
BH_MAX_NEODYMIUM = 422000        # Max energy product (J/m³)
CURIE_TEMP_NEODYMIUM = 310       # Curie temperature (°C)

# Material Properties - Ferrite Magnets (Alternative)
BR_FERRITE = 0.4                 # Remanent flux density (T)
HC_FERRITE = 250000              # Coercivity (A/m)

# Copper Wire Properties (for coils)
RESISTIVITY_COPPER = 1.68e-8     # Electrical resistivity (Ω·m)
DENSITY_COPPER = 8960            # Density (kg/m³)
TEMP_COEF_COPPER = 0.00393       # Temperature coefficient (1/°C)

# Iron Core Properties (Silicon Steel)
MU_R_IRON = 4000                 # Relative permeability
RESISTIVITY_IRON = 4.72e-7       # Electrical resistivity (Ω·m)
SATURATION_FLUX = 1.8            # Saturation flux density (T)
HYSTERESIS_COEF = 0.002          # Hysteresis loss coefficient

# Mechanical Properties
DENSITY_STEEL = 7850             # kg/m³
DENSITY_ALUMINUM = 2700          # kg/m³
DENSITY_NEODYMIUM = 7500         # kg/m³

# Bearing Properties (Ceramic Hybrid Bearings)
BEARING_FRICTION_COEF = 0.001    # Friction coefficient
BEARING_RATED_SPEED = 50000      # RPM

# Environmental Constants
AIR_DENSITY = 1.225              # kg/m³ at 15°C, 1 atm
AIR_VISCOSITY = 1.81e-5          # Dynamic viscosity (Pa·s)

# Design Defaults
DEFAULT_AIRGAP = 0.001           # 1mm air gap
DEFAULT_POLES = 12               # Number of magnetic poles
DEFAULT_SLOTS = 18               # Number of stator slots (3:2 ratio for 3-phase)
DEFAULT_PHASES = 3               # Three-phase output


class MagnetMaterial:
    """Class to hold magnet material properties"""
    
    def __init__(self, name: str, Br: float, Hc: float, BHmax: float, 
                 density: float, curie_temp: float):
        self.name = name
        self.Br = Br                # Remanent flux density (T)
        self.Hc = Hc                # Coercivity (A/m)
        self.BHmax = BHmax          # Maximum energy product (J/m³)
        self.density = density      # Density (kg/m³)
        self.curie_temp = curie_temp  # Curie temperature (°C)
        
    def get_flux_at_field(self, H: float) -> float:
        """Calculate B for given H on demagnetization curve"""
        # Linear approximation of demagnetization curve
        if H >= 0:
            return self.Br
        elif H <= -self.Hc:
            return 0
        else:
            return self.Br * (1 + H / self.Hc)


# Predefined Materials
N52_NEODYMIUM = MagnetMaterial(
    name="N52 NdFeB",
    Br=1.45,
    Hc=1115000,
    BHmax=422000,
    density=7500,
    curie_temp=310
)

N42_NEODYMIUM = MagnetMaterial(
    name="N42 NdFeB",
    Br=1.32,
    Hc=955000,
    BHmax=342000,
    density=7500,
    curie_temp=310
)

FERRITE_Y30 = MagnetMaterial(
    name="Y30 Ferrite",
    Br=0.38,
    Hc=230000,
    BHmax=27000,
    density=4800,
    curie_temp=450
)

SAMARIUM_COBALT = MagnetMaterial(
    name="SmCo 2:17",
    Br=1.12,
    Hc=840000,
    BHmax=240000,
    density=8400,
    curie_temp=800  # High temperature stability
)
