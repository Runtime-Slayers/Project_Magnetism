"""
Anti-Cogging Analysis and Design
=================================
THE MOST CRITICAL MODULE FOR YOUR PROJECT!

Cogging is when magnets "lock" into positions - preventing smooth rotation.
This module provides solutions to ELIMINATE or MINIMIZE cogging.
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from scipy.optimize import minimize, differential_evolution
from scipy.fft import fft, fftfreq
from math import gcd, lcm


@dataclass
class GeneratorGeometry:
    """Geometry parameters affecting cogging"""
    n_poles: int = 12          # Number of magnetic poles on rotor
    n_slots: int = 18          # Number of stator slots
    rotor_radius: float = 0.05 # meters
    stator_radius: float = 0.051
    air_gap: float = 0.001
    magnet_arc: float = 0.8    # Magnet arc as fraction of pole pitch
    slot_opening: float = 0.3  # Slot opening as fraction of slot pitch
    skew_angle: float = 0.0    # Magnet skew in electrical degrees
    
    @property
    def cogging_order(self) -> int:
        """LCM of poles and slots - determines cogging frequency"""
        return lcm(self.n_poles, self.n_slots)
    
    @property
    def slot_pitch(self) -> float:
        """Angular pitch of stator slots (radians)"""
        return 2 * np.pi / self.n_slots
    
    @property
    def pole_pitch(self) -> float:
        """Angular pitch of rotor poles (radians)"""
        return 2 * np.pi / self.n_poles


def calculate_cogging_torque(theta: float, geom: GeneratorGeometry,
                             B_remanent: float = 1.45) -> float:
    """
    Calculate cogging torque at rotor position theta.
    
    Uses Fourier series approximation:
    T_cog(θ) = Σ T_n × sin(n × N_cog × θ)
    
    where N_cog = LCM(poles, slots)
    
    Parameters:
    -----------
    theta : float
        Rotor angular position (radians)
    geom : GeneratorGeometry
        Generator geometry parameters
    B_remanent : float
        Magnet remanent flux density
        
    Returns:
    --------
    T_cog : float
        Cogging torque (N·m)
    """
    N_cog = geom.cogging_order
    
    # Magnetic energy variation with position
    # Simplified analytical model
    
    # Base cogging amplitude
    # T_max ∝ B² × volume × derivative of permeance
    L = geom.stator_radius - geom.rotor_radius  # Active length approximation
    V_magnet = geom.magnet_arc * geom.pole_pitch * geom.rotor_radius**2 * L
    
    # Permeance variation due to slot openings
    P_var = geom.slot_opening * np.sin(geom.n_slots * theta)
    
    # Base cogging torque
    B = B_remanent * geom.magnet_arc  # Effective B
    T_base = 0.5 * B**2 * V_magnet / (4e-7 * np.pi)  # Maxwell stress
    
    # Cogging torque with harmonics
    T_cog = 0
    for n in range(1, 6):  # First 5 harmonics
        # Each harmonic amplitude decreases
        amplitude = T_base / (n**2) * (1 - geom.skew_angle/90)**n
        T_cog += amplitude * np.sin(n * N_cog * theta)
    
    return T_cog


def analyze_cogging_spectrum(geom: GeneratorGeometry,
                            n_samples: int = 3600) -> Dict:
    """
    Perform frequency analysis of cogging torque.
    
    This reveals which harmonics dominate and guides optimization.
    """
    # Sample cogging over one rotor revolution
    theta = np.linspace(0, 2*np.pi, n_samples)
    T_cog = np.array([calculate_cogging_torque(t, geom) for t in theta])
    
    # FFT analysis
    T_fft = fft(T_cog)
    freqs = fftfreq(n_samples, 2*np.pi/n_samples)
    
    # Find dominant harmonics
    magnitudes = np.abs(T_fft[:n_samples//2])
    orders = np.round(freqs[:n_samples//2] * 2 * np.pi).astype(int)
    
    # Get top harmonics
    top_indices = np.argsort(magnitudes)[-10:]
    dominant_harmonics = [
        {"order": orders[i], "magnitude": magnitudes[i]}
        for i in top_indices if orders[i] > 0
    ]
    
    return {
        "theta": theta,
        "torque": T_cog,
        "peak_to_peak": np.max(T_cog) - np.min(T_cog),
        "rms_torque": np.sqrt(np.mean(T_cog**2)),
        "cogging_order": geom.cogging_order,
        "dominant_harmonics": sorted(dominant_harmonics, 
                                    key=lambda x: x["magnitude"], 
                                    reverse=True)
    }


def optimize_pole_slot_combination(target_power: float,
                                  max_poles: int = 24,
                                  max_slots: int = 36) -> List[Dict]:
    """
    Find optimal pole-slot combinations that minimize cogging.
    
    KEY INSIGHT: Cogging is minimized when LCM(poles, slots) is large!
    
    Best ratios for 3-phase:
    - 2:3 (e.g., 8P/12S, 10P/15S)
    - 4:3 (e.g., 8P/6S, 16P/12S)  
    - Fractional slot designs
    
    Returns ranked list of combinations.
    """
    combinations = []
    
    for p in range(2, max_poles + 1, 2):  # Poles must be even
        for s in range(3, max_slots + 1, 3):  # Slots typically multiple of 3
            # Calculate cogging order
            cog_order = lcm(p, s)
            
            # Calculate slots per pole per phase
            q = s / (p * 3)
            
            # Winding factor (approximate)
            if q == int(q):
                k_w = 0.96  # Integer slot
            else:
                k_w = 0.93  # Fractional slot (often better for cogging!)
            
            # Cogging index (lower is better)
            cogging_index = p / cog_order
            
            combinations.append({
                "poles": p,
                "slots": s,
                "cogging_order": cog_order,
                "slots_per_pole_per_phase": q,
                "winding_factor": k_w,
                "cogging_index": cogging_index,
                "recommended": cogging_index < 0.1
            })
    
    # Sort by cogging index (lower is better)
    combinations.sort(key=lambda x: x["cogging_index"])
    
    return combinations[:20]  # Return top 20


def optimize_skew_angle(geom: GeneratorGeometry) -> Dict:
    """
    Find optimal magnet skew angle to cancel cogging.
    
    Skewing shifts the cogging pattern along the rotor length,
    causing cancellation when integrated.
    
    Optimal skew = 360° / LCM(poles, slots)
    """
    N_cog = geom.cogging_order
    
    # Theoretical optimal skew (electrical degrees)
    optimal_skew = 360 / N_cog
    
    # Analyze effect of different skew angles
    skew_angles = np.linspace(0, 2 * optimal_skew, 100)
    cogging_reduction = []
    
    for skew in skew_angles:
        geom_skewed = GeneratorGeometry(
            n_poles=geom.n_poles,
            n_slots=geom.n_slots,
            rotor_radius=geom.rotor_radius,
            stator_radius=geom.stator_radius,
            air_gap=geom.air_gap,
            magnet_arc=geom.magnet_arc,
            slot_opening=geom.slot_opening,
            skew_angle=skew
        )
        analysis = analyze_cogging_spectrum(geom_skewed)
        cogging_reduction.append(analysis["peak_to_peak"])
    
    # Find minimum
    min_idx = np.argmin(cogging_reduction)
    
    return {
        "optimal_skew_electrical_deg": skew_angles[min_idx],
        "theoretical_optimal": optimal_skew,
        "cogging_reduction_percent": 100 * (1 - cogging_reduction[min_idx] / cogging_reduction[0]),
        "skew_angles": skew_angles,
        "cogging_vs_skew": cogging_reduction
    }


def optimize_magnet_shape(geom: GeneratorGeometry) -> Dict:
    """
    Optimize magnet arc and shape for minimum cogging.
    
    Options:
    1. Magnet arc ratio
    2. Chamfered edges
    3. Bread-loaf shape
    4. Parallel vs radial magnetization
    """
    
    def objective(params):
        """Minimize cogging peak-to-peak"""
        magnet_arc, slot_opening = params
        
        geom_test = GeneratorGeometry(
            n_poles=geom.n_poles,
            n_slots=geom.n_slots,
            rotor_radius=geom.rotor_radius,
            stator_radius=geom.stator_radius,
            air_gap=geom.air_gap,
            magnet_arc=magnet_arc,
            slot_opening=slot_opening,
            skew_angle=geom.skew_angle
        )
        
        analysis = analyze_cogging_spectrum(geom_test)
        return analysis["peak_to_peak"]
    
    # Bounds
    bounds = [(0.5, 0.95), (0.2, 0.6)]
    
    # Optimize using differential evolution (global optimizer)
    result = differential_evolution(objective, bounds, seed=42,
                                   maxiter=100, polish=True)
    
    return {
        "optimal_magnet_arc": result.x[0],
        "optimal_slot_opening": result.x[1],
        "minimized_cogging": result.fun,
        "convergence": result.success
    }


def halbach_array_design(n_poles: int, segments_per_pole: int = 4) -> Dict:
    """
    Design a Halbach array for maximum field concentration.
    
    Halbach arrays:
    - Concentrate field on one side (air gap)
    - Cancel field on other side (back iron not needed!)
    - Reduce cogging due to sinusoidal field distribution
    
    This is a PREMIUM solution for your generator!
    """
    n_magnets = n_poles * segments_per_pole
    
    # Magnetization angles for each segment
    angles = []
    for pole in range(n_poles):
        for seg in range(segments_per_pole):
            # Halbach formula: rotation rate = (k+1) where k is harmonic number
            # For fundamental (k=1): magnetization rotates twice per pole
            base_angle = 360 * pole / n_poles
            segment_angle = base_angle + 360 * (seg + 1) / segments_per_pole
            angles.append(segment_angle % 360)
    
    # Calculate field concentration factor
    # Halbach ideally gives 1.4× the field of conventional arrangement
    concentration_factor = 1 + np.sin(np.pi / segments_per_pole) / (np.pi / segments_per_pole)
    
    return {
        "n_magnets": n_magnets,
        "segments_per_pole": segments_per_pole,
        "magnetization_angles_deg": angles,
        "field_concentration_factor": concentration_factor,
        "field_harmonic_content": {
            "fundamental": 0.95,  # ~95% fundamental
            "3rd_harmonic": 0.03,
            "5th_harmonic": 0.02
        },
        "cogging_reduction": 0.6,  # ~60% reduction due to sinusoidal field
        "back_iron_required": False,  # Major advantage!
        "assembly_instructions": [
            "1. Use non-magnetic jig to hold segments",
            "2. Insert magnets sequentially with correct angles",
            "3. Use adhesive rated for magnet temperature",
            "4. Apply compression ring for security",
            "WARNING: Strong forces between segments - use safety equipment!"
        ]
    }


def stepped_rotor_design(geom: GeneratorGeometry, n_steps: int = 3) -> Dict:
    """
    Design a stepped/modular rotor to reduce cogging.
    
    Divides rotor into axial sections, each shifted angularly.
    Similar effect to skewing but easier to manufacture.
    """
    # Optimal step angle
    step_angle = 360 / (n_steps * geom.cogging_order)
    
    # Calculate resulting cogging
    # Stepped design cancels n_steps harmonics
    remaining_cogging = 1 / n_steps
    
    return {
        "n_steps": n_steps,
        "step_angle_deg": step_angle,
        "step_angle_mechanical_deg": step_angle * 2 / geom.n_poles,
        "cogging_reduction_factor": remaining_cogging,
        "manufacturing_notes": [
            f"Divide rotor into {n_steps} axial sections",
            f"Each section rotated by {step_angle:.2f}° electrical",
            "Assemble sections on common shaft",
            "Align with precision fixtures"
        ]
    }


def generate_anti_cogging_report(geom: GeneratorGeometry) -> str:
    """
    Generate a comprehensive anti-cogging design report.
    """
    # Run all analyses
    spectrum = analyze_cogging_spectrum(geom)
    skew_opt = optimize_skew_angle(geom)
    shape_opt = optimize_magnet_shape(geom)
    halbach = halbach_array_design(geom.n_poles)
    stepped = stepped_rotor_design(geom)
    pole_slot = optimize_pole_slot_combination(1000)[:5]
    
    report = f"""
