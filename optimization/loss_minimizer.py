"""
Loss Minimization Module
=========================
Detailed analysis and minimization of all loss mechanisms.
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class LossBreakdown:
    """Detailed breakdown of all losses"""
    # Electrical losses
    copper_loss: float = 0.0        # I²R in windings
    eddy_current_loss: float = 0.0  # In conductors and magnets
    
    # Magnetic losses
    hysteresis_loss: float = 0.0    # Core hysteresis
    iron_loss: float = 0.0          # Total iron core loss
    magnet_loss: float = 0.0        # Eddy currents in magnets
    
    # Mechanical losses
    bearing_loss: float = 0.0       # Bearing friction
    windage_loss: float = 0.0       # Air friction
    seal_loss: float = 0.0          # Shaft seal friction
    
    # Other
    stray_loss: float = 0.0         # Miscellaneous
    
    @property
    def total_electrical(self) -> float:
        return self.copper_loss + self.eddy_current_loss
    
    @property
    def total_magnetic(self) -> float:
        return self.hysteresis_loss + self.iron_loss + self.magnet_loss
    
    @property
    def total_mechanical(self) -> float:
        return self.bearing_loss + self.windage_loss + self.seal_loss
    
    @property
    def total(self) -> float:
        return (self.total_electrical + self.total_magnetic + 
                self.total_mechanical + self.stray_loss)


def calculate_copper_losses(current_rms: float, 
                           resistance: float,
                           n_phases: int = 3,
                           temperature_C: float = 75) -> float:
    """
    Calculate copper (I²R) losses in windings.
    
    Includes temperature correction for resistance.
    """
    # Temperature coefficient for copper
    alpha = 0.00393  # per °C
    R_hot = resistance * (1 + alpha * (temperature_C - 20))
    
    # Total copper loss
    P_cu = n_phases * current_rms**2 * R_hot
    
    return P_cu


def calculate_iron_losses(B_peak: float, frequency: float,
                         core_volume: float,
                         material: str = "M19_silicon_steel") -> Dict[str, float]:
    """
    Calculate iron core losses using Steinmetz equation.
    
    P_iron = k_h × f × B^α + k_e × f² × B²
    
    where:
    - k_h = hysteresis coefficient
    - k_e = eddy current coefficient
    - α ≈ 1.6-2.0 (Steinmetz exponent)
    """
    # Material properties (approximate)
    materials = {
        "M19_silicon_steel": {
            "k_h": 0.02,    # W/kg/(Hz·T^α)
            "k_e": 0.0005,  # W/kg/(Hz²·T²)
            "alpha": 1.8,
            "density": 7650  # kg/m³
        },
        "amorphous": {
            "k_h": 0.005,
            "k_e": 0.0001,
            "alpha": 1.6,
            "density": 7200
        },
        "ferrite": {
            "k_h": 0.001,
            "k_e": 0.00001,
            "alpha": 2.0,
            "density": 4800
        }
    }
    
    props = materials.get(material, materials["M19_silicon_steel"])
    
    mass = core_volume * props["density"]
    
    # Hysteresis loss
    P_h = props["k_h"] * frequency * (B_peak ** props["alpha"]) * mass
    
    # Eddy current loss
    P_e = props["k_e"] * frequency**2 * B_peak**2 * mass
    
    return {
        "hysteresis_W": P_h,
        "eddy_current_W": P_e,
        "total_iron_W": P_h + P_e,
        "specific_loss_W_per_kg": (P_h + P_e) / mass if mass > 0 else 0
    }


def calculate_bearing_losses(rpm: float,
                            bearing_type: str,
                            radial_load: float,
                            axial_load: float = 0) -> float:
    """
    Calculate bearing friction losses.
    
    Uses SKF bearing loss model.
    P_bearing = M × ω
    
    where M = friction torque
    """
    omega = rpm * 2 * np.pi / 60
    
    # Friction coefficients by bearing type
    friction_coefs = {
        "ball_bearing": 0.0010,
        "roller_bearing": 0.0018,
        "ceramic_hybrid": 0.0008,
        "magnetic_bearing": 0.0001,  # Only control losses
        "sleeve_bearing": 0.002
    }
    
    mu = friction_coefs.get(bearing_type, 0.001)
    
    # Simplified friction torque
    # M = μ × (F_r × d/2)
    # Assume d = 40mm typical
    d = 0.040  # m
    
    M = mu * radial_load * d / 2
    
    # Power loss per bearing
    P = M * omega
    
    # Two bearings
    return 2 * P


def calculate_windage_losses(rpm: float,
                            rotor_radius: float,
                            rotor_length: float,
                            air_gap: float,
                            air_density: float = 1.2) -> float:
    """
    Calculate windage (air friction) losses.
    
    Uses couette flow model for air gap.
    """
    omega = rpm * 2 * np.pi / 60
    
    # Reynolds number
    nu = 1.5e-5  # Kinematic viscosity of air
    Re = omega * rotor_radius**2 / nu
    
    # Friction coefficient
    if Re < 3e5:
        Cf = 0.515 / np.sqrt(Re)  # Laminar
    else:
        Cf = 0.0325 / Re**0.2  # Turbulent
    
    # Power loss
    P = Cf * air_density * omega**3 * rotor_radius**4 * rotor_length
    
    return P


def calculate_magnet_losses(B_variation: float,
                           frequency: float,
                           magnet_volume: float,
                           magnet_conductivity: float = 1e6) -> float:
    """
    Calculate eddy current losses in permanent magnets.
    
    Important for high-speed operation!
    Can be reduced by segmenting magnets.
    """
    # Simplified eddy current loss
    # P = (π × τ × σ × f² × B² × V) / 6
    # where τ = magnet thickness
    
    # Assume magnet thickness from volume
    tau = (magnet_volume ** (1/3))
    
    P = (np.pi * tau * magnet_conductivity * frequency**2 * 
         B_variation**2 * magnet_volume) / 6
    
    return P


class LossMinimizer:
    """
    Optimize design to minimize losses.
    """
    
    def __init__(self, target_efficiency: float = 0.95):
        self.target_efficiency = target_efficiency
        
    def analyze_loss_breakdown(self, 
                              power_output: float,
                              rpm: float,
                              geometry: Dict) -> LossBreakdown:
        """
        Perform complete loss analysis.
        """
        omega = rpm * 2 * np.pi / 60
        frequency = geometry.get("n_poles", 12) * rpm / 120
        
        # Estimate current from power
        voltage = geometry.get("voltage_rms", 230)  # Assume 230V
        current = power_output / (3 * voltage * 0.9)  # 3-phase, 0.9 PF
        
        # Copper losses
        resistance = geometry.get("coil_resistance", 0.5)
        P_cu = calculate_copper_losses(current, resistance)
        
        # Iron losses
        core_volume = (np.pi * (geometry.get("stator_outer_radius", 0.08)**2 - 
                               geometry.get("stator_inner_radius", 0.051)**2) *
                      geometry.get("axial_length", 0.1))
        iron = calculate_iron_losses(geometry.get("B_airgap", 0.8), 
                                    frequency, core_volume)
        
        # Bearing losses
        rotor_mass = geometry.get("rotor_mass", 2.0)
        radial_load = rotor_mass * 9.81  # gravity
        P_bearing = calculate_bearing_losses(rpm, "ceramic_hybrid", radial_load)
        
        # Windage
        P_windage = calculate_windage_losses(
            rpm,
            geometry.get("rotor_radius", 0.05),
            geometry.get("axial_length", 0.1),
            geometry.get("air_gap", 0.001)
        )
        
        # Magnet losses
        P_magnet = calculate_magnet_losses(
            geometry.get("B_variation", 0.1),
            frequency,
            geometry.get("magnet_volume", 1e-5)
        )
        
        return LossBreakdown(
            copper_loss=P_cu,
            eddy_current_loss=P_magnet * 0.5,  # Some eddy in conductors
            hysteresis_loss=iron["hysteresis_W"],
            iron_loss=iron["total_iron_W"],
            magnet_loss=P_magnet,
            bearing_loss=P_bearing,
            windage_loss=P_windage,
            seal_loss=0.5,  # Small constant
            stray_loss=0.01 * power_output  # 1% stray
        )
    
    def suggest_improvements(self, losses: LossBreakdown) -> List[Dict]:
        """
        Suggest design improvements based on loss breakdown.
        """
        suggestions = []
        total = losses.total
        
        # Analyze each loss component
        if losses.copper_loss / total > 0.3:
            suggestions.append({
                "component": "Copper losses",
                "contribution": f"{100*losses.copper_loss/total:.1f}%",
                "solutions": [
                    "Increase wire diameter",
                    "Use Litz wire to reduce skin effect",
                    "Improve cooling for lower temperature",
                    "Use aluminum windings (weight reduction)"
                ],
                "priority": "HIGH"
            })
        
        if losses.iron_loss / total > 0.25:
            suggestions.append({
                "component": "Iron losses",
                "contribution": f"{100*losses.iron_loss/total:.1f}%",
                "solutions": [
                    "Use thinner laminations (0.2mm instead of 0.35mm)",
                    "Use higher grade silicon steel",
                    "Consider amorphous metal core",
                    "Reduce flux density in core"
                ],
                "priority": "HIGH"
            })
        
        if losses.bearing_loss / total > 0.1:
            suggestions.append({
                "component": "Bearing losses",
                "contribution": f"{100*losses.bearing_loss/total:.1f}%",
                "solutions": [
                    "Use ceramic hybrid bearings",
                    "Consider magnetic bearings",
                    "Improve lubrication",
                    "Reduce rotor mass"
                ],
                "priority": "MEDIUM"
            })
        
        if losses.windage_loss / total > 0.1:
            suggestions.append({
                "component": "Windage losses",
                "contribution": f"{100*losses.windage_loss/total:.1f}%",
                "solutions": [
                    "Smooth rotor surface",
                    "Reduce air gap if possible",
                    "Add shroud for better aerodynamics",
                    "Consider helium environment for high-speed"
                ],
                "priority": "MEDIUM"
            })
        
        if losses.magnet_loss / total > 0.15:
            suggestions.append({
                "component": "Magnet eddy current losses",
                "contribution": f"{100*losses.magnet_loss/total:.1f}%",
                "solutions": [
                    "Segment magnets axially",
                    "Use higher resistivity magnet grade",
                    "Reduce slot harmonics with skewing",
                    "Use distributed winding"
                ],
                "priority": "MEDIUM"
            })
        
        return suggestions
    
    def generate_loss_report(self, losses: LossBreakdown,
                            power_output: float) -> str:
        """
        Generate comprehensive loss analysis report.
        """
        total = losses.total
        efficiency = power_output / (power_output + total)
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    LOSS ANALYSIS REPORT                              ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Output Power: {power_output:8.1f} W                                         ║
║  Total Losses: {total:8.1f} W                                         ║
║  Efficiency:   {100*efficiency:8.1f} %                                         ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  LOSS BREAKDOWN                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ELECTRICAL LOSSES: {losses.total_electrical:8.2f} W ({100*losses.total_electrical/total:5.1f}%)                 ║
║    ├─ Copper (I²R):      {losses.copper_loss:8.2f} W                             ║
║    └─ Eddy current:      {losses.eddy_current_loss:8.2f} W                             ║
║                                                                      ║
║  MAGNETIC LOSSES: {losses.total_magnetic:8.2f} W ({100*losses.total_magnetic/total:5.1f}%)                   ║
║    ├─ Hysteresis:        {losses.hysteresis_loss:8.2f} W                             ║
║    ├─ Iron core:         {losses.iron_loss:8.2f} W                             ║
║    └─ Magnet eddy:       {losses.magnet_loss:8.2f} W                             ║
║                                                                      ║
║  MECHANICAL LOSSES: {losses.total_mechanical:8.2f} W ({100*losses.total_mechanical/total:5.1f}%)                 ║
║    ├─ Bearings:          {losses.bearing_loss:8.2f} W                             ║
║    ├─ Windage:           {losses.windage_loss:8.2f} W                             ║
║    └─ Seals:             {losses.seal_loss:8.2f} W                             ║
║                                                                      ║
║  STRAY LOSSES:     {losses.stray_loss:8.2f} W ({100*losses.stray_loss/total:5.1f}%)                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        
        # Add suggestions
        suggestions = self.suggest_improvements(losses)
        if suggestions:
            report += "\n╔══════════════════════════════════════════════════════════════════════╗\n"
            report += "║                    IMPROVEMENT SUGGESTIONS                           ║\n"
            report += "╠══════════════════════════════════════════════════════════════════════╣\n"
            
            for i, sug in enumerate(suggestions, 1):
                report += f"║  {i}. {sug['component']} [{sug['priority']}]                        \n"
                for sol in sug['solutions'][:2]:
                    report += f"║     • {sol[:50]}  \n"
            
            report += "╚══════════════════════════════════════════════════════════════════════╝\n"
        
        return report
