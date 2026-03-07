"""
Coulomb Force and Magnetic Force Calculations
===============================================
This module handles:
- Electrostatic forces (for charge analysis)
- Magnetic forces between magnets
- Torque calculations
- The KEY force asymmetries you asked about!
"""

import numpy as np
from typing import Tuple, List
from dataclasses import dataclass
from .constants import MU_0, EPSILON_0, E_CHARGE


# =============================================================================
# ELECTROSTATIC FORCES (Your original question!)
# =============================================================================

def coulomb_force(q1: float, q2: float, r: float) -> float:
    """
    Calculate Coulomb force between two point charges.
    
    F = k * |q1 * q2| / r²
    
    where k = 1/(4πε₀) = 8.99 × 10⁹ N·m²/C²
    
    Parameters:
    -----------
    q1, q2 : float
        Charges in Coulombs
    r : float
        Distance between charges in meters
        
    Returns:
    --------
    F : float
        Force magnitude in Newtons
        Positive = repulsive, Negative = attractive
    """
    k = 1 / (4 * np.pi * EPSILON_0)  # 8.99e9 N·m²/C²
    F = k * q1 * q2 / (r ** 2)
    return F  # Sign indicates direction


def coulomb_force_with_quantum_correction(q1: float, q2: float, r: float,
                                          particle_type_1: str = "electron",
                                          particle_type_2: str = "electron") -> dict:
    """
    Coulomb force WITH quantum corrections as you requested!
    
    This includes:
    - Magnetic moment interaction (spin-spin)
    - Vacuum polarization (QED correction)
    
    Parameters:
    -----------
    q1, q2 : float
        Charges in Coulombs (use E_CHARGE for elementary charge)
    r : float
        Distance in meters
    particle_type_1, particle_type_2 : str
        "electron" or "proton"
        
    Returns:
    --------
    dict with force breakdown
    """
    # Classical Coulomb force
    k = 1 / (4 * np.pi * EPSILON_0)
    F_coulomb = k * q1 * q2 / (r ** 2)
    
    # Magnetic moment values
    MU_ELECTRON = 9.284764e-24  # J/T (Bohr magneton × g-factor)
    MU_PROTON = 1.410607e-26    # J/T (nuclear magneton × g-factor)
    
    # Select magnetic moments based on particle types
    mu1 = MU_ELECTRON if particle_type_1 == "electron" else MU_PROTON
    mu2 = MU_ELECTRON if particle_type_2 == "electron" else MU_PROTON
    
    # Spin-spin magnetic interaction (dipole-dipole)
    # F_mag ≈ (3μ₀/4π) * (μ₁μ₂/r⁴) for parallel aligned spins
    F_magnetic = (3 * MU_0 / (4 * np.pi)) * (mu1 * mu2) / (r ** 4)
    
    # Vacuum polarization (QED first-order correction)
    # Uehling potential correction
    ALPHA = 1/137.036  # Fine structure constant
    LAMBDA_C = 2.426e-12  # Compton wavelength of electron
    
    # Approximate correction factor for r >> λ_C
    if r > LAMBDA_C:
        qed_factor = 1 + (2 * ALPHA / (3 * np.pi)) * np.exp(-2 * r / LAMBDA_C)
    else:
        qed_factor = 1.0  # Near-field regime needs full calculation
    
    F_qed_corrected = F_coulomb * qed_factor
    delta_F_qed = F_qed_corrected - F_coulomb
    
    # Total force
    F_total = F_coulomb + F_magnetic
    
    return {
        "F_coulomb": F_coulomb,
        "F_magnetic_spin": F_magnetic,
        "F_qed_correction": delta_F_qed,
        "F_total": F_total,
        "particle_1": particle_type_1,
        "particle_2": particle_type_2,
        "distance": r,
        "force_difference_ee_vs_pp": (MU_ELECTRON**2 - MU_PROTON**2) * 
                                      (3 * MU_0 / (4 * np.pi)) / (r ** 4)
    }


