"""
PERMANENT MAGNET GENERATOR - COMPLETE ASSEMBLY
===============================================
Creates the full generator assembly using CadQuery.

This brings together all components:
1. ROTOR - Spinning part with permanent magnets
2. STATOR - Stationary part with copper windings  
3. SHAFT - Transmits mechanical power from turbine/engine
4. BEARINGS - Allow smooth rotation with minimal friction
5. HOUSING - Protects internals, provides mounting
6. END CAPS - Close the housing, hold bearings
7. COOLING - Fins or fan for heat dissipation

The generated STEP files can be imported into:
- FreeCAD (free, open source)
- Fusion 360 (free for hobbyists)
- SolidWorks, CATIA, NX (commercial)
- Any CFD/FEA software for simulation

CadQuery: https://cadquery.readthedocs.io/
"""

try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError:
    CADQUERY_AVAILABLE = False
    print("CadQuery not installed. Install with: pip install cadquery-ocp")

import math
from typing import Optional, Tuple, Dict
from dataclasses import dataclass

from .parameters import GeneratorParameters, DEFAULT_PARAMS
from .rotor_cad import create_rotor_assembly
from .stator_cad import create_stator_assembly


@dataclass
class BearingSpec:
    """Bearing specifications (standard sizes)."""
    inner_diameter: float   # Shaft fit (mm)
    outer_diameter: float   # Housing fit (mm)
    width: float            # Axial width (mm)
    
    @property
    def name(self) -> str:
        return f"6{int(self.inner_diameter/5):02d}"  # e.g., 6205 for 25mm bore


# Standard bearing sizes (6000 series, common for generators)
BEARINGS = {
    "6203": BearingSpec(17, 40, 12),
    "6204": BearingSpec(20, 47, 14),
    "6205": BearingSpec(25, 52, 15),
    "6206": BearingSpec(30, 62, 16),
    "6207": BearingSpec(35, 72, 17),
    "6208": BearingSpec(40, 80, 18),
}


def create_shaft(params: GeneratorParameters = None,
                shaft_length: float = 200.0) -> "cq.Workplane":
    """
    Create the generator shaft.
    
    The shaft transmits torque from the prime mover (turbine, engine)
    to the rotor. It must be:
    - Strong enough to handle torque without twisting
    - Stiff enough to avoid vibration
    - Precisely machined for bearing fit
    
    Features:
    - Main body (constant diameter through rotor)
    - Bearing journals (where bearings mount)
    - Keyway (for driving the rotor)
    - Drive end (for coupling to prime mover)
    
    Parameters:
        params: Generator parameters
        shaft_length: Total shaft length (mm)
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Shaft dimensions
    main_diameter = params.rotor_inner_radius * 2 - 0.1  # Slight clearance
    bearing_diameter = main_diameter  # Same for now
    drive_end_length = 40.0
    
    # Create main shaft body
    shaft = (
        cq.Workplane("XY")
        .circle(main_diameter / 2)
        .extrude(shaft_length)
    )
    
    # Add keyway along the length where rotor sits
    keyway = (
        cq.Workplane("XY")
        .center(main_diameter / 2 - params.keyway_depth / 2, 0)
        .rect(params.keyway_depth, params.keyway_width)
        .extrude(params.rotor_length + 20)  # Extend past rotor
    )
    # Position keyway in middle of shaft
    keyway_offset = (shaft_length - params.rotor_length) / 2
    keyway = keyway.translate((0, 0, keyway_offset - 10))
    shaft = shaft.cut(keyway)
    
    return shaft


def create_bearing(bearing_type: str = "6205") -> "cq.Workplane":
    """
    Create a simplified bearing model.
    
    Real bearings are complex with balls, races, seals, etc.
    This is a simplified representation showing the envelope.
    
    Parameters:
        bearing_type: Standard bearing designation (e.g., "6205")
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    spec = BEARINGS.get(bearing_type, BEARINGS["6205"])
    
    # Outer ring
    bearing = (
        cq.Workplane("XY")
        .circle(spec.outer_diameter / 2)
        .circle(spec.inner_diameter / 2)
        .extrude(spec.width)
    )
    
    # Add visual detail - chamfer edges
    bearing = (
        bearing
        .edges("|Z")
        .chamfer(0.5)
    )
    
    return bearing


