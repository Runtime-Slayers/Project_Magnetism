"""
ADVANCED THERMAL MANAGEMENT SYSTEM
===================================

Heat is the enemy of efficiency. Managing thermal loads allows:
1. Higher power density (more power from same size)
2. Longer component life
3. Stable performance
4. Higher efficiency (copper resistance increases with temp)

HEAT SOURCES IN A GENERATOR:
============================
1. Copper losses (I²R) - Increases with load
2. Iron/core losses - Increases with frequency
3. Magnet eddy currents - Increases with harmonics
4. Bearing friction - Constant (mostly)
5. Windage (air drag) - Increases with speed³

COOLING TECHNOLOGIES (ascending capability):
============================================
1. Natural convection: ~0.5 W/cm²
2. Forced air: ~2 W/cm²
3. Liquid jacket: ~10 W/cm²
4. Direct oil cooling: ~20 W/cm²
5. Spray cooling: ~100 W/cm²
6. Two-phase (boiling): ~200 W/cm²
7. Cryogenic (for superconductors): Special case

This module designs optimal thermal systems.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, List
from scipy.optimize import minimize
from enum import Enum


class CoolingType(Enum):
    """Cooling system types."""
    NATURAL_CONVECTION = "natural"
    FORCED_AIR = "forced_air"
    LIQUID_JACKET = "liquid_jacket"
    DIRECT_OIL = "direct_oil"
    SPRAY_COOLING = "spray"
    TWO_PHASE = "two_phase"
    CRYOGENIC = "cryogenic"


# =============================================================================
# THERMAL PROPERTIES
# =============================================================================

@dataclass  
class ThermalProperties:
    """Thermal properties of a material."""
    name: str
    thermal_conductivity_W_mK: float
    specific_heat_J_kgK: float
    density_kg_m3: float
    max_operating_temp_C: float


# Material database
THERMAL_MATERIALS = {
    "copper": ThermalProperties("Copper", 401, 385, 8960, 200),
    "aluminum": ThermalProperties("Aluminum 6061", 167, 896, 2700, 200),
    "steel_silicon": ThermalProperties("Silicon Steel", 25, 490, 7650, 180),
    "ndfeb_magnet": ThermalProperties("NdFeB N52", 9, 440, 7500, 80),
    "ndfeb_magnet_sh": ThermalProperties("NdFeB N48SH", 9, 440, 7500, 150),
    "epoxy": ThermalProperties("Epoxy Potting", 0.8, 1000, 1200, 150),
    "air": ThermalProperties("Air (25°C)", 0.026, 1006, 1.18, 500),
    "water": ThermalProperties("Water", 0.6, 4186, 997, 100),
    "oil_dielectric": ThermalProperties("Transformer Oil", 0.13, 2000, 870, 150),
    "thermal_paste": ThermalProperties("Thermal Paste", 5, 1000, 2500, 200),
}


# =============================================================================
# LOSS CALCULATION
# =============================================================================

@dataclass
class GeneratorLosses:
    """Calculator for generator losses (heat sources)."""
    
    # Geometry
    stator_outer_radius_mm: float = 80.0
    stator_inner_radius_mm: float = 55.0
    rotor_outer_radius_mm: float = 54.0
    active_length_mm: float = 100.0
    air_gap_mm: float = 1.0
    
    # Electrical parameters
    n_phases: int = 3
    phase_resistance_ohm: float = 0.5
    phase_inductance_mH: float = 1.0
    
    # Magnetic parameters
    n_poles: int = 12
    n_slots: int = 18
    core_loss_density_W_kg: float = 2.0  # At rated flux and frequency
    core_mass_kg: float = 2.0
    
    # Mechanical
    bearing_friction_W: float = 5.0
    
    def copper_loss(self, phase_current_A: float, 
                    temp_C: float = 80.0) -> float:
        """
        Calculate copper (I²R) losses.
        
        Note: Resistance increases with temperature!
        R(T) = R(20°C) * [1 + α * (T - 20)]
        α = 0.00393 /°C for copper
        """
        alpha = 0.00393
        R_hot = self.phase_resistance_ohm * (1 + alpha * (temp_C - 20))
        
        P_copper = self.n_phases * phase_current_A**2 * R_hot
        return P_copper
    
    def core_loss(self, frequency_Hz: float, 
                  flux_density_T: float = 1.5) -> float:
        """
        Calculate core (iron) losses.
        
        Using modified Steinmetz equation:
        P = k * f^1.4 * B^2.2 * mass
        """
        # Reference: 50 Hz, 1.5T
        f_ref, B_ref = 50, 1.5
        
        P_core = (self.core_loss_density_W_kg * self.core_mass_kg * 
                  (frequency_Hz / f_ref)**1.4 * (flux_density_T / B_ref)**2.2)
        return P_core
    
    def windage_loss(self, speed_rpm: float) -> float:
        """
        Calculate windage (air drag) losses.
        
        P_windage ∝ ρ * ω³ * r⁴ * L
        
        Significant at high speeds!
        """
        omega = speed_rpm * 2 * np.pi / 60
        r = self.rotor_outer_radius_mm / 1000  # m
        L = self.active_length_mm / 1000  # m
        rho_air = 1.18  # kg/m³
        
        # Empirical coefficient (depends on surface roughness)
        Cf = 0.003
        
        P_windage = Cf * rho_air * omega**3 * r**4 * L * np.pi
        return P_windage
    
    def total_loss(self, phase_current_A: float, speed_rpm: float,
                   temp_C: float = 80.0) -> Dict:
        """Calculate all losses."""
        # Electrical frequency
        pole_pairs = self.n_poles // 2
        freq = speed_rpm * pole_pairs / 60
        
        P_copper = self.copper_loss(phase_current_A, temp_C)
        P_core = self.core_loss(freq)
        P_windage = self.windage_loss(speed_rpm)
        P_bearing = self.bearing_friction_W
        
        P_total = P_copper + P_core + P_windage + P_bearing
        
        return {
            "copper_W": P_copper,
            "core_W": P_core,
            "windage_W": P_windage,
            "bearing_W": P_bearing,
            "total_W": P_total,
            "breakdown_percent": {
                "copper": P_copper / P_total * 100,
                "core": P_core / P_total * 100,
                "windage": P_windage / P_total * 100,
                "bearing": P_bearing / P_total * 100
            }
        }


# =============================================================================
# THERMAL RESISTANCE NETWORK
# =============================================================================

@dataclass
class ThermalNode:
    """A node in the thermal network."""
    name: str
    temperature_C: float = 25.0
    heat_generation_W: float = 0.0
    thermal_mass_J_K: float = 1000.0  # C = m * c_p
    
    # Connected nodes (thermal resistances in K/W)
    connections: Dict[str, float] = field(default_factory=dict)


class ThermalNetwork:
    """
    Thermal resistance network for generator.
    
    Models heat flow from sources (windings, core) to sinks (coolant, ambient).
    
    Solves: T_i = T_ambient + Σ(R_th * Q)
    
    Nodes:
    - Winding (copper)
    - Stator core (iron)
    - Stator housing (aluminum)
    - Rotor magnets
    - Rotor core
    - Shaft
    - Bearings
    - Coolant/ambient
    """
    
    def __init__(self, cooling_type: CoolingType = CoolingType.FORCED_AIR):
        """Initialize thermal network."""
        self.cooling_type = cooling_type
        self.nodes: Dict[str, ThermalNode] = {}
        self.ambient_temp_C = 25.0
        
        self._build_network()
    
    def _build_network(self):
        """Build the thermal resistance network."""
        # Create nodes
        self.nodes["winding"] = ThermalNode("Winding (Cu)", thermal_mass_J_K=500)
        self.nodes["stator_core"] = ThermalNode("Stator Core", thermal_mass_J_K=2000)
        self.nodes["housing"] = ThermalNode("Housing", thermal_mass_J_K=1000)
        self.nodes["rotor_magnets"] = ThermalNode("Magnets", thermal_mass_J_K=300)
        self.nodes["rotor_core"] = ThermalNode("Rotor Core", thermal_mass_J_K=800)
        self.nodes["air_gap"] = ThermalNode("Air Gap", thermal_mass_J_K=1)
        self.nodes["coolant"] = ThermalNode("Coolant", thermal_mass_J_K=float('inf'))
        
        # Define thermal resistances (K/W) based on cooling type
        if self.cooling_type == CoolingType.NATURAL_CONVECTION:
            R_housing_coolant = 2.0
            R_gap = 5.0
        elif self.cooling_type == CoolingType.FORCED_AIR:
            R_housing_coolant = 0.5
            R_gap = 3.0
        elif self.cooling_type == CoolingType.LIQUID_JACKET:
            R_housing_coolant = 0.1
            R_gap = 3.0
        elif self.cooling_type == CoolingType.DIRECT_OIL:
            R_housing_coolant = 0.05
            R_gap = 0.5  # Oil fills gap
        else:
            R_housing_coolant = 0.1
            R_gap = 3.0
        
        # Winding to stator core (through slot liner)
        self.nodes["winding"].connections["stator_core"] = 0.3
        
        # Stator core to housing (press fit)
        self.nodes["stator_core"].connections["housing"] = 0.1
        
        # Housing to coolant
        self.nodes["housing"].connections["coolant"] = R_housing_coolant
        
        # Air gap thermal resistances
        self.nodes["stator_core"].connections["air_gap"] = R_gap / 2
        self.nodes["air_gap"].connections["rotor_magnets"] = R_gap / 2
        
        # Rotor internal
        self.nodes["rotor_magnets"].connections["rotor_core"] = 0.5
        
        # Rotor to coolant (through shaft and bearings)
        self.nodes["rotor_core"].connections["coolant"] = 1.0
    
    def solve_steady_state(self, losses: Dict[str, float]) -> Dict[str, float]:
        """
        Solve for steady-state temperatures.
        
        Parameters:
            losses: Dict mapping node names to heat generation (W)
            
        Returns:
            Dict mapping node names to temperature (°C)
        """
        # Set heat generation
        for name, Q in losses.items():
            if name in self.nodes:
                self.nodes[name].heat_generation_W = Q
        
        # Set coolant temperature (boundary condition)
        self.nodes["coolant"].temperature_C = self.ambient_temp_C
        
        # Simple iterative solver (Gauss-Seidel)
        for _ in range(100):
            for name, node in self.nodes.items():
                if name == "coolant":
                    continue  # Fixed boundary
                
                # Sum heat flows from/to connected nodes
                Q_net = node.heat_generation_W
                sum_G = 0  # Sum of conductances
                sum_GT = 0  # Sum of G * T
                
                for connected_name, R_th in node.connections.items():
                    if connected_name in self.nodes:
                        T_connected = self.nodes[connected_name].temperature_C
                        G = 1 / R_th  # Thermal conductance
                        sum_G += G
                        sum_GT += G * T_connected
                
                # Update temperature
                if sum_G > 0:
                    node.temperature_C = (Q_net + sum_GT) / sum_G
        
        return {name: node.temperature_C for name, node in self.nodes.items()}
    
    def get_max_allowable_loss(self, max_winding_temp_C: float = 155.0) -> float:
        """
        Calculate maximum allowable loss for given temperature limit.
        
        Class F insulation: 155°C max
        Class H insulation: 180°C max
        
        Parameters:
            max_winding_temp_C: Max allowed winding temperature
            
        Returns:
            Maximum total winding loss (W)
        """
        # Use binary search
        Q_min, Q_max = 0, 5000
        
        for _ in range(20):
            Q_test = (Q_min + Q_max) / 2
            temps = self.solve_steady_state({"winding": Q_test})
            
            if temps["winding"] > max_winding_temp_C:
                Q_max = Q_test
            else:
                Q_min = Q_test
        
        return Q_min


# =============================================================================
# COOLING SYSTEM DESIGN
# =============================================================================

@dataclass
class LiquidCoolingJacket:
    """
    Liquid cooling jacket design.
    
    A channel around the stator for coolant flow.
    Much more effective than air cooling.
    """
    
    # Geometry
    stator_od_mm: float = 160.0  # Stator outer diameter
    jacket_thickness_mm: float = 10.0
    channel_width_mm: float = 8.0
    channel_depth_mm: float = 8.0
    n_channels: int = 1  # Spiral or parallel
    
    # Coolant properties (water-glycol 50/50)
    coolant_density_kg_m3: float = 1050.0
    coolant_cp_J_kgK: float = 3400.0
    coolant_viscosity_Pa_s: float = 0.003
    coolant_k_W_mK: float = 0.4
    
    # Operating conditions
    flow_rate_lpm: float = 5.0  # Liters per minute
    inlet_temp_C: float = 25.0
    
    def calculate_thermal_resistance(self, active_length_mm: float) -> float:
        """
        Calculate jacket-to-stator thermal resistance (K/W).
        
        Includes:
        - Convection from stator to coolant
        - Jacket wall conduction (small)
        """
        # Convert to SI
        L = active_length_mm / 1000
        D_h = 2 * self.channel_width_mm * self.channel_depth_mm / \
              (self.channel_width_mm + self.channel_depth_mm) / 1000  # Hydraulic diameter
        A_channel = self.channel_width_mm * self.channel_depth_mm * 1e-6  # m²
        
        # Flow velocity
        Q_m3s = self.flow_rate_lpm / 60 / 1000
        v = Q_m3s / (A_channel * self.n_channels)
        
        # Reynolds number
        rho = self.coolant_density_kg_m3
        mu = self.coolant_viscosity_Pa_s
        Re = rho * v * D_h / mu
        
        # Prandtl number
        Pr = mu * self.coolant_cp_J_kgK / self.coolant_k_W_mK
        
        # Nusselt number (Dittus-Boelter for turbulent flow)
        if Re > 2300:
            Nu = 0.023 * Re**0.8 * Pr**0.4
        else:
            Nu = 3.66  # Laminar
        
        # Heat transfer coefficient
        h = Nu * self.coolant_k_W_mK / D_h
        
        # Convection area (stator OD × length)
        A_conv = np.pi * self.stator_od_mm / 1000 * L
        
        # Thermal resistance
        R_conv = 1 / (h * A_conv)
        
        return R_conv
    
    def calculate_pressure_drop(self, active_length_mm: float) -> float:
        """Calculate pressure drop through jacket (Pa)."""
        L = active_length_mm / 1000 * 2  # Approximate channel length
        D_h = 2 * self.channel_width_mm * self.channel_depth_mm / \
              (self.channel_width_mm + self.channel_depth_mm) / 1000
        A_channel = self.channel_width_mm * self.channel_depth_mm * 1e-6
        
        Q_m3s = self.flow_rate_lpm / 60 / 1000
        v = Q_m3s / (A_channel * self.n_channels)
        
        rho = self.coolant_density_kg_m3
        mu = self.coolant_viscosity_Pa_s
        Re = rho * v * D_h / mu
        
        # Friction factor
        if Re > 2300:
            f = 0.316 / Re**0.25  # Blasius
        else:
            f = 64 / Re
        
        # Pressure drop
        dP = f * L / D_h * rho * v**2 / 2
        
        return dP
    
    def calculate_heat_capacity(self) -> float:
        """Calculate heat removal capacity (W) for 10°C rise."""
        Q_m3s = self.flow_rate_lpm / 60 / 1000
        m_dot = Q_m3s * self.coolant_density_kg_m3  # kg/s
        delta_T = 10  # °C temperature rise
        
        Q_capacity = m_dot * self.coolant_cp_J_kgK * delta_T
        return Q_capacity
    
    def get_specifications(self) -> Dict:
        """Get cooling jacket specifications."""
        return {
            "type": "Liquid Cooling Jacket",
            "coolant": "Water-Glycol 50/50",
            "flow_rate_lpm": self.flow_rate_lpm,
            "inlet_temp_C": self.inlet_temp_C,
            "thermal_resistance_K_W": self.calculate_thermal_resistance(100),
            "pressure_drop_kPa": self.calculate_pressure_drop(100) / 1000,
            "heat_capacity_W": self.calculate_heat_capacity(),
            "pump_power_estimate_W": self.flow_rate_lpm * 2,  # Rough estimate
        }


@dataclass
class DirectOilCooling:
    """
    Direct oil cooling system.
    
    The stator is submersed in cooling oil, which directly contacts
    the windings. Much better heat transfer than jacket cooling.
    
    Used in high-performance motors (Tesla, etc.)
    """
    
    oil_type: str = "PAO Synthetic"
    oil_density_kg_m3: float = 850.0
    oil_cp_J_kgK: float = 2000.0
    oil_k_W_mK: float = 0.13
    oil_viscosity_Pa_s: float = 0.02
    
    flow_rate_lpm: float = 10.0
    inlet_temp_C: float = 40.0
    
    def calculate_heat_capacity(self) -> float:
        """Heat capacity for 20°C rise."""
        Q_m3s = self.flow_rate_lpm / 60 / 1000
        m_dot = Q_m3s * self.oil_density_kg_m3
        delta_T = 20
        return m_dot * self.oil_cp_J_kgK * delta_T
    
    def get_specifications(self) -> Dict:
        """Get specifications."""
        return {
            "type": "Direct Oil Cooling",
            "oil": self.oil_type,
            "flow_rate_lpm": self.flow_rate_lpm,
            "heat_capacity_W": self.calculate_heat_capacity(),
            "advantages": [
                "Direct contact with windings",
                "Very low thermal resistance",
                "Also provides insulation",
                "Lubricates bearings"
            ],
            "disadvantages": [
                "Higher viscosity = more pumping power",
                "Oil degradation over time",
                "Potential leakage issues",
                "Added weight"
            ]
        }


# =============================================================================
# THERMAL SIMULATION
# =============================================================================

class ThermalSimulator:
    """
    Transient thermal simulator for generator.
    
    Simulates temperature rise during startup and varying load conditions.
    """
    
    def __init__(self, losses: GeneratorLosses,
                 cooling: CoolingType = CoolingType.LIQUID_JACKET):
        """Initialize simulator."""
        self.losses = losses
        self.network = ThermalNetwork(cooling)
    
    def simulate_startup(self, current_A: float, speed_rpm: float,
                        duration_s: float = 600) -> Dict:
        """
        Simulate thermal startup transient.
        
        Parameters:
            current_A: Operating current
            speed_rpm: Operating speed
            duration_s: Simulation duration (default 10 minutes)
            
        Returns:
            Time series of temperatures
        """
        dt = 1.0  # 1 second time step
        n_steps = int(duration_s / dt)
        
        time = np.zeros(n_steps)
        temps = {name: np.zeros(n_steps) for name in self.network.nodes}
        
        # Initial temperatures
        for name in self.network.nodes:
            temps[name][0] = self.network.ambient_temp_C
        
        # Get loss breakdown
        loss_data = self.losses.total_loss(current_A, speed_rpm)
        
        for i in range(1, n_steps):
            time[i] = i * dt
            
            # Update heat generation based on temperature-dependent resistance
            current_winding_temp = temps["winding"][i-1]
            loss_data = self.losses.total_loss(current_A, speed_rpm, current_winding_temp)
            
            # Apply heat to nodes
            heat_inputs = {
                "winding": loss_data["copper_W"],
                "stator_core": loss_data["core_W"] * 0.7,  # 70% in stator
                "rotor_core": loss_data["core_W"] * 0.3,   # 30% in rotor
            }
            
            # Simple forward Euler for each node
            for name, node in self.network.nodes.items():
                if name == "coolant":
                    temps[name][i] = self.network.ambient_temp_C
                    continue
                
                # Heat input
                Q_in = heat_inputs.get(name, 0)
                
                # Heat transfer to/from connected nodes
                Q_transfer = 0
                for connected, R_th in node.connections.items():
                    if connected in self.network.nodes:
                        T_other = temps[connected][i-1]
                        T_self = temps[name][i-1]
                        Q_transfer += (T_other - T_self) / R_th
                
                # Temperature change
                dT = (Q_in + Q_transfer) / node.thermal_mass_J_K * dt
                temps[name][i] = temps[name][i-1] + dT
        
        # Find thermal time constant (time to reach 63.2% of final)
        T_final = temps["winding"][-1]
        T_initial = temps["winding"][0]
        T_63pct = T_initial + 0.632 * (T_final - T_initial)
        
        idx_63 = np.argmax(temps["winding"] >= T_63pct)
        tau = time[idx_63] if idx_63 > 0 else float('inf')
        
        return {
            "time_s": time,
            "temperatures": temps,
            "final_temperatures": {name: temps[name][-1] for name in temps},
            "thermal_time_constant_s": tau,
            "steady_state_reached": temps["winding"][-1] - temps["winding"][-10] < 0.1
        }
    
    def find_max_continuous_current(self, speed_rpm: float,
                                     max_winding_temp_C: float = 155.0) -> float:
        """
        Find maximum continuous current for given winding temperature limit.
        
        Parameters:
            speed_rpm: Operating speed
            max_winding_temp_C: Maximum allowed winding temperature
            
        Returns:
            Maximum continuous current (A)
        """
        # Binary search
        I_min, I_max = 0, 100
        
        for _ in range(15):
            I_test = (I_min + I_max) / 2
            
            result = self.simulate_startup(I_test, speed_rpm, duration_s=1800)
            T_final = result["final_temperatures"]["winding"]
            
            if T_final > max_winding_temp_C:
                I_max = I_test
            else:
                I_min = I_test
        
        return I_min


# =============================================================================
# DESIGN OPTIMIZATION
# =============================================================================

def optimize_cooling_system(power_W: float, speed_rpm: float,
                           max_temp_C: float = 155.0) -> Dict:
    """
    Optimize cooling system for given power requirement.
    
    Parameters:
        power_W: Required power output
        speed_rpm: Operating speed
        max_temp_C: Maximum winding temperature
        
    Returns:
        Optimal cooling design
    """
    print(f"\nDesigning cooling for {power_W}W @ {speed_rpm} RPM")
    print("-" * 50)
    
    results = {}
    
    for cooling in [CoolingType.NATURAL_CONVECTION, CoolingType.FORCED_AIR,
                    CoolingType.LIQUID_JACKET, CoolingType.DIRECT_OIL]:
        
        losses = GeneratorLosses()
        sim = ThermalSimulator(losses, cooling)
        
        # Find max current
        I_max = sim.find_max_continuous_current(speed_rpm, max_temp_C)
        
        # Estimate power at this current (rough: P ≈ 0.8 * V * I for efficiency)
        P_estimate = I_max * 50 * 0.8  # Assuming 50V terminal
        
        results[cooling.value] = {
            "max_current_A": I_max,
            "estimated_power_W": P_estimate,
            "meets_requirement": P_estimate >= power_W
        }
        
        print(f"{cooling.value:<20}: I_max = {I_max:.1f}A, P ≈ {P_estimate:.0f}W")
    
    # Recommend smallest adequate system
    for cooling in [CoolingType.NATURAL_CONVECTION, CoolingType.FORCED_AIR,
                    CoolingType.LIQUID_JACKET, CoolingType.DIRECT_OIL]:
        if results[cooling.value]["meets_requirement"]:
            print(f"\n✅ RECOMMENDED: {cooling.value}")
            return {
                "recommended_cooling": cooling.value,
                "all_results": results
            }
    
    print("\n⚠️ WARNING: Even direct oil cooling may not suffice!")
    print("   Consider: Larger generator or superconducting design")
    return {"recommended_cooling": "INSUFFICIENT", "all_results": results}


# =============================================================================
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("THERMAL MANAGEMENT SYSTEM ANALYSIS")
    print("="*70)
    
    # Loss analysis
    print("\n1. LOSS BREAKDOWN")
    print("-"*50)
    losses = GeneratorLosses()
    
    for current in [5, 10, 20]:
        for rpm in [1000, 2000, 3000]:
            loss = losses.total_loss(current, rpm)
            print(f"I={current}A, {rpm}RPM: "
                  f"Cu={loss['copper_W']:.1f}W, "
                  f"Fe={loss['core_W']:.1f}W, "
                  f"Wind={loss['windage_W']:.1f}W, "
                  f"Total={loss['total_W']:.1f}W")
    
    # Cooling comparison
    print("\n2. COOLING TECHNOLOGY COMPARISON")
    print("-"*50)
    
    for cooling in CoolingType:
        if cooling == CoolingType.CRYOGENIC:
            continue  # Skip cryogenic (special case)
        
        network = ThermalNetwork(cooling)
        temps = network.solve_steady_state({"winding": 100})  # 100W loss
        print(f"{cooling.value:<20}: Winding = {temps['winding']:.1f}°C "
              f"(for 100W loss)")
    
    # Startup simulation
    print("\n3. THERMAL STARTUP SIMULATION")
    print("-"*50)
    
    sim = ThermalSimulator(GeneratorLosses(), CoolingType.LIQUID_JACKET)
    result = sim.simulate_startup(15, 2000, duration_s=600)
    
    print(f"Operating: 15A @ 2000 RPM")
    print(f"Thermal time constant: {result['thermal_time_constant_s']:.0f} seconds")
    print(f"Final temperatures (10 min):")
    for name, temp in result['final_temperatures'].items():
        print(f"  {name}: {temp:.1f}°C")
    
    # Design optimization
    print("\n4. COOLING SYSTEM DESIGN")
    optimize_cooling_system(power_W=1000, speed_rpm=2000)
    
    # Liquid cooling jacket specs
    print("\n5. LIQUID COOLING JACKET SPECIFICATIONS")
    print("-"*50)
    jacket = LiquidCoolingJacket(flow_rate_lpm=8)
    specs = jacket.get_specifications()
    for key, value in specs.items():
        print(f"  {key}: {value}")
