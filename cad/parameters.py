"""
PERMANENT MAGNET GENERATOR - DESIGN PARAMETERS
================================================
Central parameter file for all CAD components.
All dimensions in MILLIMETERS (mm) for CadQuery.

This file contains all the configurable parameters for the generator design.
Modify these values to customize your generator.
"""

import math
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class GeneratorParameters:
    """
    Complete set of design parameters for the permanent magnet generator.
    
    All dimensions are in millimeters (mm) unless otherwise noted.
    Angles are in degrees.
    """
    
    # ========================================================================
    # MAIN DESIGN PARAMETERS
    # ========================================================================
    
    # Number of magnetic poles (MUST be even number)
    n_poles: int = 12
    
    # Number of stator slots (typically 1.5× poles for 3-phase)
    n_slots: int = 18
    
    # Number of electrical phases
    n_phases: int = 3
    
    # ========================================================================
    # ROTOR DIMENSIONS (mm)
    # ========================================================================
    
    # Rotor outer radius (where magnets are mounted)
    rotor_outer_radius: float = 50.0
    
    # Rotor inner radius (shaft bore)
    rotor_inner_radius: float = 15.0
    
    # Rotor active length (axial direction)
    rotor_length: float = 100.0
    
    # Rotor back-iron thickness
    rotor_back_iron: float = 8.0
    
    # ========================================================================
    # MAGNET DIMENSIONS (mm)
    # ========================================================================
    
    # Magnet thickness (radial direction)
    magnet_thickness: float = 5.0
    
    # Magnet arc ratio (fraction of pole pitch, 0.5 to 0.95)
    magnet_arc_ratio: float = 0.85
    
    # Magnet length (axial, slightly less than rotor_length)
    magnet_length: float = 96.0
    
    # Magnet skew angle for anti-cogging (electrical degrees)
    magnet_skew_deg: float = 15.0
    
    # ========================================================================
    # STATOR DIMENSIONS (mm)
    # ========================================================================
    
    # Air gap between rotor and stator (CRITICAL - typically 0.5-2mm)
    air_gap: float = 1.5
    
    # Stator outer radius
    stator_outer_radius: float = 80.0
    
    # Stator yoke (back iron) thickness
    stator_yoke: float = 10.0
    
    # Stator tooth width at narrowest point
    tooth_width: float = 5.0
    
    # Slot opening width
    slot_opening: float = 2.0
    
    # ========================================================================
    # SHAFT DIMENSIONS (mm)
    # ========================================================================
    
    # Shaft diameter
    shaft_diameter: float = 20.0
    
    # Shaft total length
    shaft_length: float = 200.0
    
    # Keyway dimensions
    keyway_width: float = 6.0
    keyway_depth: float = 3.0
    
    # ========================================================================
    # HOUSING DIMENSIONS (mm)
    # ========================================================================
    
    # Housing wall thickness
    housing_wall: float = 5.0
    
    # End cap thickness
    end_cap_thickness: float = 10.0
    
    # Cooling fin parameters
    fin_count: int = 12
    fin_height: float = 15.0
    fin_thickness: float = 3.0
    
    # ========================================================================
    # BEARING PARAMETERS (mm) - Standard 6004-2RS
    # ========================================================================
    
    bearing_od: float = 42.0
    bearing_id: float = 20.0
    bearing_width: float = 12.0
    
    # ========================================================================
    # CALCULATED PROPERTIES
    # ========================================================================
    
    @property
    def stator_inner_radius(self) -> float:
        """Stator inner radius = rotor outer + air gap"""
        return self.rotor_outer_radius + self.air_gap
    
    @property
    def pole_pitch_deg(self) -> float:
        """Angular pitch of one pole in degrees"""
        return 360.0 / self.n_poles
    
    @property
    def slot_pitch_deg(self) -> float:
        """Angular pitch of one slot in degrees"""
        return 360.0 / self.n_slots
    
    @property
    def magnet_angle_deg(self) -> float:
        """Angular extent of one magnet in degrees"""
        return self.magnet_arc_ratio * self.pole_pitch_deg
    
    @property
    def slot_depth(self) -> float:
        """Depth of stator slot"""
        return self.stator_outer_radius - self.stator_inner_radius - self.stator_yoke - 2
    
    @property
    def housing_outer_diameter(self) -> float:
        """Outer diameter of housing"""
        return 2 * self.stator_outer_radius + 2 * self.housing_wall
    
    @property
    def cogging_order(self) -> int:
        """LCM of poles and slots - determines cogging frequency"""
        from math import gcd
        return (self.n_poles * self.n_slots) // gcd(self.n_poles, self.n_slots)
    
    def validate(self) -> list:
        """
        Validate design parameters and return list of warnings/errors.
        
        Returns:
            List of warning/error messages (empty if all OK)
        """
        issues = []
        
        # Check poles are even
        if self.n_poles % 2 != 0:
            issues.append("ERROR: n_poles must be even!")
        
        # Check slots for 3-phase
        if self.n_phases == 3 and self.n_slots % 3 != 0:
            issues.append("ERROR: n_slots must be divisible by 3 for 3-phase!")
        
        # Check air gap
        if self.air_gap < 0.5:
            issues.append("WARNING: Air gap < 0.5mm may cause rotor-stator contact!")
        if self.air_gap > 3.0:
            issues.append("WARNING: Air gap > 3mm reduces efficiency significantly!")
        
        # Check magnet arc
        if self.magnet_arc_ratio < 0.5:
            issues.append("WARNING: Magnet arc ratio < 0.5 reduces flux significantly!")
        if self.magnet_arc_ratio > 0.95:
            issues.append("WARNING: Magnet arc ratio > 0.95 leaves no gap between magnets!")
        
        # Check shaft fits in rotor
        if self.shaft_diameter / 2 >= self.rotor_inner_radius:
            issues.append("ERROR: Shaft diameter too large for rotor bore!")
        
        return issues