def create_housing(params: GeneratorParameters = None,
                  wall_thickness: float = 8.0) -> "cq.Workplane":
    """
    Create the generator housing (frame).
    
    The housing:
    - Protects internal components
    - Provides mounting feet
    - Acts as heat sink (optional fins)
    - Supports the stator
    
    Parameters:
        params: Generator parameters
        wall_thickness: Housing wall thickness (mm)
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Housing dimensions
    inner_radius = params.stator_outer_radius + 0.5  # Small clearance
    outer_radius = inner_radius + wall_thickness
    housing_length = params.stator_length + 20  # Extra for end caps
    
    # Main cylindrical housing
    housing = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(housing_length)
    )
    
    # Add mounting feet
    foot_width = 30.0
    foot_length = outer_radius * 2 + 20
    foot_height = 15.0
    
    for x_mult in [-1, 1]:
        foot = (
            cq.Workplane("XY")
            .center(x_mult * (outer_radius - 5), -outer_radius - foot_height / 2)
            .rect(foot_width, foot_height)
            .extrude(housing_length)
        )
        
        # Mounting holes
        hole = (
            cq.Workplane("XY")
            .center(x_mult * (outer_radius - 5), -outer_radius - foot_height / 2)
            .circle(4)  # M8 clearance
            .extrude(housing_length)
        )
        foot = foot.cut(hole)
        housing = housing.union(foot)
    
    # Add cooling fins
    num_fins = 12
    fin_height = 5.0
    fin_thickness = 2.0
    
    for i in range(num_fins):
        angle = i * 30  # 30° spacing
        if 60 < angle < 120 or 240 < angle < 300:  # Skip bottom (feet area)
            continue
            
        # Create radial fin
        fin = (
            cq.Workplane("XY")
            .center(outer_radius, 0)
            .rect(fin_height * 2, fin_thickness)
            .extrude(housing_length - 10)
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        fin = fin.translate((0, 0, 5))
        housing = housing.union(fin)
    
    return housing


def create_end_cap(params: GeneratorParameters = None,
                  bearing_type: str = "6205",
                  is_drive_end: bool = False) -> "cq.Workplane":
    """
    Create an end cap (bearing housing).
    
    End caps:
    - Hold the bearings in place
    - Seal the housing
    - Allow shaft to pass through
    - Can include seals to keep out dust/moisture
    
    Parameters:
        params: Generator parameters  
        bearing_type: Which bearing size
        is_drive_end: True for drive end (thicker, stronger)
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    bearing = BEARINGS.get(bearing_type, BEARINGS["6205"])
    
    # End cap dimensions
    outer_radius = params.stator_outer_radius + 8.5  # Match housing
    cap_thickness = 15.0 if is_drive_end else 12.0
    
    # Main disc
    cap = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .extrude(cap_thickness)
    )
    
    # Bearing pocket (where bearing sits)
    bearing_pocket = (
        cq.Workplane("XY")
        .circle(bearing.outer_diameter / 2 + 0.05)  # Press fit
        .extrude(bearing.width + 1)
    )
    cap = cap.cut(bearing_pocket)
    
    # Shaft hole
    shaft_hole = (
        cq.Workplane("XY")
        .circle(bearing.inner_diameter / 2 + 2)  # Clearance
        .extrude(cap_thickness)
    )
    cap = cap.cut(shaft_hole)
    
    # Bolt holes for mounting to housing (6 holes)
    bolt_circle = outer_radius - 10
    for i in range(6):
        angle = math.radians(i * 60)
        x = bolt_circle * math.cos(angle)
        y = bolt_circle * math.sin(angle)
        
        bolt_hole = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(4.5)  # M8 clearance
            .extrude(cap_thickness)
        )
        cap = cap.cut(bolt_hole)
    
    return cap


