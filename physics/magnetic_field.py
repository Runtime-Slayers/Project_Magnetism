"""
Magnetic Field Calculations for Permanent Magnet Generator
============================================================
Comprehensive magnetic field modeling including:
- Point dipole approximation
- Halbach array fields
- Finite element-like grid calculations
- Flux linkage calculations
"""

import numpy as np
from typing import Tuple, List, Optional
from dataclasses import dataclass
from .constants import MU_0, BR_NEODYMIUM, N52_NEODYMIUM


@dataclass
class Magnet:
    """Represents a single permanent magnet"""
    position: np.ndarray      # [x, y, z] in meters
    magnetization: np.ndarray  # [Mx, My, Mz] in A/m
    dimensions: np.ndarray    # [length, width, height] in meters
    Br: float = BR_NEODYMIUM  # Remanent flux density
    
    @property
    def volume(self) -> float:
        return np.prod(self.dimensions)
    
    @property
    def magnetic_moment(self) -> np.ndarray:
        """Magnetic dipole moment m = M * V"""
        return self.magnetization * self.volume


def dipole_field(r: np.ndarray, m: np.ndarray, r0: np.ndarray = None) -> np.ndarray:
    """
    Calculate magnetic field from a magnetic dipole.
    
    B(r) = (μ₀/4π) * [3(m·r̂)r̂ - m] / r³
    
    Parameters:
    -----------
    r : np.ndarray
        Position vector where field is calculated [x, y, z]
    m : np.ndarray
        Magnetic moment vector [mx, my, mz]
    r0 : np.ndarray, optional
        Position of the dipole (default: origin)
        
    Returns:
    --------
    B : np.ndarray
        Magnetic field vector [Bx, By, Bz] in Tesla
    """
    if r0 is not None:
        r = r - r0
    
    r_mag = np.linalg.norm(r)
    if r_mag < 1e-10:
        return np.zeros(3)
    
    r_hat = r / r_mag
    
    # Dipole field formula
    B = (MU_0 / (4 * np.pi)) * (3 * np.dot(m, r_hat) * r_hat - m) / (r_mag ** 3)
    
    return B


def halbach_array_field(r: np.ndarray, n_magnets: int, radius: float,
                        magnet_dims: np.ndarray, Br: float = BR_NEODYMIUM,
                        order: int = 1) -> np.ndarray:
    """
    Calculate magnetic field from a Halbach array (circular).
    
    Halbach arrays concentrate flux on one side and cancel on the other.
    This is KEY for high-efficiency generators!
    
    Parameters:
    -----------
    r : np.ndarray
        Position where field is calculated
    n_magnets : int
        Number of magnets in the array
    radius : float
        Radius of the array (meters)
    magnet_dims : np.ndarray
        Dimensions of each magnet [radial, tangential, axial]
    Br : float
        Remanent flux density of magnets
    order : int
        Halbach array order (1 = standard, 2 = quadrupole, etc.)
        
    Returns:
    --------
    B : np.ndarray
        Total magnetic field at position r
    """
    B_total = np.zeros(3)
    
    # Magnetization magnitude
    M = Br / MU_0
    
    for i in range(n_magnets):
        # Position angle of magnet
        theta = 2 * np.pi * i / n_magnets
        
        # Halbach magnetization direction
        # For order k: magnetization rotates (k+1) times per revolution
        mag_angle = (order + 1) * theta
        
        # Magnet position
        magnet_pos = radius * np.array([np.cos(theta), np.sin(theta), 0])
        
        # Magnetization vector (in radial-tangential plane)
        magnetization = M * np.array([
            np.cos(mag_angle),
            np.sin(mag_angle),
            0
        ])
        
        # Volume of magnet
        volume = np.prod(magnet_dims)
        
        # Magnetic moment
        m = magnetization * volume
        
        # Add contribution from this magnet
        B_total += dipole_field(r, m, magnet_pos)
    
    return B_total


def calculate_flux_linkage(coil_positions: np.ndarray, 
                          coil_area: float,
                          coil_normal: np.ndarray,
                          magnets: List[Magnet],
                          n_turns: int = 100) -> float:
    """
    Calculate magnetic flux through a coil.
    
    Φ = N * ∫∫ B · dA
    
    This is essential for EMF calculation via Faraday's law.
    
    Parameters:
    -----------
    coil_positions : np.ndarray
        Array of sample points within the coil
    coil_area : float
        Total area of the coil (m²)
    coil_normal : np.ndarray
        Unit normal vector to coil plane
    magnets : List[Magnet]
        List of magnets contributing to field
    n_turns : int
        Number of turns in the coil
        
    Returns:
    --------
    flux : float
        Total flux linkage (Weber)
    """
    # Calculate average B field through coil
    B_avg = np.zeros(3)
    
    for pos in coil_positions:
        for magnet in magnets:
            B_avg += dipole_field(pos, magnet.magnetic_moment, magnet.position)
    
    B_avg /= len(coil_positions)
    
    # Flux linkage = N * B · A
    flux = n_turns * np.dot(B_avg, coil_normal) * coil_area
    
    return flux