def compare_charge_forces_all_cases(r: float = 0.01) -> dict:
    """
    Compare forces for ALL your cases at distance r!
    
    Cases:
    1. +e, +e (electron-electron or proton-proton)
    2. -e, -e (same as above in magnitude)
    3. +e, -e (attractive)
    4. +e, 0 (polarization)
    5. -e, 0 (polarization)
    6. 0, 0 (van der Waals)
    
    Returns complete analysis.
    """
    e = E_CHARGE  # 1.602e-19 C
    k = 1 / (4 * np.pi * EPSILON_0)
    
    # Base Coulomb forces
    F_base = k * e * e / (r ** 2)
    
    # Magnetic corrections
    MU_E = 9.284764e-24  # Electron magnetic moment
    MU_P = 1.410607e-26  # Proton magnetic moment
    
    F_mag_ee = (3 * MU_0 / (4 * np.pi)) * (MU_E * MU_E) / (r ** 4)
    F_mag_pp = (3 * MU_0 / (4 * np.pi)) * (MU_P * MU_P) / (r ** 4)
    
    # Polarization force (charge + neutral)
    # F = α * q² / (4πε₀)² / r⁵
    # where α is polarizability of neutral particle
    ALPHA_H = 6.67e-31  # Polarizability of hydrogen atom (m³)
    F_polarization = 2 * ALPHA_H * (k * e) ** 2 / (r ** 5)
    
    # Van der Waals (neutral-neutral)
    # F = -C₆/r⁷ (approximate)
    C6 = 1.0e-77  # Approximate C6 coefficient for atoms (J·m⁶)
    F_vdw = 6 * C6 / (r ** 7)
    
    return {
        "distance_m": r,
        "distance_cm": r * 100,
        
        "case_1_pos_pos": {
            "description": "+e and +e (two positive charges)",
            "F_classical": F_base,
            "F_magnetic_if_electrons": F_mag_ee,
            "F_magnetic_if_protons": F_mag_pp,
            "F_total_electrons": F_base + F_mag_ee,
            "F_total_protons": F_base + F_mag_pp,
            "direction": "REPULSIVE",
            "difference_e_vs_p": F_mag_ee - F_mag_pp
        },
        
        "case_2_neg_neg": {
            "description": "-e and -e (two negative charges/electrons)",
            "F_classical": F_base,
            "F_magnetic": F_mag_ee,
            "F_total": F_base + F_mag_ee,
            "direction": "REPULSIVE",
            "note": "Electrons only - no negative protons exist"
        },
        
        "case_3_pos_neg": {
            "description": "+e and -e (opposite charges)",
            "F_classical": -F_base,  # Negative = attractive
            "F_total": -F_base,
            "direction": "ATTRACTIVE",
            "note": "Strongest force case"
        },
        
        "case_4_pos_neutral": {
            "description": "+e and neutral",
            "F_polarization": F_polarization,
            "direction": "ATTRACTIVE (induced dipole)",
            "note": "Much weaker than Coulomb"
        },
        
        "case_5_neg_neutral": {
            "description": "-e and neutral",
            "F_polarization": F_polarization,
            "direction": "ATTRACTIVE (induced dipole)",
            "note": "Same as case 4 by symmetry"
        },
        
        "case_6_neutral_neutral": {
            "description": "Both neutral",
            "F_vdw": F_vdw,
            "direction": "ATTRACTIVE (van der Waals)",
            "note": "Weakest force"
        },
        
        "KEY_FINDING": {
            "message": "ELECTRON-ELECTRON repulsion IS slightly stronger than PROTON-PROTON!",
            "difference": F_mag_ee - F_mag_pp,
            "ratio": F_mag_ee / F_mag_pp if F_mag_pp > 0 else float('inf'),
            "reason": "Electron magnetic moment is 658x larger than proton magnetic moment"
        }
    }


# =============================================================================
# MAGNETIC FORCES FOR GENERATOR DESIGN
# =============================================================================

@dataclass
class MagneticDipole:
    """Represents a magnetic dipole (simplified magnet model)"""
    position: np.ndarray      # [x, y, z] meters
    moment: np.ndarray        # [mx, my, mz] A·m²
    

def magnetic_dipole_force(m1: MagneticDipole, m2: MagneticDipole) -> np.ndarray:
    """
    Calculate force between two magnetic dipoles.
    
    This is the fundamental force in our generator!
    
    F = (3μ₀/4π) * { [m₁·m₂ - 5(m₁·r̂)(m₂·r̂)]r̂ + (m₂·r̂)m₁ + (m₁·r̂)m₂ } / r⁴
    
    Parameters:
    -----------
    m1, m2 : MagneticDipole
        The two interacting dipoles
        
    Returns:
    --------
    F : np.ndarray
        Force vector on m2 due to m1
    """
    r = m2.position - m1.position
    r_mag = np.linalg.norm(r)
    
    if r_mag < 1e-10:
        return np.zeros(3)
    
    r_hat = r / r_mag
    
    # Dot products
    m1_dot_m2 = np.dot(m1.moment, m2.moment)
    m1_dot_r = np.dot(m1.moment, r_hat)
    m2_dot_r = np.dot(m2.moment, r_hat)
    
    # Force calculation
    prefactor = (3 * MU_0) / (4 * np.pi * r_mag**4)
    
    F = prefactor * (
        (m1_dot_m2 - 5 * m1_dot_r * m2_dot_r) * r_hat +
        m2_dot_r * m1.moment +
        m1_dot_r * m2.moment
    )
    
    return F


