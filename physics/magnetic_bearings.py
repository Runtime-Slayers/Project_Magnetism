"""
MAGNETIC BEARING DESIGN MODULE
==============================

Magnetic bearings eliminate mechanical contact, reducing friction to effectively ZERO.
This is the key technology for ultra-high efficiency generators.

TYPES IMPLEMENTED:
1. Passive Magnetic Bearings (PMB) - Using permanent magnets only
2. Active Magnetic Bearings (AMB) - Electromagnets with feedback control
3. Hybrid Bearings - Combination of passive and active

PHYSICS:
- Earnshaw's Theorem: Cannot have stable equilibrium with static magnets alone
- Solution: Use diamagnetics, superconductors, or active control
- Our approach: Passive radial + Active axial (or vice versa)

ADVANTAGES:
- Zero friction (no mechanical contact)
- No lubrication required
- Very high speed capability (>100,000 RPM)
- Long lifetime (no wear)
- No contamination

CHALLENGES:
- Earnshaw's theorem requires workarounds
- Active systems need power and control
- Higher upfront cost

References:
- Schweitzer, G. "Magnetic Bearings: Theory, Design, and Application"
- NASA/TM-2002-211159 "Magnetic Bearing Technology"
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional, Callable, List
from scipy.integrate import odeint
from scipy.optimize import minimize
import warnings


# Physical constants
MU_0 = 4 * np.pi * 1e-7  # Vacuum permeability (H/m)


# =============================================================================
# PASSIVE MAGNETIC BEARING (PMB)
# =============================================================================

@dataclass
class PassiveMagneticBearing:
    """
    Passive Magnetic Bearing using permanent magnets.
    
    Configuration: Radial repulsion bearing with axial stabilization
    
    The rotor has ring magnets, the stator has ring magnets.
    They repel each other, centering the rotor.
    
    Passive bearings can be stable in ONE direction only (Earnshaw).
    We use passive for RADIAL and active for AXIAL.
    """
    
    # Geometry (mm)
    rotor_magnet_inner_radius: float = 20.0
    rotor_magnet_outer_radius: float = 30.0
    rotor_magnet_height: float = 10.0
    
    stator_magnet_inner_radius: float = 32.0  # Slightly larger
    stator_magnet_outer_radius: float = 45.0
    stator_magnet_height: float = 15.0
    
    air_gap: float = 2.0  # mm - radial gap between magnets
    
    # Material
    magnet_Br: float = 1.4  # Tesla (remanence) - N52 NdFeB
    
    # Number of axial rings (stacking increases stiffness)
    n_rings: int = 2
    
    def __post_init__(self):
        """Validate and calculate derived properties."""
        # Convert to meters for calculations
        self.r1_rotor = self.rotor_magnet_inner_radius / 1000
        self.r2_rotor = self.rotor_magnet_outer_radius / 1000
        self.h_rotor = self.rotor_magnet_height / 1000
        
        self.r1_stator = self.stator_magnet_inner_radius / 1000
        self.r2_stator = self.stator_magnet_outer_radius / 1000
        self.h_stator = self.stator_magnet_height / 1000
        
        self.gap = self.air_gap / 1000
    
    def calculate_radial_stiffness(self) -> float:
        """
        Calculate radial stiffness (N/m).
        
        Higher stiffness = better centering, but harder to start.
        
        Approximate formula for ring magnets in repulsion:
        k_r ≈ (π * Br² * A_eff) / (μ₀ * g²)
        
        Where A_eff is effective pole area.
        
        Returns:
            Radial stiffness in N/m
        """
        # Effective area (geometric mean of rotor/stator)
        A_rotor = np.pi * (self.r2_rotor**2 - self.r1_rotor**2)
        A_stator = np.pi * (self.r2_stator**2 - self.r1_stator**2)
        A_eff = np.sqrt(A_rotor * A_stator)
        
        # Radial stiffness (simplified model)
        k_r = (np.pi * self.magnet_Br**2 * A_eff) / (MU_0 * self.gap**2)
        
        # Multiply by number of rings
        k_r *= self.n_rings
        
        return k_r
    
    def calculate_axial_stiffness(self) -> float:
        """
        Calculate axial stiffness (N/m).
        
        For a radial repulsion bearing, axial stiffness is NEGATIVE!
        This is Earnshaw's theorem - you can't have stability in all directions.
        
        We need active control or mechanical contact for axial support.
        
        Returns:
            Axial stiffness in N/m (negative = unstable)
        """
        # The axial stiffness is approximately -0.5 * radial stiffness
        # for typical ring magnet geometry
        k_a = -0.5 * self.calculate_radial_stiffness()
        
        return k_a
    
    def calculate_load_capacity(self) -> float:
        """
        Calculate maximum radial load before contact (N).
        
        Returns:
            Maximum load in Newtons
        """
        k_r = self.calculate_radial_stiffness()
        max_displacement = self.gap * 0.8  # Leave 20% margin
        
        return k_r * max_displacement
    
    def calculate_critical_speed(self, rotor_mass_kg: float) -> float:
        """
        Calculate first critical speed (resonance).
        
        The rotor will vibrate excessively at this speed - AVOID IT.
        
        Parameters:
            rotor_mass_kg: Mass of the rotor
            
        Returns:
            Critical speed in RPM
        """
        k_r = self.calculate_radial_stiffness()
        
        # Natural frequency
        omega_n = np.sqrt(k_r / rotor_mass_kg)
        
        # Convert to RPM
        rpm_critical = omega_n * 60 / (2 * np.pi)
        
        return rpm_critical
    
    def get_specifications(self) -> dict:
        """Get complete bearing specifications."""
        rotor_mass_estimate = 2.0  # kg, typical
        
        return {
            "type": "Passive Magnetic Bearing (Radial Repulsion)",
            "radial_stiffness_N_m": self.calculate_radial_stiffness(),
            "axial_stiffness_N_m": self.calculate_axial_stiffness(),
            "max_radial_load_N": self.calculate_load_capacity(),
            "critical_speed_rpm": self.calculate_critical_speed(rotor_mass_estimate),
            "friction_coefficient": 0,  # No contact!
            "power_loss_W": 0,  # No power consumption
            "notes": [
                "Axial stiffness is NEGATIVE - needs active axial control",
                "Avoid operation near critical speed",
                "No lubrication required",
                "Infinite lifetime (no wear)"
            ]
        }


# =============================================================================
# ACTIVE MAGNETIC BEARING (AMB)
# =============================================================================

@dataclass
class ActiveMagneticBearing:
    """
    Active Magnetic Bearing with feedback control.
    
    Uses electromagnets with position sensors and a feedback controller
    to actively maintain rotor position.
    
    This can achieve stable levitation in ALL directions (bypasses Earnshaw).
    
    Control Loop:
    1. Sensor measures rotor position
    2. Controller calculates required force
    3. Power amplifier drives electromagnet current
    4. Electromagnet applies force to rotor
    5. Repeat at high frequency (5-20 kHz)
    """
    
    # Geometry
    pole_count: int = 8  # 4 pairs (X+, X-, Y+, Y-)
    pole_face_area_mm2: float = 400.0  # Area per pole
    air_gap_mm: float = 1.0  # Nominal air gap
    coil_turns: int = 100  # Turns per pole
    
    # Electromagnet core
    saturation_flux_T: float = 1.8  # Silicon steel
    
    # Controller parameters
    stiffness_N_m: float = 1e6  # Desired closed-loop stiffness
    damping_ratio: float = 0.7  # Critical damping
    bandwidth_Hz: float = 1000  # Control bandwidth
    
    # Bias current (for linearization)
    bias_current_A: float = 2.0
    
    def __post_init__(self):
        """Calculate derived parameters."""
        self.A_pole = self.pole_face_area_mm2 * 1e-6  # m²
        self.g0 = self.air_gap_mm / 1000  # m
        self.N = self.coil_turns
        
    def calculate_force_constant(self) -> float:
        """
        Calculate force constant Ki (N/A).
        
        For a single electromagnet:
        F = (μ₀ * N² * A * i²) / (4 * g²)
        
        Linearized around bias current i₀:
        F ≈ Ki * Δi
        
        where Ki = (μ₀ * N² * A * i₀) / (2 * g₀²)
        """
        Ki = (MU_0 * self.N**2 * self.A_pole * self.bias_current_A) / (2 * self.g0**2)
        return Ki
    
    def calculate_position_constant(self) -> float:
        """
        Calculate negative stiffness Kx (N/m).
        
        This is the inherent instability of electromagnetic attraction.
        The controller must overcome this.
        
        Kx = -μ₀ * N² * A * i₀² / (2 * g₀³)
        """
        Kx = -(MU_0 * self.N**2 * self.A_pole * self.bias_current_A**2) / (2 * self.g0**3)
        return Kx
    
    def calculate_max_force(self) -> float:
        """
        Calculate maximum force per axis (N).
        
        Limited by magnetic saturation.
        F_max = B_sat² * A / (2 * μ₀)
        """
        F_max = (self.saturation_flux_T**2 * self.A_pole) / (2 * MU_0)
        # Per axis (two opposing poles)
        return F_max * 2
    
    def calculate_controller_gains(self, rotor_mass_kg: float) -> dict:
        """
        Calculate PID controller gains for stable levitation.
        
        For a second-order system:
        m * ẍ = Kx * x + Ki * i
        
        With PD controller: i = Kp * x + Kd * ẋ
        
        Closed-loop: m * ẍ = (Kx + Ki*Kp) * x + Ki*Kd * ẋ
        
        For desired stiffness k and damping ratio ζ:
        Kp = (k - Kx) / Ki
        Kd = 2 * ζ * sqrt(m * (k - Kx)) / Ki
        
        Parameters:
            rotor_mass_kg: Rotor mass
            
        Returns:
            Dictionary with controller gains
        """
        Ki = self.calculate_force_constant()
        Kx = self.calculate_position_constant()
        k = self.stiffness_N_m
        m = rotor_mass_kg
        zeta = self.damping_ratio
        
        # Check stability
        if k <= abs(Kx):
            warnings.warn(f"Desired stiffness {k} must exceed open-loop {abs(Kx):.0f} N/m")
            k = abs(Kx) * 2
        
        # PD gains
        Kp = (k + Kx) / Ki  # Note: Kx is negative
        Kd = 2 * zeta * np.sqrt(m * k) / Ki
        
        # Integral gain for steady-state accuracy
        omega_i = 2 * np.pi * 10  # 10 Hz integral crossover
        Kint = omega_i * Kp / 10
        
        # Natural frequency
        omega_n = np.sqrt(k / m)
        
        return {
            "Kp_A_m": Kp,
            "Kd_A_s_m": Kd,
            "Ki_A_m_s": Kint,
            "natural_frequency_Hz": omega_n / (2 * np.pi),
            "closed_loop_stiffness_N_m": k,
            "damping_ratio": zeta,
            "force_constant_N_A": Ki,
            "position_constant_N_m": Kx,
        }
    
    def calculate_power_consumption(self, rotor_mass_kg: float) -> dict:
        """
        Calculate steady-state and dynamic power consumption.
        
        Parameters:
            rotor_mass_kg: Rotor mass
            
        Returns:
            Power consumption breakdown
        """
        # Bias power (always consumed)
        R_coil = 2.0  # Assume 2 ohms per coil
        P_bias = self.pole_count * self.bias_current_A**2 * R_coil
        
        # Gravity compensation (if vertical)
        F_gravity = rotor_mass_kg * 9.81
        Ki = self.calculate_force_constant()
        i_gravity = F_gravity / Ki
        P_gravity = (self.pole_count // 2) * i_gravity**2 * R_coil
        
        # Dynamic power (depends on vibration, estimate 10% of max)
        P_dynamic = 0.1 * P_bias
        
        return {
            "bias_power_W": P_bias,
            "gravity_compensation_W": P_gravity,
            "dynamic_estimate_W": P_dynamic,
            "total_steady_state_W": P_bias + P_gravity + P_dynamic,
            "notes": "Actual dynamic power depends on disturbances"
        }
    
    def simulate_step_response(self, rotor_mass_kg: float,
                               step_force_N: float = 10.0,
                               duration_s: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate closed-loop step response.
        
        Parameters:
            rotor_mass_kg: Rotor mass
            step_force_N: Step disturbance force
            duration_s: Simulation duration
            
        Returns:
            (time, position) arrays
        """
        gains = self.calculate_controller_gains(rotor_mass_kg)
        Ki = gains["force_constant_N_A"]
        Kx = gains["position_constant_N_m"]
        Kp = gains["Kp_A_m"]
        Kd = gains["Kd_A_s_m"]
        Kint = gains["Ki_A_m_s"]
        m = rotor_mass_kg
        
        def dynamics(state, t):
            x, v, x_int = state
            
            # Controller
            i_control = Kp * x + Kd * v + Kint * x_int
            
            # Clamp current
            i_max = 10.0  # A
            i_control = np.clip(i_control, -i_max, i_max)
            
            # Force
            F_mag = Ki * i_control + Kx * x
            F_ext = step_force_N if t > 0.01 else 0  # Step at 10ms
            
            # Acceleration
            a = (F_mag + F_ext) / m
            
            return [v, a, x]
        
        t = np.linspace(0, duration_s, 1000)
        x0 = [0, 0, 0]  # Initial state
        
        solution = odeint(dynamics, x0, t)
        
        return t, solution[:, 0] * 1e6  # Return in micrometers
    
    def get_specifications(self) -> dict:
        """Get complete bearing specifications."""
        rotor_mass = 2.0  # kg, typical
        
        return {
            "type": "Active Magnetic Bearing (8-pole)",
            "max_force_per_axis_N": self.calculate_max_force(),
            "closed_loop_stiffness_N_m": self.stiffness_N_m,
            "damping_ratio": self.damping_ratio,
            "control_bandwidth_Hz": self.bandwidth_Hz,
            "friction_coefficient": 0,
            "power_consumption_W": self.calculate_power_consumption(rotor_mass)["total_steady_state_W"],
            "controller_gains": self.calculate_controller_gains(rotor_mass),
            "notes": [
                "Requires position sensors (eddy current or capacitive)",
                "Needs digital controller (DSP or FPGA)",
                "Power amplifiers required for each axis",
                "Backup bearings recommended for safety"
            ]
        }