# Default parameters instance
DEFAULT_PARAMS = GeneratorParameters()


def print_parameters(params: GeneratorParameters = None):
    """Print all parameters in a formatted table"""
    if params is None:
        params = DEFAULT_PARAMS
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              GENERATOR DESIGN PARAMETERS                             ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ELECTRICAL CONFIGURATION                                           ║
║  ├─ Poles:          {n_poles:3d}                                           ║
║  ├─ Slots:          {n_slots:3d}                                           ║
║  ├─ Phases:         {n_phases:3d}                                           ║
║  └─ Cogging Order:  {cog:3d} (higher = smoother)                       ║
║                                                                      ║
║  ROTOR (mm)                                                          ║
║  ├─ Outer Radius:   {r_out:6.1f}                                         ║
║  ├─ Inner Radius:   {r_in:6.1f}                                         ║
║  └─ Length:         {r_len:6.1f}                                         ║
║                                                                      ║
║  MAGNETS (mm)                                                        ║
║  ├─ Thickness:      {m_thick:6.1f}                                         ║
║  ├─ Arc Ratio:      {m_arc:6.2f}                                         ║
║  └─ Skew Angle:     {m_skew:6.1f}° (anti-cogging)                         ║
║                                                                      ║
║  STATOR (mm)                                                         ║
║  ├─ Inner Radius:   {s_in:6.1f}                                         ║
║  ├─ Outer Radius:   {s_out:6.1f}                                         ║
║  └─ Air Gap:        {gap:6.1f} (CRITICAL!)                              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""".format(
        n_poles=params.n_poles,
        n_slots=params.n_slots,
        n_phases=params.n_phases,
        cog=params.cogging_order,
        r_out=params.rotor_outer_radius,
        r_in=params.rotor_inner_radius,
        r_len=params.rotor_length,
        m_thick=params.magnet_thickness,
        m_arc=params.magnet_arc_ratio,
        m_skew=params.magnet_skew_deg,
        s_in=params.stator_inner_radius,
        s_out=params.stator_outer_radius,
        gap=params.air_gap
    ))
    
    # Print validation
    issues = params.validate()
    if issues:
        print("⚠️  VALIDATION ISSUES:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ All parameters validated successfully!")


if __name__ == "__main__":
    print_parameters()