def calculate_emf(flux_values: np.ndarray, time_values: np.ndarray) -> np.ndarray:
    """
    Calculate induced EMF from flux linkage using Faraday's law.
    
    ε = -dΦ/dt
    
    Parameters:
    -----------
    flux_values : np.ndarray
        Array of flux linkage values over time
    time_values : np.ndarray
        Corresponding time values
        
    Returns:
    --------
    emf : np.ndarray
        Induced EMF at each time point
    """
    # Numerical differentiation
    emf = -np.gradient(flux_values, time_values)
    return emf


class MagneticFieldGrid:
    """
    Grid-based magnetic field calculation for visualization
    and numerical analysis.
    """
    
    def __init__(self, x_range: Tuple[float, float],
                 y_range: Tuple[float, float],
                 z_range: Tuple[float, float],
                 resolution: int = 50):
        """Initialize a 3D grid for field calculations"""
        self.x = np.linspace(x_range[0], x_range[1], resolution)
        self.y = np.linspace(y_range[0], y_range[1], resolution)
        self.z = np.linspace(z_range[0], z_range[1], resolution)
        
        self.X, self.Y, self.Z = np.meshgrid(self.x, self.y, self.z)
        self.Bx = np.zeros_like(self.X)
        self.By = np.zeros_like(self.Y)
        self.Bz = np.zeros_like(self.Z)
        
    def calculate_field(self, magnets: List[Magnet]):
        """Calculate B field at all grid points"""
        for i in range(len(self.x)):
            for j in range(len(self.y)):
                for k in range(len(self.z)):
                    pos = np.array([self.X[j, i, k], 
                                   self.Y[j, i, k], 
                                   self.Z[j, i, k]])
                    
                    B = np.zeros(3)
                    for magnet in magnets:
                        B += dipole_field(pos, magnet.magnetic_moment, 
                                         magnet.position)
                    
                    self.Bx[j, i, k] = B[0]
                    self.By[j, i, k] = B[1]
                    self.Bz[j, i, k] = B[2]
    
    @property
    def B_magnitude(self) -> np.ndarray:
        """Calculate field magnitude at all points"""
        return np.sqrt(self.Bx**2 + self.By**2 + self.Bz**2)


def rotor_field_at_angle(theta: float, n_poles: int, radius: float,
                         magnet_dims: np.ndarray, Br: float,
                         stator_radius: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate rotor magnetic field as seen by stator at given rotor angle.
    
    Parameters:
    -----------
    theta : float
        Rotor angular position (radians)
    n_poles : int
        Number of magnetic poles on rotor
    radius : float
        Rotor outer radius
    magnet_dims : np.ndarray
        Magnet dimensions [radial, tangential, axial]
    Br : float
        Remanent flux density
    stator_radius : float
        Inner radius of stator
        
    Returns:
    --------
    angles : np.ndarray
        Angular positions around stator
    B_radial : np.ndarray
        Radial component of B field at stator
    """
    # Sample points around stator inner surface
    n_samples = 360
    angles = np.linspace(0, 2*np.pi, n_samples)
    B_radial = np.zeros(n_samples)
    
    M = Br / MU_0
    volume = np.prod(magnet_dims)
    
    for idx, phi in enumerate(angles):
        # Stator point position
        stator_point = stator_radius * np.array([np.cos(phi), np.sin(phi), 0])
        
        # Sum contributions from all rotor magnets
        B = np.zeros(3)
        for pole in range(n_poles):
            # Magnet position (rotated by theta)
            magnet_angle = theta + 2 * np.pi * pole / n_poles
            magnet_pos = radius * np.array([
                np.cos(magnet_angle), 
                np.sin(magnet_angle), 
                0
            ])
            
            # Magnetization direction (alternating radial)
            sign = 1 if pole % 2 == 0 else -1
            magnetization = sign * M * np.array([
                np.cos(magnet_angle),
                np.sin(magnet_angle),
                0
            ])
            
            m = magnetization * volume
            B += dipole_field(stator_point, m, magnet_pos)
        
        # Radial component at stator
        r_hat = np.array([np.cos(phi), np.sin(phi), 0])
        B_radial[idx] = np.dot(B, r_hat)
    
    return angles, B_radial