# =============================================================================
# HYBRID MAGNETIC BEARING SYSTEM
# =============================================================================

@dataclass
class HybridMagneticBearingSystem:
    """
    Complete bearing system using passive radial + active axial.
    
    This is the most practical zero-contact bearing solution:
    - Passive PM bearings handle radial loads (no power needed)
    - Active EM bearing handles axial thrust (lower power than full active)
    - Touch-down bearings for safety during power loss
    """
    
    # Passive radial bearings (one at each end)
    radial_bearing: PassiveMagneticBearing = field(
        default_factory=PassiveMagneticBearing
    )
    
    # Active axial bearing
    axial_bearing: ActiveMagneticBearing = field(
        default_factory=lambda: ActiveMagneticBearing(
            pole_count=4,  # Only 4 poles for axial
            pole_face_area_mm2=1000.0,  # Larger for thrust
            air_gap_mm=0.8,
            stiffness_N_m=5e5,
        )
    )
    
    # Backup/touch-down bearings
    touchdown_gap_mm: float = 0.5  # Gap when levitated
    touchdown_type: str = "ceramic ball bearing"
    
    # System parameters
    rotor_mass_kg: float = 2.0
    max_axial_thrust_N: float = 50.0
    
    def get_system_specifications(self) -> dict:
        """Get complete bearing system specifications."""
        radial_spec = self.radial_bearing.get_specifications()
        axial_spec = self.axial_bearing.get_specifications()
        
        # Total loss is just the axial bearing power (passive uses none)
        total_power = self.axial_bearing.calculate_power_consumption(
            self.rotor_mass_kg
        )["total_steady_state_W"]
        
        return {
            "configuration": "Hybrid (Passive Radial + Active Axial)",
            "radial_system": {
                "type": "Passive PM Repulsion",
                "stiffness_N_m": radial_spec["radial_stiffness_N_m"],
                "max_load_N": radial_spec["max_radial_load_N"],
                "power_W": 0,  # No power for passive
            },
            "axial_system": {
                "type": "Active Electromagnetic",
                "stiffness_N_m": axial_spec["closed_loop_stiffness_N_m"],
                "max_thrust_N": self.max_axial_thrust_N,
                "power_W": total_power,
            },
            "touchdown_bearings": {
                "type": self.touchdown_type,
                "gap_mm": self.touchdown_gap_mm,
                "purpose": "Safety during power loss or overload"
            },
            "total_friction_coefficient": 0,
            "total_power_consumption_W": total_power,
            "critical_speed_rpm": self.radial_bearing.calculate_critical_speed(
                self.rotor_mass_kg
            ),
            "advantages": [
                "Zero friction = ultra-high efficiency",
                "No lubricant = clean operation",
                "High speed capability",
                "Very long lifetime (no wear)"
            ],
            "limitations": [
                "Higher initial cost",
                "Requires control electronics",
                "Needs auxiliary power for active bearing",
                "Lower load capacity than roller bearings"
            ]
        }