def create_cooling_fan(params: GeneratorParameters = None,
                       fan_diameter: float = None) -> "cq.Workplane":
    """
    Create a cooling fan for the generator.
    
    Small generators often use a shaft-mounted fan to pull air
    through the housing for cooling. This is a simplified model.
    
    Parameters:
        params: Generator parameters
        fan_diameter: Fan outer diameter (auto-sized if None)
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    if fan_diameter is None:
        fan_diameter = params.rotor_inner_radius * 3
    
    hub_diameter = params.rotor_inner_radius * 2
    hub_height = 10.0
    blade_count = 6
    blade_thickness = 2.0
    
    # Hub (center)
    fan = (
        cq.Workplane("XY")
        .circle(hub_diameter / 2)
        .circle(params.rotor_inner_radius)  # Shaft hole
        .extrude(hub_height)
    )
    
    # Blades (radial, slightly curved would be better but simple for now)
    blade_length = (fan_diameter - hub_diameter) / 2
    blade_height = hub_height * 1.5
    
    for i in range(blade_count):
        angle = i * (360 / blade_count)
        
        blade = (
            cq.Workplane("XZ")
            .center(hub_diameter / 2 + blade_length / 2, blade_height / 2)
            .rect(blade_length, blade_height)
            .extrude(blade_thickness)
            .rotate((0, 0, 0), (0, 0, 1), angle + 15)  # 15° angle for airflow
        )
        fan = fan.union(blade)
    
    return fan


def create_generator_assembly(params: GeneratorParameters = None,
                             include_housing: bool = True,
                             exploded_view: bool = False) -> "cq.Workplane":
    """
    Create the complete generator assembly.
    
    This brings together all components into a single model.
    Use exploded_view=True to see how parts fit together.
    
    Components in order (from drive end to non-drive end):
    1. Drive end cap with bearing
    2. Shaft
    3. Rotor (mounted on shaft)
    4. Stator (mounted in housing)
    5. Housing
    6. Non-drive end cap with bearing
    7. Cooling fan (optional)
    
    Parameters:
        params: Generator parameters
        include_housing: Whether to include housing and end caps
        exploded_view: Spread parts apart for visualization
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Explosion offset for exploded view
    offset = 30.0 if exploded_view else 0.0
    
    # Calculate positions
    housing_length = params.stator_length + 20
    shaft_length = housing_length + 80  # Extends past both ends
    
    stator_z = 10  # Inside housing
    rotor_z = stator_z + (params.stator_length - params.rotor_length) / 2
    shaft_z = -30
    
    # ===== CREATE COMPONENTS =====
    
    # Rotor (at center)
    rotor = create_rotor_assembly(params)
    rotor = rotor.translate((0, 0, rotor_z - offset))
    
    # Stator (fixed, surrounds rotor with air gap)
    stator = create_stator_assembly(params)
    stator = stator.translate((0, 0, stator_z))
    
    # Shaft
    shaft = create_shaft(params, shaft_length)
    shaft = shaft.translate((0, 0, shaft_z - 2 * offset))
    
    assembly = rotor.union(stator).union(shaft)
    
    if include_housing:
        # Housing
        housing = create_housing(params)
        housing = housing.translate((0, 0, offset))
        
        # End caps
        drive_cap = create_end_cap(params, is_drive_end=True)
        drive_cap = drive_cap.translate((0, 0, -15 - 2 * offset))
        
        non_drive_cap = create_end_cap(params, is_drive_end=False)
        non_drive_cap = non_drive_cap.translate((0, 0, housing_length + 2 * offset))
        
        # Bearings
        bearing_de = create_bearing("6205")
        bearing_de = bearing_de.translate((0, 0, -10 - 2 * offset))
        
        bearing_nde = create_bearing("6205")
        bearing_nde = bearing_nde.translate((0, 0, housing_length + 5 + 2 * offset))
        
        # Cooling fan
        fan = create_cooling_fan(params)
        fan = fan.translate((0, 0, housing_length + 25 + 3 * offset))
        
        assembly = (
            assembly
            .union(housing)
            .union(drive_cap)
            .union(non_drive_cap)
            .union(bearing_de)
            .union(bearing_nde)
            .union(fan)
        )
    
    return assembly


