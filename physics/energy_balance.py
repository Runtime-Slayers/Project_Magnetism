"""
Energy Balance and Efficiency Calculations
============================================
Comprehensive energy analysis for the PMG including:
- Power input/output balance
- Loss mechanisms (friction, eddy currents, hysteresis, windage)
- Efficiency optimization
- Heat generation estimates
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass, field
from .constants import (MU_0, RESISTIVITY_COPPER, RESISTIVITY_IRON,
                        AIR_DENSITY, AIR_VISCOSITY, BEARING_FRICTION_COEF,
                        HYSTERESIS_COEF, SATURATION_FLUX)


@dataclass
class GeneratorSpecs:
    """Complete generator specification"""
    # Geometry
    rotor_radius: float = 0.05       # meters
    stator_outer_radius: float = 0.08
    axial_length: float = 0.10       # meters
    air_gap: float = 0.001           # 1mm
    
    # Magnetic
    n_poles: int = 12
    n_slots: int = 18                # 3:2 ratio for 3-phase
    n_phases: int = 3
    B_airgap: float = 0.8            # Tesla
    magnet_Br: float = 1.45          # NdFeB N52
    
    # Electrical
    n_turns_per_coil: int = 100
    wire_diameter: float = 0.001     # 1mm wire
    coil_resistance: float = 0.0     # Calculated
    
    # Mechanical
    shaft_radius: float = 0.01       # 10mm shaft
    rotor_mass: float = 2.0          # kg
    bearing_type: str = "ceramic_hybrid"
    
    # Operating conditions
    rpm: float = 3000
    load_resistance: float = 10.0    # Ohms
    ambient_temp: float = 25.0       # °C
    
    def __post_init__(self):
        """Calculate derived values"""
        self.omega = 2 * np.pi * self.rpm / 60  # rad/s
        self.electrical_freq = self.n_poles * self.rpm / 120  # Hz
        self.stator_inner_radius = self.rotor_radius + self.air_gap
        
        # Calculate coil resistance
        coil_length = 2 * np.pi * self.rotor_radius * self.n_turns_per_coil
        wire_area = np.pi * (self.wire_diameter/2)**2
        self.coil_resistance = RESISTIVITY_COPPER * coil_length / wire_area


def calculate_all_losses(specs: GeneratorSpecs) -> Dict[str, float]:
    """
    Calculate all power loss mechanisms.
    
    Total Loss = P_copper + P_iron + P_friction + P_windage + P_stray
    
    This is critical for efficiency analysis!
    """
    
    # 1. COPPER LOSSES (I²R losses in windings)
    # P_cu = I² × R × n_phases
    # Estimate current from induced EMF and load
    emf_peak = specs.n_turns_per_coil * specs.B_airgap * \
               (2 * specs.rotor_radius * specs.axial_length) * specs.omega
    current_rms = emf_peak / (np.sqrt(2) * (specs.coil_resistance + specs.load_resistance))
    P_copper = specs.n_phases * current_rms**2 * specs.coil_resistance
    
    # 2. IRON LOSSES (Core losses)
    # P_iron = P_hysteresis + P_eddy
    
    # Hysteresis loss: P_h = k_h × f × B_max^n × volume
    # Steinmetz equation with n ≈ 1.6-2.0
    iron_volume = np.pi * (specs.stator_outer_radius**2 - 
                          specs.stator_inner_radius**2) * specs.axial_length
    P_hysteresis = HYSTERESIS_COEF * specs.electrical_freq * \
                   (specs.B_airgap**1.8) * iron_volume
    
    # Eddy current loss: P_e = k_e × f² × B_max² × thickness² × volume
    lamination_thickness = 0.35e-3  # 0.35mm silicon steel laminations
    k_eddy = (np.pi**2 * lamination_thickness**2) / (6 * RESISTIVITY_IRON)
    P_eddy = k_eddy * specs.electrical_freq**2 * specs.B_airgap**2 * iron_volume
    
    P_iron = P_hysteresis + P_eddy
    
    # 3. FRICTION LOSSES (Bearings)
    # P_friction = μ × F_radial × v = μ × (m × ω² × r) × (ω × r_bearing)
    # For well-designed system with ceramic bearings:
    radial_load = specs.rotor_mass * specs.omega**2 * 0.001  # Approximate
    bearing_velocity = specs.omega * specs.shaft_radius
    P_friction = BEARING_FRICTION_COEF * radial_load * bearing_velocity * 2  # Two bearings
    
    # 4. WINDAGE LOSSES (Air drag on rotor)
    # P_windage = C_f × ρ × ω³ × r⁴ × L
    # Where C_f is friction coefficient
    reynolds = AIR_DENSITY * specs.omega * specs.rotor_radius**2 / AIR_VISCOSITY
    if reynolds < 3e5:
        Cf = 0.515 / reynolds**0.5  # Laminar
    else:
        Cf = 0.0325 / reynolds**0.2  # Turbulent
    
    P_windage = Cf * AIR_DENSITY * specs.omega**3 * specs.rotor_radius**4 * \
                specs.axial_length
    
    # 5. STRAY LOSSES (Additional losses, typically 1-2% of output)
    P_output_estimate = emf_peak * current_rms * 0.9 * specs.n_phases / np.sqrt(2)
    P_stray = 0.015 * P_output_estimate  # 1.5% stray loss
    
    # Total losses
    P_total_loss = P_copper + P_iron + P_friction + P_windage + P_stray
    
    return {
        "P_copper_loss": P_copper,
        "P_hysteresis_loss": P_hysteresis,
        "P_eddy_loss": P_eddy,
        "P_iron_total": P_iron,
        "P_friction_loss": P_friction,
        "P_windage_loss": P_windage,
        "P_stray_loss": P_stray,
        "P_total_loss": P_total_loss,
        "breakdown_percentage": {
            "copper": 100 * P_copper / P_total_loss,
            "iron": 100 * P_iron / P_total_loss,
            "friction": 100 * P_friction / P_total_loss,
            "windage": 100 * P_windage / P_total_loss,
            "stray": 100 * P_stray / P_total_loss
        }
    }


def calculate_efficiency(specs: GeneratorSpecs) -> Dict[str, float]:
    """
    Calculate overall generator efficiency.
    
    η = P_output / P_input = P_output / (P_output + P_losses)
    
    IMPORTANT: This is NOT "infinite energy" - it converts
    mechanical energy to electrical energy with some losses.
    """
    losses = calculate_all_losses(specs)
    
    # Calculate output power
    emf_peak = specs.n_turns_per_coil * specs.B_airgap * \
               (2 * specs.rotor_radius * specs.axial_length) * specs.omega
    emf_rms = emf_peak / np.sqrt(2)
    
    # Load current
    total_resistance = specs.coil_resistance + specs.load_resistance
    current_rms = emf_rms / total_resistance
    
    # Output power (to load)
    P_output = specs.n_phases * current_rms**2 * specs.load_resistance
    
    # Input mechanical power
    P_input = P_output + losses["P_total_loss"]
    
    # Required input torque
    torque_input = P_input / specs.omega
    
    # Efficiency
    efficiency = P_output / P_input if P_input > 0 else 0
    
    return {
        "emf_peak_V": emf_peak,
        "emf_rms_V": emf_rms,
        "current_rms_A": current_rms,
        "P_output_W": P_output,
        "P_input_W": P_input,
        "P_losses_W": losses["P_total_loss"],
        "efficiency": efficiency,
        "efficiency_percent": 100 * efficiency,
        "torque_required_Nm": torque_input,
        "power_density_W_per_kg": P_output / specs.rotor_mass,
        "loss_breakdown": losses["breakdown_percentage"]
    }


def heat_generation_analysis(specs: GeneratorSpecs) -> Dict[str, float]:
    """
    Analyze heat generation for thermal management.
    
    Heat must be dissipated to prevent magnet demagnetization!
    """
    losses = calculate_all_losses(specs)
    
    # Heat generation rate = power loss
    Q_total = losses["P_total_loss"]  # Watts = J/s
    
    # Approximate thermal resistance (simplified model)
    # R_th = 1 / (h × A) where h ≈ 10-25 W/(m²·K) for natural convection
    surface_area = 2 * np.pi * specs.stator_outer_radius * specs.axial_length
    h_convection = 15  # W/(m²·K)
    R_thermal = 1 / (h_convection * surface_area)
    
    # Temperature rise
    delta_T = Q_total * R_thermal
    
    # Operating temperature
    T_operating = specs.ambient_temp + delta_T
    
    # Check against Curie temperature (for NdFeB: ~310°C)
    curie_temp = 310  # °C
    safety_margin = curie_temp - T_operating
    
    return {
        "heat_generation_W": Q_total,
        "surface_area_m2": surface_area,
        "thermal_resistance_K_per_W": R_thermal,
        "temperature_rise_C": delta_T,
        "operating_temp_C": T_operating,
        "curie_temperature_C": curie_temp,
        "safety_margin_C": safety_margin,
        "cooling_required": delta_T > 50,
        "demagnetization_risk": safety_margin < 50
    }


def optimize_for_efficiency(base_specs: GeneratorSpecs,
                           target_power: float = 1000) -> GeneratorSpecs:
    """
    Optimize generator parameters for maximum efficiency
    while meeting target power output.
    
    Uses gradient-based optimization on key parameters.
    """
    from scipy.optimize import minimize
    
    def objective(params):
        """Minimize losses for given power output"""
        specs = GeneratorSpecs(
            rotor_radius=params[0],
            axial_length=params[1],
            n_poles=int(params[2]) * 2,  # Must be even
            air_gap=params[3],
            rpm=params[4]
        )
        
        result = calculate_efficiency(specs)
        
        # Penalty for not meeting power target
        power_penalty = 100 * (result["P_output_W"] - target_power)**2
        
        # Minimize losses
        return result["P_losses_W"] + power_penalty
    
    # Initial guess
    x0 = [0.05, 0.10, 6, 0.001, 3000]
    
    # Bounds
    bounds = [
        (0.02, 0.15),   # rotor radius
        (0.05, 0.20),   # axial length
        (2, 12),        # n_poles/2
        (0.0005, 0.003),# air gap
        (1000, 6000)    # rpm
    ]
    
    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
    
    optimized_specs = GeneratorSpecs(
        rotor_radius=result.x[0],
        axial_length=result.x[1],
        n_poles=int(result.x[2]) * 2,
        air_gap=result.x[3],
        rpm=result.x[4]
    )
    
    return optimized_specs


def energy_conservation_proof():
    """
    IMPORTANT: Mathematical proof that infinite energy is impossible.
    
    This explains the physics so you understand the real constraints.
    """
    explanation = """
    ============================================================
    WHY "INFINITE ELECTRICITY" IS IMPOSSIBLE - BUT HIGH EFFICIENCY IS!
    ============================================================
    
    FUNDAMENTAL LAW: Energy Conservation (1st Law of Thermodynamics)
    Energy cannot be created or destroyed, only converted.
    
    In our generator:
    ═══════════════════════════════════════════════════════════
    
    ENERGY FLOW:
    
    MECHANICAL INPUT  ──►  GENERATOR  ──►  ELECTRICAL OUTPUT
    (Rotation)                            + LOSSES (Heat)
    
    P_mechanical = P_electrical + P_losses
    
    ═══════════════════════════════════════════════════════════
    
    WHAT PERMANENT MAGNETS DO:
    - They provide a CONSTANT magnetic field (no energy input needed to maintain)
    - They DO NOT provide the ENERGY for electricity!
    - The energy comes from the MECHANICAL rotation
    
    WHAT WE CAN OPTIMIZE:
    ✓ Minimize friction losses (bearings, air drag)
    ✓ Minimize electrical losses (copper, iron core)
    ✓ Minimize cogging (smooth rotation)
    ✓ Maximize power density (smaller, lighter)
    
    REALISTIC EXPECTATIONS:
    - Commercial PM generators: 90-96% efficiency
    - Our optimized design target: 92-95% efficiency
    - Losses = 5-10% as heat
    
    THE SOURCE OF MECHANICAL ENERGY STILL NEEDED:
    - Wind turbine
    - Water turbine (hydro)
    - Hand crank
    - Motor (converts other energy to mechanical)
    - Flywheel (stores kinetic energy)
    
    ═══════════════════════════════════════════════════════════
    
    YOUR PROJECT IS VALUABLE because:
    1. High-efficiency generators reduce energy waste
    2. Anti-cogging designs run smoother at low speeds
    3. PM generators need no external excitation (field coils)
    4. Lower maintenance than wound-field generators
    
    ═══════════════════════════════════════════════════════════
    """
    return explanation


@dataclass
class EnergyFlowDiagram:
    """Visual representation of energy flow"""
    input_mechanical_W: float
    output_electrical_W: float
    copper_loss_W: float
    iron_loss_W: float
    friction_loss_W: float
    windage_loss_W: float
    
    def to_sankey_data(self) -> dict:
        """Generate data for a Sankey diagram"""
        return {
            "nodes": [
                {"name": "Mechanical Input"},
                {"name": "Generator"},
                {"name": "Electrical Output"},
                {"name": "Copper Losses"},
                {"name": "Iron Losses"},
                {"name": "Friction Losses"},
                {"name": "Windage Losses"}
            ],
            "links": [
                {"source": 0, "target": 1, "value": self.input_mechanical_W},
                {"source": 1, "target": 2, "value": self.output_electrical_W},
                {"source": 1, "target": 3, "value": self.copper_loss_W},
                {"source": 1, "target": 4, "value": self.iron_loss_W},
                {"source": 1, "target": 5, "value": self.friction_loss_W},
                {"source": 1, "target": 6, "value": self.windage_loss_W}
            ]
        }
    
    def __str__(self) -> str:
        efficiency = self.output_electrical_W / self.input_mechanical_W * 100
        return f"""
╔════════════════════════════════════════════════════════════╗
║              ENERGY FLOW DIAGRAM                           ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║   MECHANICAL INPUT: {self.input_mechanical_W:8.2f} W                         ║
║         │                                                  ║
║         ▼                                                  ║
║   ┌─────────────┐                                         ║
║   │  GENERATOR  │───► ELECTRICAL OUTPUT: {self.output_electrical_W:8.2f} W     ║
║   └─────────────┘                                         ║
║         │                                                  ║
║         ├──► Copper Loss:   {self.copper_loss_W:8.4f} W                  ║
║         ├──► Iron Loss:     {self.iron_loss_W:8.4f} W                  ║
║         ├──► Friction Loss: {self.friction_loss_W:8.4f} W                  ║
║         └──► Windage Loss:  {self.windage_loss_W:8.4f} W                  ║
║                                                            ║
║   EFFICIENCY: {efficiency:5.2f}%                                      ║
╚════════════════════════════════════════════════════════════╝
"""