def calculate_rotor_torque(rotor_magnets: List[MagneticDipole],
                           stator_magnets: List[MagneticDipole],
                           rotor_axis: np.ndarray = np.array([0, 0, 1])) -> float:
    """
    Calculate net torque on rotor from stator field.
    
    τ = Σ r × F
    
    Parameters:
    -----------
    rotor_magnets : List[MagneticDipole]
        Magnets on the rotating part
    stator_magnets : List[MagneticDipole]
        Magnets on the stationary part
    rotor_axis : np.ndarray
        Axis of rotation (default: z-axis)
        
    Returns:
    --------
    torque : float
        Net torque around rotation axis (N·m)
    """
    total_torque = np.zeros(3)
    
    for rotor_mag in rotor_magnets:
        F_total = np.zeros(3)
        
        for stator_mag in stator_magnets:
            F = magnetic_dipole_force(stator_mag, rotor_mag)
            F_total += F
        
        # Torque contribution: τ = r × F
        torque = np.cross(rotor_mag.position, F_total)
        total_torque += torque
    
    # Project onto rotation axis
    return np.dot(total_torque, rotor_axis / np.linalg.norm(rotor_axis))


def calculate_cogging_torque(theta: float, n_rotor_poles: int, n_stator_slots: int,
                             rotor_radius: float, stator_radius: float,
                             magnet_moment: float) -> float:
    """
    Calculate cogging torque at given angular position.
    
    Cogging is the "notchy" feeling - we want to MINIMIZE this!
    
    T_cog = T_max * sin(n_cog * θ)
    
    where n_cog = LCM(poles, slots)
    
    Parameters:
    -----------
    theta : float
        Rotor angle (radians)
    n_rotor_poles : int
        Number of rotor poles
    n_stator_slots : int
        Number of stator slots
    rotor_radius, stator_radius : float
        Radii in meters
    magnet_moment : float
        Magnetic moment per magnet
        
    Returns:
    --------
    T_cog : float
        Cogging torque at this position
    """
    # LCM determines cogging frequency
    from math import gcd
    n_cog = (n_rotor_poles * n_stator_slots) // gcd(n_rotor_poles, n_stator_slots)
    
    # Air gap
    air_gap = stator_radius - rotor_radius
    
    # Maximum cogging torque (empirical formula)
    B_ag = (MU_0 * magnet_moment) / (4 * np.pi * air_gap**3)
    T_max = 0.5 * B_ag**2 * rotor_radius**3 / MU_0
    
    # Cogging torque
    T_cog = T_max * np.sin(n_cog * theta)
    
    return T_cog


def calculate_radial_force(theta: float, n_poles: int, 
                          rotor_radius: float, stator_radius: float,
                          B_airgap: float) -> Tuple[float, float]:
    """
    Calculate radial magnetic forces (attraction/repulsion).
    
    These are centripetal/centrifugal forces you mentioned!
    
    Returns:
    --------
    F_radial : float
        Net radial force (positive = outward)
    F_tangential : float
        Tangential force (creates torque)
    """
    air_gap = stator_radius - rotor_radius
    
    # Maxwell stress tensor gives magnetic pressure
    # p = B²/(2μ₀) - this is the attractive force per unit area
    
    # Radial component of B at rotor surface (approximate)
    B_r = B_airgap * np.cos(n_poles/2 * theta)
    
    # Tangential component
    B_t = B_airgap * np.sin(n_poles/2 * theta)
    
    # Maxwell stress tensor components
    sigma_rr = (B_r**2 - B_t**2) / (2 * MU_0)  # Normal stress (attractive)
    sigma_rt = B_r * B_t / MU_0                 # Shear stress (torque)
    
    # Force per unit area * approximate area
    area = np.pi * rotor_radius**2 / n_poles
    
    F_radial = sigma_rr * area      # Centripetal force
    F_tangential = sigma_rt * area  # Creates rotation
    
    return F_radial, F_tangential
