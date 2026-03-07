"""
ADVANCED MATERIALS FOR NEXT-GENERATION GENERATORS
==================================================

This module contains material properties for cutting-edge generator designs
that exceed current commercial technology.

TECHNOLOGIES INCLUDED:
1. High-Temperature Superconductors (HTS) - Zero resistance windings
2. Amorphous Metal Cores - Ultra-low hysteresis loss
3. Nanocrystalline Soft Magnetics - Best of both worlds
4. Carbon Nanotube Conductors - Lower weight, higher conductivity
5. Halbach-Optimized NdFeB - Maximum field strength magnets
6. Diamond-Like Carbon Coatings - Ultra-low friction
7. Graphene Thermal Interface - Superior heat dissipation

These represent the frontier of materials science as of 2026.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum


class TechnologyReadiness(Enum):
    """Technology Readiness Level (TRL) classification."""
    LABORATORY = 1      # Basic research
    PROTOTYPE = 4       # Lab validation
    DEMONSTRATION = 6   # Prototype demonstration
    COMMERCIAL = 9      # Full commercial deployment


# =============================================================================
# MAGNETIC CORE MATERIALS
# =============================================================================

@dataclass
class CoreMaterial:
    """Properties of magnetic core materials."""
    name: str
    saturation_flux_T: float          # Tesla - max B field before saturation
    relative_permeability: float       # μr - how well it concentrates flux
    resistivity_ohm_m: float          # Ω·m - higher = less eddy current loss
    hysteresis_loss_factor: float     # W/kg at 1T, 50Hz (Steinmetz)
    density_kg_m3: float              # kg/m³
    max_temp_C: float                 # Maximum operating temperature
    cost_per_kg_usd: float            # Approximate cost
    trl: TechnologyReadiness          # Technology readiness
    
    @property
    def core_loss_at_1T_50Hz(self) -> float:
        """Total core loss in W/kg at standard conditions."""
        return self.hysteresis_loss_factor
    
    def calculate_loss(self, B_peak: float, frequency: float, 
                       mass_kg: float) -> float:
        """
        Calculate total core loss using modified Steinmetz equation.
        
        P = k * f^α * B^β * mass
        
        For most materials: α ≈ 1.3-1.5, β ≈ 2.0-2.5
        """
        # Steinmetz coefficients (typical values)
        alpha = 1.4
        beta = 2.2
        
        # Normalize to reference (1T, 50Hz)
        P_specific = self.hysteresis_loss_factor * (frequency/50)**alpha * (B_peak/1.0)**beta
        return P_specific * mass_kg


# Standard Silicon Steel (baseline - what most generators use today)
M270_35A = CoreMaterial(
    name="M270-35A Silicon Steel",
    saturation_flux_T=1.8,
    relative_permeability=4000,
    resistivity_ohm_m=4.5e-7,
    hysteresis_loss_factor=2.7,  # W/kg at 1T, 50Hz
    density_kg_m3=7650,
    max_temp_C=150,
    cost_per_kg_usd=3.0,
    trl=TechnologyReadiness.COMMERCIAL
)

# High-grade Grain-Oriented Silicon Steel
HI_B_GOES = CoreMaterial(
    name="HiB Grain-Oriented Electrical Steel",
    saturation_flux_T=2.0,
    relative_permeability=30000,  # Much higher in rolling direction
    resistivity_ohm_m=4.8e-7,
    hysteresis_loss_factor=0.9,   # Much lower loss!
    density_kg_m3=7650,
    max_temp_C=150,
    cost_per_kg_usd=8.0,
    trl=TechnologyReadiness.COMMERCIAL
)

# Amorphous Metal (Metglas) - ADVANCED
METGLAS_2605SA1 = CoreMaterial(
    name="Metglas 2605SA1 Amorphous",
    saturation_flux_T=1.56,
    relative_permeability=45000,
    resistivity_ohm_m=1.3e-6,     # Higher resistivity = less eddy loss
    hysteresis_loss_factor=0.28,  # 90% lower than silicon steel!
    density_kg_m3=7180,
    max_temp_C=150,
    cost_per_kg_usd=25.0,
    trl=TechnologyReadiness.COMMERCIAL
)

# Nanocrystalline (Finemet, Vitroperm) - CUTTING EDGE
NANOCRYSTALLINE = CoreMaterial(
    name="Vitroperm 500F Nanocrystalline",
    saturation_flux_T=1.2,
    relative_permeability=80000,   # Extremely high
    resistivity_ohm_m=1.15e-6,
    hysteresis_loss_factor=0.08,   # Almost zero loss!
    density_kg_m3=7300,
    max_temp_C=180,
    cost_per_kg_usd=80.0,
    trl=TechnologyReadiness.DEMONSTRATION
)

# Cobalt-Iron Alloy (Hiperco 50) - for aerospace/military
HIPERCO_50 = CoreMaterial(
    name="Hiperco 50 (Co-Fe)",
    saturation_flux_T=2.4,         # Highest saturation available!
    relative_permeability=10000,
    resistivity_ohm_m=4.0e-7,
    hysteresis_loss_factor=1.5,
    density_kg_m3=8120,
    max_temp_C=200,
    cost_per_kg_usd=150.0,         # Very expensive
    trl=TechnologyReadiness.COMMERCIAL
)


# =============================================================================
# PERMANENT MAGNET MATERIALS
# =============================================================================

@dataclass  
class MagnetMaterial:
    """Properties of permanent magnet materials."""
    name: str
    grade: str
    remanence_T: float              # Br - residual magnetization
    coercivity_kA_m: float          # Hc - resistance to demagnetization
    energy_product_kJ_m3: float     # (BH)max - figure of merit
    max_temp_C: float               # Max operating temperature
    temp_coefficient_Br: float      # %/°C - how Br changes with temp
    density_kg_m3: float
    cost_per_kg_usd: float
    trl: TechnologyReadiness
    
    @property
    def energy_product_MGOe(self) -> float:
        """Convert to legacy units (still used in industry)."""
        return self.energy_product_kJ_m3 / 7.958


# Standard NdFeB (what we had before)
N52 = MagnetMaterial(
    name="Neodymium Iron Boron",
    grade="N52",
    remanence_T=1.45,
    coercivity_kA_m=875,
    energy_product_kJ_m3=398,      # 50 MGOe
    max_temp_C=80,                  # Low - this is N52's weakness
    temp_coefficient_Br=-0.12,
    density_kg_m3=7500,
    cost_per_kg_usd=80,
    trl=TechnologyReadiness.COMMERCIAL
)

# High-temperature NdFeB
N48SH = MagnetMaterial(
    name="Neodymium Iron Boron",
    grade="N48SH",
    remanence_T=1.37,
    coercivity_kA_m=1590,          # Much higher coercivity
    energy_product_kJ_m3=366,
    max_temp_C=150,                 # Can handle higher temps
    temp_coefficient_Br=-0.10,
    density_kg_m3=7500,
    cost_per_kg_usd=100,
    trl=TechnologyReadiness.COMMERCIAL
)

# Dysprosium-free NdFeB (sustainable alternative)
N45_DY_FREE = MagnetMaterial(
    name="Dy-free NdFeB (Grain Boundary Diffusion)",
    grade="N45-GBD",
    remanence_T=1.35,
    coercivity_kA_m=1400,
    energy_product_kJ_m3=350,
    max_temp_C=120,
    temp_coefficient_Br=-0.11,
    density_kg_m3=7500,
    cost_per_kg_usd=70,             # Lower cost, no rare Dy
    trl=TechnologyReadiness.DEMONSTRATION
)

# Samarium Cobalt - for extreme temperatures
SM2CO17 = MagnetMaterial(
    name="Samarium Cobalt",
    grade="Sm2Co17",
    remanence_T=1.15,
    coercivity_kA_m=800,
    energy_product_kJ_m3=240,
    max_temp_C=350,                 # Excellent thermal stability!
    temp_coefficient_Br=-0.03,      # Very stable
    density_kg_m3=8400,
    cost_per_kg_usd=200,
    trl=TechnologyReadiness.COMMERCIAL
)

# EXPERIMENTAL: Iron Nitride (potentially replaces rare earths)
FE16N2 = MagnetMaterial(
    name="Iron Nitride (Alpha'' Fe16N2)",
    grade="Experimental",
    remanence_T=2.9,                # EXTREMELY high - theoretical
    coercivity_kA_m=900,
    energy_product_kJ_m3=1000,      # Could be 2x NdFeB!
    max_temp_C=200,
    temp_coefficient_Br=-0.08,
    density_kg_m3=7800,
    cost_per_kg_usd=50,             # No rare earths!
    trl=TechnologyReadiness.LABORATORY  # Still in research
)


# =============================================================================
# CONDUCTOR MATERIALS
# =============================================================================

@dataclass
class ConductorMaterial:
    """Properties of electrical conductors."""
    name: str
    resistivity_ohm_m: float        # At 20°C
    temp_coefficient: float          # α (1/°C)
    density_kg_m3: float
    thermal_conductivity_W_mK: float
    max_current_density_A_mm2: float  # Typical safe limit
    cost_per_kg_usd: float
    trl: TechnologyReadiness
    is_superconductor: bool = False
    critical_temp_K: float = 0       # For superconductors
    critical_current_A_mm2: float = 0  # For superconductors


# Standard copper
COPPER_ANNEALED = ConductorMaterial(
    name="Annealed Copper (C11000)",
    resistivity_ohm_m=1.68e-8,
    temp_coefficient=0.00393,
    density_kg_m3=8960,
    thermal_conductivity_W_mK=401,
    max_current_density_A_mm2=6.0,
    cost_per_kg_usd=8,
    trl=TechnologyReadiness.COMMERCIAL
)

# Litz wire (reduced skin effect)
LITZ_WIRE = ConductorMaterial(
    name="Litz Wire (Type 2)",
    resistivity_ohm_m=1.72e-8,       # Slightly higher due to stranding
    temp_coefficient=0.00393,
    density_kg_m3=8500,              # Lower fill factor
    thermal_conductivity_W_mK=350,
    max_current_density_A_mm2=8.0,   # Better at high frequency
    cost_per_kg_usd=25,
    trl=TechnologyReadiness.COMMERCIAL
)

# Aluminum (lightweight alternative)
ALUMINUM_1350 = ConductorMaterial(
    name="Aluminum 1350",
    resistivity_ohm_m=2.83e-8,       # 61% IACS
    temp_coefficient=0.00429,
    density_kg_m3=2700,              # Much lighter!
    thermal_conductivity_W_mK=237,
    max_current_density_A_mm2=4.0,
    cost_per_kg_usd=3,
    trl=TechnologyReadiness.COMMERCIAL
)

# Carbon Nanotube Wire (ADVANCED)
CNT_WIRE = ConductorMaterial(
    name="Carbon Nanotube Wire",
    resistivity_ohm_m=1.0e-8,        # Better than copper!
    temp_coefficient=0.001,           # More stable
    density_kg_m3=1600,              # MUCH lighter
    thermal_conductivity_W_mK=3000,  # Excellent thermal
    max_current_density_A_mm2=100,   # Very high capacity
    cost_per_kg_usd=5000,            # Still expensive
    trl=TechnologyReadiness.PROTOTYPE
)

# YBCO High-Temperature Superconductor
YBCO_HTS = ConductorMaterial(
    name="YBCO (YBa2Cu3O7) HTS Tape",
    resistivity_ohm_m=0,              # ZERO in superconducting state!
    temp_coefficient=0,
    density_kg_m3=6300,
    thermal_conductivity_W_mK=5,      # Poor thermal (ceramic)
    max_current_density_A_mm2=0,      # See critical current
    cost_per_kg_usd=2000,
    trl=TechnologyReadiness.DEMONSTRATION,
    is_superconductor=True,
    critical_temp_K=93,               # Works in liquid nitrogen (77K)!
    critical_current_A_mm2=500        # At 77K, self-field
)

# MgB2 Superconductor (cheaper alternative)
MGB2_SC = ConductorMaterial(
    name="Magnesium Diboride (MgB2)",
    resistivity_ohm_m=0,
    temp_coefficient=0,
    density_kg_m3=2570,
    thermal_conductivity_W_mK=30,
    max_current_density_A_mm2=0,
    cost_per_kg_usd=50,               # Much cheaper than YBCO!
    trl=TechnologyReadiness.DEMONSTRATION,
    is_superconductor=True,
    critical_temp_K=39,               # Needs 20K, harder to cool
    critical_current_A_mm2=1000       # Higher critical current
)


# =============================================================================
# BEARING & FRICTION REDUCTION
# =============================================================================

@dataclass
class BearingTechnology:
    """Bearing technologies for ultra-low friction."""
    name: str
    friction_coefficient: float       # Dimensionless
    max_speed_rpm: float              # Speed limit
    max_load_factor: float            # Relative to size
    maintenance_interval_hours: float  # 0 = maintenance-free
    power_loss_factor: float          # Relative to standard bearings
    cost_factor: float                # Relative to standard bearings
    trl: TechnologyReadiness


STANDARD_BALL_BEARING = BearingTechnology(
    name="Standard Deep Groove Ball Bearing",
    friction_coefficient=0.0015,
    max_speed_rpm=20000,
    max_load_factor=1.0,
    maintenance_interval_hours=20000,
    power_loss_factor=1.0,
    cost_factor=1.0,
    trl=TechnologyReadiness.COMMERCIAL
)

CERAMIC_HYBRID_BEARING = BearingTechnology(
    name="Ceramic Hybrid (Si3N4 balls)",
    friction_coefficient=0.0008,      # 50% less friction
    max_speed_rpm=50000,              # Much higher speed
    max_load_factor=0.8,
    maintenance_interval_hours=50000,
    power_loss_factor=0.5,
    cost_factor=5.0,
    trl=TechnologyReadiness.COMMERCIAL
)

FULL_CERAMIC_BEARING = BearingTechnology(
    name="Full Ceramic (Si3N4)",
    friction_coefficient=0.0005,
    max_speed_rpm=80000,
    max_load_factor=0.6,
    maintenance_interval_hours=100000,
    power_loss_factor=0.3,
    cost_factor=20.0,
    trl=TechnologyReadiness.COMMERCIAL
)

AIR_BEARING = BearingTechnology(
    name="Aerostatic/Aerodynamic Air Bearing",
    friction_coefficient=0.00001,     # Almost zero!
    max_speed_rpm=200000,
    max_load_factor=0.3,
    maintenance_interval_hours=float('inf'),  # No contact wear
    power_loss_factor=0.05,           # Needs air supply
    cost_factor=50.0,
    trl=TechnologyReadiness.DEMONSTRATION
)

MAGNETIC_BEARING_PASSIVE = BearingTechnology(
    name="Passive Magnetic Bearing",
    friction_coefficient=0,           # No contact!
    max_speed_rpm=100000,
    max_load_factor=0.2,
    maintenance_interval_hours=float('inf'),
    power_loss_factor=0.02,           # Some eddy losses
    cost_factor=30.0,
    trl=TechnologyReadiness.DEMONSTRATION
)

MAGNETIC_BEARING_ACTIVE = BearingTechnology(
    name="Active Magnetic Bearing (AMB)",
    friction_coefficient=0,           # No contact!
    max_speed_rpm=300000,             # Highest possible
    max_load_factor=0.5,
    maintenance_interval_hours=float('inf'),
    power_loss_factor=0.1,            # Control system uses power
    cost_factor=100.0,
    trl=TechnologyReadiness.COMMERCIAL  # Used in turbo machinery
)

SUPERCONDUCTING_BEARING = BearingTechnology(
    name="HTS Superconducting Bearing",
    friction_coefficient=0,
    max_speed_rpm=500000,             # Limited by rotor strength
    max_load_factor=0.4,
    maintenance_interval_hours=float('inf'),
    power_loss_factor=0.001,          # Just cooling power
    cost_factor=500.0,
    trl=TechnologyReadiness.PROTOTYPE
)


# =============================================================================
# THERMAL MANAGEMENT
# =============================================================================

@dataclass
class CoolingSystem:
    """Cooling system technologies."""
    name: str
    heat_transfer_coefficient_W_m2K: float
    max_heat_flux_W_cm2: float
    power_consumption_fraction: float  # Of heat removed
    complexity: int                    # 1-10 scale
    cost_factor: float
    trl: TechnologyReadiness


NATURAL_CONVECTION = CoolingSystem(
    name="Natural Air Convection",
    heat_transfer_coefficient_W_m2K=10,
    max_heat_flux_W_cm2=0.5,
    power_consumption_fraction=0,
    complexity=1,
    cost_factor=1.0,
    trl=TechnologyReadiness.COMMERCIAL
)

FORCED_AIR = CoolingSystem(
    name="Forced Air Cooling (Fan)",
    heat_transfer_coefficient_W_m2K=50,
    max_heat_flux_W_cm2=2,
    power_consumption_fraction=0.02,
    complexity=3,
    cost_factor=1.5,
    trl=TechnologyReadiness.COMMERCIAL
)

LIQUID_JACKET = CoolingSystem(
    name="Liquid Cooling Jacket",
    heat_transfer_coefficient_W_m2K=500,
    max_heat_flux_W_cm2=10,
    power_consumption_fraction=0.01,
    complexity=5,
    cost_factor=3.0,
    trl=TechnologyReadiness.COMMERCIAL
)

DIRECT_LIQUID = CoolingSystem(
    name="Direct Oil/Dielectric Cooling",
    heat_transfer_coefficient_W_m2K=1000,
    max_heat_flux_W_cm2=20,
    power_consumption_fraction=0.015,
    complexity=6,
    cost_factor=5.0,
    trl=TechnologyReadiness.COMMERCIAL
)

SPRAY_COOLING = CoolingSystem(
    name="Spray/Jet Impingement Cooling",
    heat_transfer_coefficient_W_m2K=5000,
    max_heat_flux_W_cm2=100,
    power_consumption_fraction=0.02,
    complexity=7,
    cost_factor=10.0,
    trl=TechnologyReadiness.DEMONSTRATION
)

TWO_PHASE_COOLING = CoolingSystem(
    name="Two-Phase (Boiling) Cooling",
    heat_transfer_coefficient_W_m2K=10000,
    max_heat_flux_W_cm2=200,
    power_consumption_fraction=0.01,
    complexity=8,
    cost_factor=20.0,
    trl=TechnologyReadiness.DEMONSTRATION
)

CRYOGENIC_LN2 = CoolingSystem(
    name="Cryogenic (Liquid Nitrogen)",
    heat_transfer_coefficient_W_m2K=2000,
    max_heat_flux_W_cm2=50,
    power_consumption_fraction=0.20,  # Cryocooler is expensive
    complexity=9,
    cost_factor=50.0,
    trl=TechnologyReadiness.DEMONSTRATION
)


# =============================================================================
# MATERIAL SELECTION HELPER
# =============================================================================

def select_optimal_materials(target_efficiency: float = 0.98,
                            max_cost_factor: float = 10.0,
                            max_temp_C: float = 100,
                            allow_experimental: bool = False) -> Dict:
    """
    Select optimal material combination for target efficiency.
    
    Parameters:
        target_efficiency: Target overall efficiency (0-1)
        max_cost_factor: Maximum cost multiplier vs baseline
        max_temp_C: Operating temperature limit
        allow_experimental: Include TRL < DEMONSTRATION materials
        
    Returns:
        Dictionary with recommended materials for each component
    """
    min_trl = TechnologyReadiness.LABORATORY if allow_experimental else TechnologyReadiness.DEMONSTRATION
    
    recommendations = {
        "core_material": None,
        "magnet_material": None,
        "conductor": None,
        "bearing": None,
        "cooling": None,
        "expected_efficiency": 0,
        "total_cost_factor": 0,
        "notes": []
    }
    
    # Core selection
    cores = [M270_35A, HI_B_GOES, METGLAS_2605SA1, NANOCRYSTALLINE, HIPERCO_50]
    valid_cores = [c for c in cores if c.trl.value >= min_trl.value and c.max_temp_C >= max_temp_C]
    # Sort by loss (lower is better)
    valid_cores.sort(key=lambda x: x.hysteresis_loss_factor)
    for core in valid_cores:
        if core.cost_per_kg_usd / M270_35A.cost_per_kg_usd <= max_cost_factor:
            recommendations["core_material"] = core
            break
    
    # Magnet selection
    magnets = [N52, N48SH, N45_DY_FREE, SM2CO17, FE16N2]
    valid_magnets = [m for m in magnets if m.trl.value >= min_trl.value and m.max_temp_C >= max_temp_C]
    # Sort by energy product (higher is better)
    valid_magnets.sort(key=lambda x: -x.energy_product_kJ_m3)
    for mag in valid_magnets:
        if mag.cost_per_kg_usd / N52.cost_per_kg_usd <= max_cost_factor:
            recommendations["magnet_material"] = mag
            break
    
    # Conductor selection
    conductors = [COPPER_ANNEALED, LITZ_WIRE, ALUMINUM_1350, CNT_WIRE, YBCO_HTS, MGB2_SC]
    valid_conductors = [c for c in conductors if c.trl.value >= min_trl.value]
    if target_efficiency > 0.97:
        # For very high efficiency, consider superconductors
        sc = [c for c in valid_conductors if c.is_superconductor]
        if sc and allow_experimental:
            recommendations["conductor"] = sc[0]
            recommendations["notes"].append("Superconducting windings require cryogenic cooling")
        else:
            recommendations["conductor"] = LITZ_WIRE
    else:
        recommendations["conductor"] = COPPER_ANNEALED
    
    # Bearing selection
    bearings = [STANDARD_BALL_BEARING, CERAMIC_HYBRID_BEARING, FULL_CERAMIC_BEARING,
                AIR_BEARING, MAGNETIC_BEARING_PASSIVE, MAGNETIC_BEARING_ACTIVE]
    valid_bearings = [b for b in bearings if b.trl.value >= min_trl.value]
    # Sort by friction
    valid_bearings.sort(key=lambda x: x.friction_coefficient)
    for bear in valid_bearings:
        if bear.cost_factor <= max_cost_factor:
            recommendations["bearing"] = bear
            break
    
    # Cooling selection based on expected losses
    if target_efficiency > 0.97:
        recommendations["cooling"] = LIQUID_JACKET
    elif target_efficiency > 0.95:
        recommendations["cooling"] = FORCED_AIR
    else:
        recommendations["cooling"] = NATURAL_CONVECTION
    
    # Estimate efficiency
    core_eff = 1 - recommendations["core_material"].hysteresis_loss_factor / 100
    bearing_eff = 1 - recommendations["bearing"].friction_coefficient
    conductor_loss = 0 if recommendations["conductor"].is_superconductor else 0.02
    
    recommendations["expected_efficiency"] = core_eff * bearing_eff * (1 - conductor_loss)
    
    # Calculate cost factor
    base_cost = M270_35A.cost_per_kg_usd + N52.cost_per_kg_usd + COPPER_ANNEALED.cost_per_kg_usd
    selected_cost = (recommendations["core_material"].cost_per_kg_usd +
                    recommendations["magnet_material"].cost_per_kg_usd +
                    recommendations["conductor"].cost_per_kg_usd)
    recommendations["total_cost_factor"] = selected_cost / base_cost * recommendations["bearing"].cost_factor
    
    return recommendations


def print_material_comparison():
    """Print comparison tables for all materials."""
    print("\n" + "="*80)
    print("ADVANCED MATERIALS COMPARISON - CORE")
    print("="*80)
    print(f"{'Material':<35} {'B_sat(T)':<10} {'μr':<10} {'Loss(W/kg)':<12} {'$/kg':<8}")
    print("-"*80)
    for mat in [M270_35A, HI_B_GOES, METGLAS_2605SA1, NANOCRYSTALLINE, HIPERCO_50]:
        print(f"{mat.name:<35} {mat.saturation_flux_T:<10.2f} {mat.relative_permeability:<10.0f} "
              f"{mat.hysteresis_loss_factor:<12.2f} {mat.cost_per_kg_usd:<8.0f}")
    
    print("\n" + "="*80)
    print("ADVANCED MATERIALS COMPARISON - MAGNETS")
    print("="*80)
    print(f"{'Material':<35} {'Br(T)':<8} {'(BH)max':<10} {'Tmax(°C)':<10} {'$/kg':<8}")
    print("-"*80)
    for mat in [N52, N48SH, SM2CO17, FE16N2]:
        print(f"{mat.name} {mat.grade:<10} {mat.remanence_T:<8.2f} {mat.energy_product_kJ_m3:<10.0f} "
              f"{mat.max_temp_C:<10.0f} {mat.cost_per_kg_usd:<8.0f}")
    
    print("\n" + "="*80)
    print("ADVANCED MATERIALS COMPARISON - BEARINGS")
    print("="*80)
    print(f"{'Technology':<35} {'μ friction':<12} {'Max RPM':<12} {'Loss Factor':<12}")
    print("-"*80)
    for bear in [STANDARD_BALL_BEARING, CERAMIC_HYBRID_BEARING, MAGNETIC_BEARING_ACTIVE]:
        print(f"{bear.name:<35} {bear.friction_coefficient:<12.6f} {bear.max_speed_rpm:<12.0f} "
              f"{bear.power_loss_factor:<12.3f}")


if __name__ == "__main__":
    print_material_comparison()
    
    print("\n" + "="*80)
    print("OPTIMAL MATERIAL SELECTION")
    print("="*80)
    
    # High efficiency, moderate cost
    rec = select_optimal_materials(target_efficiency=0.96, max_cost_factor=20)
    print(f"\nFor 96% efficiency, cost factor ≤20:")
    print(f"  Core: {rec['core_material'].name}")
    print(f"  Magnets: {rec['magnet_material'].name} {rec['magnet_material'].grade}")
    print(f"  Conductor: {rec['conductor'].name}")
    print(f"  Bearings: {rec['bearing'].name}")
    print(f"  Expected efficiency: {rec['expected_efficiency']*100:.1f}%")