def export_generator_assembly(params: GeneratorParameters = None,
                             output_dir: str = "output",
                             export_individual: bool = True) -> Dict[str, str]:
    """
    Export all generator components to STEP files.
    
    Creates individual files for each component plus the full assembly.
    This allows importing parts separately for manufacturing or simulation.
    
    Parameters:
        params: Generator parameters
        output_dir: Directory for output files
        export_individual: Also export individual components
        
    Returns:
        Dictionary of component names to file paths
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    if params is None:
        params = DEFAULT_PARAMS
    
    exports = {}
    
    # Full assembly
    print("Creating full assembly...")
    assembly = create_generator_assembly(params)
    assembly_path = os.path.join(output_dir, "generator_assembly.step")
    cq.exporters.export(assembly, assembly_path)
    exports["assembly"] = assembly_path
    print(f"  ✅ {assembly_path}")
    
    # Exploded view
    print("Creating exploded view...")
    exploded = create_generator_assembly(params, exploded_view=True)
    exploded_path = os.path.join(output_dir, "generator_exploded.step")
    cq.exporters.export(exploded, exploded_path)
    exports["exploded"] = exploded_path
    print(f"  ✅ {exploded_path}")
    
    if export_individual:
        # Individual components
        components = {
            "rotor": create_rotor_assembly(params),
            "stator": create_stator_assembly(params),
            "shaft": create_shaft(params),
            "housing": create_housing(params),
            "end_cap_drive": create_end_cap(params, is_drive_end=True),
            "end_cap_non_drive": create_end_cap(params, is_drive_end=False),
            "bearing": create_bearing("6205"),
            "cooling_fan": create_cooling_fan(params),
        }
        
        print("Exporting individual components...")
        for name, component in components.items():
            path = os.path.join(output_dir, f"{name}.step")
            cq.exporters.export(component, path)
            exports[name] = path
            print(f"  ✅ {path}")
    
    print(f"\n📁 All files exported to: {output_dir}/")
    return exports


def get_bill_of_materials(params: GeneratorParameters = None) -> Dict:
    """
    Generate a bill of materials for the generator.
    
    This lists all components needed to build the generator
    with approximate specifications.
    
    Parameters:
        params: Generator parameters
        
    Returns:
        Dictionary with BOM information
    """
    if params is None:
        params = DEFAULT_PARAMS
    
    bom = {
        "rotor_core": {
            "material": "Silicon Steel (M270-35A)",
            "quantity": 1,
            "outer_diameter_mm": (params.rotor_outer_radius - params.magnet_thickness) * 2,
            "inner_diameter_mm": params.rotor_inner_radius * 2,
            "length_mm": params.rotor_length,
            "notes": "Laminated, 0.35mm sheets"
        },
        "permanent_magnets": {
            "material": params.magnet_material,
            "quantity": params.n_poles,
            "grade": "N52 NdFeB",
            "type": "Arc segment",
            "arc_angle_deg": params.magnet_angle_deg,
            "thickness_mm": params.magnet_thickness,
            "length_mm": params.magnet_length,
            "notes": "Alternating N-S magnetization"
        },
        "stator_core": {
            "material": "Silicon Steel (M270-35A)",
            "quantity": 1,
            "outer_diameter_mm": params.stator_outer_radius * 2,
            "inner_diameter_mm": params.stator_inner_radius * 2,
            "length_mm": params.stator_length,
            "slots": params.n_slots,
            "notes": "Laminated, 0.35mm sheets"
        },
        "copper_wire": {
            "material": "Copper, enameled",
            "quantity_kg": "~2-5 (depends on design)",
            "wire_gauge": "AWG 16-20 (1.0-1.3mm)",
            "notes": f"Wind {params.n_slots} coils"
        },
        "bearings": {
            "type": "6205-2RS (sealed)",
            "quantity": 2,
            "bore_mm": 25,
            "outer_mm": 52,
            "width_mm": 15,
            "notes": "Deep groove ball bearing"
        },
        "shaft": {
            "material": "4140 Steel",
            "quantity": 1,
            "diameter_mm": params.rotor_inner_radius * 2,
            "length_mm": 200,
            "notes": "Ground finish at bearing journals"
        },
        "housing": {
            "material": "Aluminum 6061-T6",
            "quantity": 1,
            "notes": "Can be cast or machined"
        },
        "fasteners": {
            "end_cap_bolts": "M8 x 30, qty 12",
            "mounting_bolts": "M10 x varies, qty 4",
            "notes": "Stainless or zinc plated"
        },
        "slot_liners": {
            "material": "Nomex paper",
            "thickness_mm": 0.3,
            "quantity": params.n_slots,
        }
    }
    
    return bom


# For direct testing
if __name__ == "__main__":
    if CADQUERY_AVAILABLE:
        print("="*60)
        print("PERMANENT MAGNET GENERATOR - CAD EXPORT")
        print("="*60)
        
        # Show BOM first
        print("\n📋 BILL OF MATERIALS:")
        print("-"*40)
        bom = get_bill_of_materials()
        for component, details in bom.items():
            print(f"\n{component.upper()}:")
            for key, value in details.items():
                print(f"  {key}: {value}")
        
        # Export all
        print("\n" + "="*60)
        print("EXPORTING CAD FILES...")
        print("="*60)
        exports = export_generator_assembly()
        
        print("\n✅ Export complete!")
        print("   Import .STEP files into FreeCAD, Fusion 360, or other CAD software")
        
    else:
        print("⚠️  CadQuery not installed!")
        print("   Install with: pip install cadquery-ocp")
        print("   Then run this script again.")
