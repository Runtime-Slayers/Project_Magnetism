"""
Resonance Analysis and Vibration Control
==========================================
Critical for smooth, long-lasting generator operation.

This module analyzes:
- Mechanical resonance frequencies
- Torsional vibrations
- Electromagnetic forcing frequencies
- Critical speeds
- Damping requirements
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy.signal import find_peaks, welch
from scipy.linalg import eig
import warnings


@dataclass
class MechanicalSystem:
    """Mechanical parameters for resonance analysis"""
    # Rotor
    rotor_mass: float = 2.0           # kg
    rotor_radius: float = 0.05        # m
    rotor_length: float = 0.10        # m
    rotor_moment_of_inertia: float = None  # kg·m² (calculated if None)
    
    # Shaft
    shaft_radius: float = 0.01        # m
    shaft_length: float = 0.15        # m
    shaft_modulus: float = 200e9      # Pa (steel)
    
    # Bearings
    bearing_stiffness: float = 1e8    # N/m
    bearing_damping: float = 1e3      # N·s/m
    
    # Magnetic
    n_poles: int = 12
    n_slots: int = 18
    magnetic_stiffness: float = 1e5   # N/m (radial magnetic force gradient)
    
    def __post_init__(self):
        if self.rotor_moment_of_inertia is None:
            # Solid cylinder approximation
            self.rotor_moment_of_inertia = 0.5 * self.rotor_mass * self.rotor_radius**2


def calculate_natural_frequencies(system: MechanicalSystem) -> Dict:
    """
    Calculate natural frequencies of the rotor-bearing system.
    
    Models:
    1. Rigid rotor on flexible bearings
    2. Flexible rotor (bending modes)
    3. Torsional modes
    
    These are the frequencies TO AVOID during operation!
    """
    m = system.rotor_mass
    k = system.bearing_stiffness
    c = system.bearing_damping
    I = system.rotor_moment_of_inertia
    
    # -----------------------------------------------------------------
    # 1. RIGID ROTOR MODES (Bounce and Rock)
    # -----------------------------------------------------------------
    # Bounce mode: vertical translation
    omega_bounce = np.sqrt(2 * k / m)  # Two bearings
    f_bounce = omega_bounce / (2 * np.pi)
    
    # Rock mode: rotation about center
    L = system.shaft_length
    omega_rock = np.sqrt(k * L**2 / (2 * I))
    f_rock = omega_rock / (2 * np.pi)
    
    # -----------------------------------------------------------------
    # 2. FLEXIBLE ROTOR (Euler-Bernoulli beam)
    # -----------------------------------------------------------------
    E = system.shaft_modulus
    d = 2 * system.shaft_radius
    I_shaft = np.pi * d**4 / 64  # Second moment of area
    rho = 7850  # Steel density kg/m³
    A = np.pi * system.shaft_radius**2
    
    # First bending mode (simply supported approximation)
    lambda_1 = np.pi  # First mode shape factor
    omega_bend_1 = lambda_1**2 * np.sqrt(E * I_shaft / (rho * A * L**4))
    f_bend_1 = omega_bend_1 / (2 * np.pi)
    
    # Second bending mode
    lambda_2 = 2 * np.pi
    omega_bend_2 = lambda_2**2 * np.sqrt(E * I_shaft / (rho * A * L**4))
    f_bend_2 = omega_bend_2 / (2 * np.pi)
    
    # -----------------------------------------------------------------
    # 3. TORSIONAL MODES
    # -----------------------------------------------------------------
    G = E / (2 * (1 + 0.3))  # Shear modulus (Poisson's ratio ≈ 0.3)
    J = np.pi * d**4 / 32    # Polar moment of inertia
    I_rotor = system.rotor_moment_of_inertia
    
    omega_torsion_1 = np.sqrt(G * J / (L * I_rotor))
    f_torsion_1 = omega_torsion_1 / (2 * np.pi)
    
    # -----------------------------------------------------------------
    # 4. CRITICAL SPEEDS
    # -----------------------------------------------------------------
    # Critical speed = rotational speed where forcing = natural frequency
    critical_speeds_rpm = [
        f_bounce * 60,
        f_rock * 60,
        f_bend_1 * 60,
        f_torsion_1 * 60
    ]
    
    return {
        "natural_frequencies_Hz": {
            "bounce_mode": f_bounce,
            "rock_mode": f_rock,
            "first_bending": f_bend_1,
            "second_bending": f_bend_2,
            "first_torsional": f_torsion_1
        },
        "critical_speeds_rpm": {
            "bounce": critical_speeds_rpm[0],
            "rock": critical_speeds_rpm[1],
            "first_bending": critical_speeds_rpm[2],
            "first_torsional": critical_speeds_rpm[3]
        },
        "angular_frequencies_rad_s": {
            "bounce": omega_bounce,
            "rock": omega_rock,
            "first_bending": omega_bend_1,
            "first_torsional": omega_torsion_1
        }
    }


def calculate_forcing_frequencies(rpm: float, n_poles: int, 
                                 n_slots: int) -> Dict:
    """
    Calculate electromagnetic forcing frequencies.
    
    Sources of periodic forces:
    1. Rotor rotation (1× RPM)
    2. Cogging (slots × RPM)
    3. Ripple torque (electrical frequency harmonics)
    4. Slot harmonics
    """
    f_rotation = rpm / 60  # Hz
    
    # Cogging frequency
    from math import lcm
    N_cog = lcm(n_poles, n_slots)
    f_cogging = N_cog * f_rotation
    
    # Electrical frequency
    f_electrical = n_poles * f_rotation / 2
    
    # Slot passing frequency
    f_slot = n_slots * f_rotation
    
    return {
        "rotation_frequency_Hz": f_rotation,
        "cogging_frequency_Hz": f_cogging,
        "electrical_frequency_Hz": f_electrical,
        "slot_passing_frequency_Hz": f_slot,
        "harmonics": {
            "1x": f_rotation,
            "2x": 2 * f_rotation,
            f"cogging ({N_cog}x)": f_cogging,
            f"slots ({n_slots}x)": f_slot,
            "electrical": f_electrical,
            "2× electrical": 2 * f_electrical
        }
    }


def check_resonance_conditions(system: MechanicalSystem,
                               operating_rpm: float) -> Dict:
    """
    Check if operating speed coincides with any resonance.
    
    Returns warnings if operating near critical speeds.
    """
    natural = calculate_natural_frequencies(system)
    forcing = calculate_forcing_frequencies(operating_rpm, 
                                           system.n_poles, 
                                           system.n_slots)
    
    # Safety margin: should be ±20% away from resonance
    margin = 0.20
    
    warnings_list = []
    
    for mode_name, f_natural in natural["natural_frequencies_Hz"].items():
        for force_name, f_force in forcing["harmonics"].items():
            ratio = f_force / f_natural if f_natural > 0 else 0
            
            if 1 - margin < ratio < 1 + margin:
                severity = "CRITICAL" if abs(ratio - 1) < 0.05 else "WARNING"
                warnings_list.append({
                    "severity": severity,
                    "message": f"{force_name} forcing ({f_force:.1f} Hz) near {mode_name} ({f_natural:.1f} Hz)",
                    "ratio": ratio,
                    "recommended_action": "Change RPM or modify design"
                })
    
    # Check critical speeds
    for speed_name, critical_rpm in natural["critical_speeds_rpm"].items():
        speed_ratio = operating_rpm / critical_rpm if critical_rpm > 0 else 0
        
        if 0.7 < speed_ratio < 1.3:
            warnings_list.append({
                "severity": "CRITICAL",
                "message": f"Operating at {operating_rpm} RPM near {speed_name} critical speed ({critical_rpm:.0f} RPM)",
                "ratio": speed_ratio,
                "recommended_action": "Must pass through critical speed quickly or redesign"
            })
    
    return {
        "natural_frequencies": natural,
        "forcing_frequencies": forcing,
        "resonance_warnings": warnings_list,
        "safe_to_operate": len([w for w in warnings_list if w["severity"] == "CRITICAL"]) == 0
    }


def design_vibration_damping(system: MechanicalSystem,
                            target_damping_ratio: float = 0.1) -> Dict:
    """
    Design damping solutions for vibration control.
    
    Options:
    1. Bearing damping
    2. Squeeze film dampers
    3. Magnetic damping
    4. Friction damping
    """
    natural = calculate_natural_frequencies(system)
    m = system.rotor_mass
    
    solutions = {}
    
    for mode_name, omega in natural["angular_frequencies_rad_s"].items():
        if omega > 0:
            # Critical damping coefficient
            c_critical = 2 * m * omega
            
            # Required damping for target damping ratio
            c_required = target_damping_ratio * c_critical
            
            solutions[mode_name] = {
                "natural_frequency_Hz": omega / (2 * np.pi),
                "critical_damping_Ns_m": c_critical,
                "required_damping_Ns_m": c_required,
                "current_damping_Ns_m": system.bearing_damping,
                "damping_ratio_current": system.bearing_damping / c_critical,
                "needs_additional_damping": system.bearing_damping < c_required
            }
    
    # Damping solutions
    damping_options = [
        {
            "type": "Squeeze Film Damper",
            "description": "Oil-filled gap between bearing and housing",
            "damping_range_Ns_m": (1e3, 1e5),
            "pros": ["Effective for large amplitudes", "Adjustable"],
            "cons": ["Requires oil supply", "Temperature sensitive"]
        },
        {
            "type": "Eddy Current Damper",
            "description": "Conductor moving in magnetic field",
            "damping_range_Ns_m": (1e2, 1e4),
            "pros": ["No contact", "Maintenance free", "Already have magnets"],
            "cons": ["Generates heat", "Reduces efficiency"]
        },
        {
            "type": "Constrained Layer Damping",
            "description": "Viscoelastic layer sandwiched on structure",
            "damping_range_Ns_m": (1e2, 1e3),
            "pros": ["Simple", "Inexpensive"],
            "cons": ["Limited to certain frequency range"]
        },
        {
            "type": "Active Magnetic Bearing",
            "description": "Electromagnets with feedback control",
            "damping_range_Ns_m": (1e2, 1e6),
            "pros": ["Infinitely adjustable", "Can eliminate resonance"],
            "cons": ["Complex", "Expensive", "Requires power"]
        }
    ]
    
    return {
        "mode_analysis": solutions,
        "damping_options": damping_options,
        "recommendation": "Eddy current damping integrates well with PM generator design"
    }


def calculate_Campbell_diagram(system: MechanicalSystem,
                               rpm_range: Tuple[float, float] = (0, 6000),
                               n_points: int = 100) -> Dict:
    """
    Generate Campbell diagram data.
    
    Campbell diagram shows how natural frequencies change with speed
    and where they intersect with forcing frequencies (resonance points).
    
    Essential for avoiding resonance during operation!
    """
    natural = calculate_natural_frequencies(system)
    
    # RPM values
    rpm_values = np.linspace(rpm_range[0], rpm_range[1], n_points)
    
    # Natural frequencies (may vary with speed due to gyroscopic effects)
    # For now, assume constant
    nat_freq_lines = {
        name: np.ones(n_points) * freq 
        for name, freq in natural["natural_frequencies_Hz"].items()
    }
    
    # Forcing frequency lines (vary with speed)
    forcing_lines = {
        "1× rotation": rpm_values / 60,
        "2× rotation": 2 * rpm_values / 60,
        f"cogging ({np.lcm(system.n_poles, system.n_slots)}×)": 
            np.lcm(system.n_poles, system.n_slots) * rpm_values / 60,
        f"slot ({system.n_slots}×)": system.n_slots * rpm_values / 60,
        f"electrical ({system.n_poles//2}×)": system.n_poles//2 * rpm_values / 60
    }
    
    # Find intersection points (resonances)
    intersections = []
    for nat_name, nat_freq in natural["natural_frequencies_Hz"].items():
        for force_name, force_freq in forcing_lines.items():
            # Find where forcing line crosses natural frequency
            crossings = np.where(np.diff(np.sign(force_freq - nat_freq)))[0]
            for idx in crossings:
                rpm_crossing = rpm_values[idx]
                intersections.append({
                    "rpm": rpm_crossing,
                    "frequency_Hz": nat_freq,
                    "natural_mode": nat_name,
                    "forcing": force_name,
                    "severity": "HIGH" if nat_name in ["first_bending", "first_torsional"] else "MEDIUM"
                })
    
    return {
        "rpm_values": rpm_values,
        "natural_frequency_lines": nat_freq_lines,
        "forcing_frequency_lines": forcing_lines,
        "resonance_crossings": intersections,
        "safe_operating_ranges": find_safe_ranges(rpm_values, intersections)
    }


def find_safe_ranges(rpm_values: np.ndarray, 
                    intersections: List[Dict],
                    margin_rpm: float = 200) -> List[Tuple[float, float]]:
    """
    Find RPM ranges that are safely away from all resonances.
    """
    # Get all critical RPMs
    critical_rpms = sorted([i["rpm"] for i in intersections])
    
    if not critical_rpms:
        return [(rpm_values[0], rpm_values[-1])]
    
    safe_ranges = []
    current_start = rpm_values[0]
    
    for critical_rpm in critical_rpms:
        if critical_rpm - margin_rpm > current_start + margin_rpm:
            safe_ranges.append((current_start + margin_rpm, critical_rpm - margin_rpm))
        current_start = critical_rpm
    
    # Add final range
    if rpm_values[-1] - margin_rpm > current_start + margin_rpm:
        safe_ranges.append((current_start + margin_rpm, rpm_values[-1] - margin_rpm))
    
    return safe_ranges


def generate_resonance_report(system: MechanicalSystem,
                             operating_rpm: float) -> str:
    """
    Generate comprehensive resonance analysis report.
    """
    natural = calculate_natural_frequencies(system)
    forcing = calculate_forcing_frequencies(operating_rpm, system.n_poles, system.n_slots)
    resonance_check = check_resonance_conditions(system, operating_rpm)
    campbell = calculate_Campbell_diagram(system)
    damping = design_vibration_damping(system)
    
    report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    RESONANCE ANALYSIS REPORT                         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  OPERATING CONDITION: {operating_rpm:.0f} RPM ({operating_rpm/60:.1f} Hz)                           ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  NATURAL FREQUENCIES                                                 ║
╠══════════════════════════════════════════════════════════════════════╣
"""
    
    for mode, freq in natural["natural_frequencies_Hz"].items():
        report += f"║  • {mode:20s}: {freq:8.1f} Hz ({freq*60:.0f} CPM)           ║\n"
    
    report += """║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  FORCING FREQUENCIES @ {:.0f} RPM                                       ║
╠══════════════════════════════════════════════════════════════════════╣
""".format(operating_rpm)
    
    for name, freq in forcing["harmonics"].items():
        report += f"║  • {name:20s}: {freq:8.1f} Hz                              ║\n"
    
    report += """║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  RESONANCE WARNINGS                                                  ║
╠══════════════════════════════════════════════════════════════════════╣
"""
    
    if resonance_check["resonance_warnings"]:
        for warning in resonance_check["resonance_warnings"]:
            report += f"║  ⚠ [{warning['severity']:8s}] {warning['message'][:50]}\n"
    else:
        report += "║  ✓ No resonance conditions detected at this speed               ║\n"
    
    report += f"""║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  SAFE OPERATING RANGES                                               ║
╠══════════════════════════════════════════════════════════════════════╣
"""
    
    for i, (start, end) in enumerate(campbell["safe_operating_ranges"]):
        report += f"║  Range {i+1}: {start:.0f} - {end:.0f} RPM                                         ║\n"
    
    report += """║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  RECOMMENDATIONS                                                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  1. Operate within safe RPM ranges listed above                      ║
║  2. Add eddy current damping if passing through resonance            ║
║  3. Stiffen shaft to raise bending frequencies                       ║
║  4. Add flywheel mass to reduce torsional frequency                  ║
║  5. Use magnetic bearings for active vibration control               ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    return report