# =============================================================================
# SUPERCONDUCTING MAGNETIC BEARING
# =============================================================================

@dataclass
class SuperconductingBearing:
    """
    Superconducting Magnetic Bearing (SMB).
    
    Uses High-Temperature Superconductors (HTS) to achieve:
    - PERFECT diamagnetic levitation
    - Stable in ALL directions (beats Earnshaw's theorem!)
    - Essentially ZERO loss (just cooling power)
    
    Physics:
    - Superconductors expel magnetic fields (Meissner effect)
    - Flux pinning provides stability
    - No control system needed!
    
    Challenges:
    - Requires cryogenic cooling (liquid nitrogen, 77K)
    - Lower load capacity than active bearings
    - Still experimental for large machines
    """
    
    # HTS material
    superconductor_type: str = "YBCO bulk"
    critical_temperature_K: float = 93.0
    operating_temperature_K: float = 77.0  # Liquid nitrogen
    
    # Geometry
    superconductor_diameter_mm: float = 60.0
    superconductor_thickness_mm: float = 15.0
    permanent_magnet_diameter_mm: float = 50.0
    permanent_magnet_height_mm: float = 20.0
    
    # Levitation gap
    levitation_gap_mm: float = 5.0
    
    def calculate_levitation_force(self) -> float:
        """
        Estimate levitation force (N).
        
        For YBCO + NdFeB system:
        F ≈ 1-2 N/cm² of facing area
        
        This is lower than conventional bearings but friction-free.
        """
        # Effective area (smaller of HTS or PM)
        r_hts = self.superconductor_diameter_mm / 2 / 10  # cm
        r_pm = self.permanent_magnet_diameter_mm / 2 / 10  # cm
        
        A_eff = np.pi * min(r_hts, r_pm)**2  # cm²
        
        # Pressure (depends on gap, temperature, field)
        pressure_N_cm2 = 1.5  # Typical for well-designed SMB
        
        return A_eff * pressure_N_cm2
    
    def calculate_cooling_power(self) -> float:
        """
        Estimate cryocooler power requirement (W).
        
        A small Stirling or pulse-tube cooler for 77K operation.
        Heat load from:
        - Conduction through supports
        - Radiation
        - Leads and sensors
        """
        # Typical small cryocooler: 10-50W electrical for 1-5W cooling at 77K
        # Coefficient of Performance ≈ 0.05-0.1 at 77K
        
        heat_load_W = 2.0  # Estimate for small bearing
        cop = 0.07
        
        electrical_power = heat_load_W / cop
        
        return electrical_power
    
    def calculate_stiffness(self) -> dict:
        """
        Calculate flux-pinning stiffness.
        
        SMBs have good stiffness in all directions due to flux pinning.
        """
        # Approximate stiffness (N/m)
        # Typical: 10⁴ - 10⁵ N/m depending on size
        
        A_mm2 = np.pi * (self.permanent_magnet_diameter_mm / 2)**2
        
        # Empirical: ~1000 N/m per cm² of area
        k_radial = A_mm2 / 100 * 1000  # N/m
        k_axial = k_radial * 0.5  # Usually lower axially
        
        return {
            "radial_stiffness_N_m": k_radial,
            "axial_stiffness_N_m": k_axial,
            "note": "Both positive - stable in all directions!"
        }
    
    def get_specifications(self) -> dict:
        """Get complete superconducting bearing specifications."""
        stiffness = self.calculate_stiffness()
        
        return {
            "type": f"Superconducting Magnetic Bearing ({self.superconductor_type})",
            "operating_temperature_K": self.operating_temperature_K,
            "cooling_method": "Liquid nitrogen or cryocooler",
            "levitation_force_N": self.calculate_levitation_force(),
            "radial_stiffness_N_m": stiffness["radial_stiffness_N_m"],
            "axial_stiffness_N_m": stiffness["axial_stiffness_N_m"],
            "friction_coefficient": 0,
            "electrical_power_W": self.calculate_cooling_power(),
            "advantages": [
                "Zero friction",
                "Stable without control system",
                "No electronics needed for levitation",
                "Extremely high speed capability",
                "Self-centering (flux pinning)"
            ],
            "limitations": [
                "Requires cryogenic cooling",
                "Lower load capacity",
                "Complex thermal design",
                "Higher initial cost",
                "Cool-down time before operation"
            ],
            "applications": [
                "Flywheels for energy storage",
                "High-speed generators",
                "Research equipment",
                "Future transportation"
            ]
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def compare_bearing_technologies(rotor_mass_kg: float = 2.0,
                                 target_speed_rpm: float = 10000) -> None:
    """
    Compare all bearing technologies for a given application.
    
    Parameters:
        rotor_mass_kg: Rotor mass
        target_speed_rpm: Target operating speed
    """
    print("\n" + "="*80)
    print("BEARING TECHNOLOGY COMPARISON")
    print(f"Rotor mass: {rotor_mass_kg} kg, Target speed: {target_speed_rpm} RPM")
    print("="*80)
    
    # Calculate rotor weight
    weight_N = rotor_mass_kg * 9.81
    
    bearings = [
        ("Passive Magnetic (PM)", PassiveMagneticBearing()),
        ("Active Magnetic (AMB)", ActiveMagneticBearing()),
        ("Hybrid (PM+AMB)", HybridMagneticBearingSystem(rotor_mass_kg=rotor_mass_kg)),
        ("Superconducting (HTS)", SuperconductingBearing()),
    ]
    
    print(f"\n{'Technology':<25} {'Friction':<12} {'Power (W)':<12} {'Max Load (N)':<15} {'Notes':<30}")
    print("-"*95)
    
    for name, bearing in bearings:
        if hasattr(bearing, 'get_system_specifications'):
            specs = bearing.get_system_specifications()
            friction = specs.get('total_friction_coefficient', 0)
            power = specs.get('total_power_consumption_W', 0)
            max_load = specs['radial_system']['max_load_N'] if 'radial_system' in specs else 'N/A'
        else:
            specs = bearing.get_specifications()
            friction = specs.get('friction_coefficient', 0)
            power = specs.get('power_consumption_W', specs.get('electrical_power_W', 0))
            max_load = specs.get('max_radial_load_N', specs.get('levitation_force_N', 'N/A'))
        
        notes = specs.get('notes', specs.get('limitations', []))
        note_str = notes[0] if notes else ""
        
        print(f"{name:<25} {friction:<12.6f} {power:<12.1f} {str(max_load):<15} {note_str[:30]:<30}")
    
    print("\n" + "-"*95)
    print("RECOMMENDATION:")
    if target_speed_rpm > 50000:
        print("  → Superconducting bearing for ultra-high speed")
    elif target_speed_rpm > 20000:
        print("  → Active magnetic bearing for high speed and precision")
    elif weight_N > 100:
        print("  → Hybrid system (passive radial + active axial) for best efficiency")
    else:
        print("  → Hybrid system for zero-friction, moderate power consumption")


def design_magnetic_bearing_for_generator(rotor_mass_kg: float,
                                          rotor_od_mm: float,
                                          max_speed_rpm: float,
                                          axial_thrust_N: float = 50.0) -> HybridMagneticBearingSystem:
    """
    Auto-design a hybrid magnetic bearing system for a generator.
    
    Parameters:
        rotor_mass_kg: Mass of rotor
        rotor_od_mm: Outer diameter of rotor (for sizing)
        max_speed_rpm: Maximum operating speed
        axial_thrust_N: Expected axial load
        
    Returns:
        Configured HybridMagneticBearingSystem
    """
    # Size passive radial bearings based on rotor
    # Magnets should be roughly 30-50% of rotor diameter
    rotor_magnet_od = rotor_od_mm * 0.35
    rotor_magnet_id = rotor_od_mm * 0.20
    
    radial = PassiveMagneticBearing(
        rotor_magnet_inner_radius=rotor_magnet_id,
        rotor_magnet_outer_radius=rotor_magnet_od,
        rotor_magnet_height=15.0,
        stator_magnet_inner_radius=rotor_magnet_od + 4.0,
        stator_magnet_outer_radius=rotor_magnet_od + 20.0,
        stator_magnet_height=20.0,
        air_gap=2.0,
        n_rings=2
    )
    
    # Check critical speed
    critical = radial.calculate_critical_speed(rotor_mass_kg)
    if max_speed_rpm > critical * 0.7:
        # Need stiffer bearing - add more rings
        radial.n_rings = 4
    
    # Size active axial bearing for thrust load
    force_margin = 2.0  # Safety factor
    required_force = axial_thrust_N * force_margin + rotor_mass_kg * 9.81
    
    # Calculate required pole area
    B_sat = 1.5  # Conservative
    A_required = 2 * MU_0 * required_force / B_sat**2
    
    axial = ActiveMagneticBearing(
        pole_count=4,
        pole_face_area_mm2=max(500, A_required * 1e6),
        air_gap_mm=0.8,
        stiffness_N_m=5e5,
    )
    
    return HybridMagneticBearingSystem(
        radial_bearing=radial,
        axial_bearing=axial,
        rotor_mass_kg=rotor_mass_kg,
        max_axial_thrust_N=axial_thrust_N
    )


if __name__ == "__main__":
    print("MAGNETIC BEARING DESIGN MODULE")
    print("="*50)
    
    # Compare technologies
    compare_bearing_technologies(rotor_mass_kg=2.0, target_speed_rpm=15000)
    
    # Design example
    print("\n\nDESIGNING BEARING FOR 2KG ROTOR, 100MM OD, 15000 RPM:")
    print("-"*50)
    system = design_magnetic_bearing_for_generator(
        rotor_mass_kg=2.0,
        rotor_od_mm=100,
        max_speed_rpm=15000,
        axial_thrust_N=30
    )
    
    specs = system.get_system_specifications()
    print(f"\nConfiguration: {specs['configuration']}")
    print(f"Total power consumption: {specs['total_power_consumption_W']:.1f} W")
    print(f"Critical speed: {specs['critical_speed_rpm']:.0f} RPM")
    
    print("\nAdvantages:")
    for adv in specs['advantages']:
        print(f"  ✓ {adv}")