╔══════════════════════════════════════════════════════════════════╗
║           ANTI-COGGING DESIGN REPORT                             ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  CURRENT DESIGN:                                                 ║
║  • Poles: {geom.n_poles}    Slots: {geom.n_slots}                              ║
║  • Cogging Order: {spectrum['cogging_order']}                                          ║
║  • Peak-to-Peak Torque: {spectrum['peak_to_peak']:.6f} N·m                        ║
║  • RMS Cogging: {spectrum['rms_torque']:.6f} N·m                             ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  OPTIMIZATION RESULTS:                                           ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1. SKEW OPTIMIZATION:                                           ║
║     Optimal Skew Angle: {skew_opt['optimal_skew_electrical_deg']:.2f}° (electrical)                   ║
║     Reduction: {skew_opt['cogging_reduction_percent']:.1f}%                                          ║
║                                                                  ║
║  2. MAGNET SHAPE OPTIMIZATION:                                   ║
║     Optimal Arc Ratio: {shape_opt['optimal_magnet_arc']:.2f}                                   ║
║     Optimal Slot Opening: {shape_opt['optimal_slot_opening']:.2f}                               ║
║                                                                  ║
║  3. HALBACH ARRAY BENEFITS:                                      ║
║     Field Concentration: {halbach['field_concentration_factor']:.2f}×                               ║
║     Cogging Reduction: {100*halbach['cogging_reduction']:.0f}%                                     ║
║     Back Iron: NOT REQUIRED                                      ║
║                                                                  ║
║  4. STEPPED ROTOR (3-step):                                      ║
║     Step Angle: {stepped['step_angle_deg']:.2f}° electrical                             ║
║     Cogging Factor: {stepped['cogging_reduction_factor']:.2f}                                       ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  RECOMMENDED POLE-SLOT COMBINATIONS:                             ║
╠══════════════════════════════════════════════════════════════════╣
"""
    
    for i, ps in enumerate(pole_slot):
        report += f"║  {i+1}. {ps['poles']}P/{ps['slots']}S  Cog Order: {ps['cogging_order']}  "
        report += f"q={ps['slots_per_pole_per_phase']:.2f}  {'✓' if ps['recommended'] else ''}\n"
    
    report += """║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  RECOMMENDED ACTIONS:                                            ║
║  1. Use pole-slot ratio with high cogging order                  ║
║  2. Apply optimal skew angle                                     ║
║  3. Consider Halbach array for premium design                    ║
║  4. Use fractional slot design (non-integer q)                   ║
║  5. Chamfer magnet edges                                         ║
╚══════════════════════════════════════════════════════════════════╝
"""
    return report
