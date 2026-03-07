"""
PERMANENT MAGNET GENERATOR - ROTOR CAD MODEL
==============================================
Creates the rotor assembly using CadQuery.

The rotor consists of:
1. Rotor core (laminated steel) - the main cylindrical body
2. Permanent magnets - alternating N/S poles arranged around circumference
3. Shaft interface - keyway for torque transmission
4. Retention features - optional ring to hold magnets at high speed

CadQuery Documentation: https://cadquery.readthedocs.io/
"""

try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError:
    CADQUERY_AVAILABLE = False
    print("CadQuery not installed. Install with: pip install cadquery-ocp")

import math
from typing import Optional, Tuple
from .parameters import GeneratorParameters, DEFAULT_PARAMS


def create_rotor_core(params: GeneratorParameters = None) -> "cq.Workplane":
    """
    Create the rotor core (laminated steel cylinder).
    
    The rotor core is a hollow cylinder with:
    - Central bore for the shaft
    - Keyway for torque transmission
    - Optional weight reduction holes
    
    Parameters:
        params: Generator parameters (uses defaults if None)
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required for CAD generation")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Main cylinder (hollow)
    core = (
        cq.Workplane("XY")
        # Outer cylinder
        .circle(params.rotor_outer_radius - params.magnet_thickness)
        # Inner bore (shaft hole)
        .circle(params.rotor_inner_radius)
        # Extrude to rotor length
        .extrude(params.rotor_length)
    )
    
    # Add keyway (slot for shaft key)
    keyway = (
        cq.Workplane("XY")
        .center(params.rotor_inner_radius - params.keyway_depth / 2, 0)
        .rect(params.keyway_depth, params.keyway_width)
        .extrude(params.rotor_length)
    )
    core = core.cut(keyway)
    
    # Add weight reduction holes (optional, for balancing)
    # 6 holes equally spaced at 60°
    hole_radius = 8.0  # mm
    hole_distance = 25.0  # mm from center
    
    for i in range(6):
        angle = math.radians(i * 60 + 30)  # Offset by 30°
        x = hole_distance * math.cos(angle)
        y = hole_distance * math.sin(angle)
        
        hole = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(hole_radius)
            .extrude(params.rotor_length)
        )
        core = core.cut(hole)
    
    return core


def create_single_magnet(params: GeneratorParameters = None,
                        pole_number: int = 0) -> "cq.Workplane":
    """
    Create a single arc-shaped permanent magnet.
    
    This creates a curved magnet segment that fits on the rotor surface.
    The magnet is arc-shaped to conform to the rotor's cylindrical surface.
    
    Parameters:
        params: Generator parameters
        pole_number: Which pole position (0 to n_poles-1)
        
    Returns:
        CadQuery Workplane object (single magnet)
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Magnet geometry
    outer_radius = params.rotor_outer_radius
    inner_radius = outer_radius - params.magnet_thickness
    arc_angle = params.magnet_angle_deg
    start_angle = pole_number * params.pole_pitch_deg - arc_angle / 2
    
    # Create arc-shaped magnet using revolution
    # First create the cross-section, then revolve
    magnet = (
        cq.Workplane("XZ")
        # Position at magnet location
        .center(inner_radius + params.magnet_thickness / 2, params.magnet_length / 2)
        # Create rectangular cross-section
        .rect(params.magnet_thickness, params.magnet_length)
        # Revolve around Z axis for arc shape
        .revolve(arc_angle, (0, 0, 0), (0, 0, 1))
        # Rotate to correct pole position
        .rotate((0, 0, 0), (0, 0, 1), start_angle + arc_angle / 2)
    )
    
    # Translate to correct Z position (centered on rotor)
    z_offset = (params.rotor_length - params.magnet_length) / 2
    magnet = magnet.translate((0, 0, z_offset))
    
    return magnet


def create_all_magnets(params: GeneratorParameters = None) -> "cq.Workplane":
    """
    Create all permanent magnets arranged around the rotor.
    
    Magnets alternate N-S-N-S... around the circumference.
    In the 3D model, we use different colors to distinguish polarity.
    
    Parameters:
        params: Generator parameters
        
    Returns:
        CadQuery Assembly or combined Workplane
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Create first magnet as base
    all_magnets = None
    
    for i in range(params.n_poles):
        magnet = create_single_magnet(params, i)
        
        if all_magnets is None:
            all_magnets = magnet
        else:
            all_magnets = all_magnets.union(magnet)
    
    return all_magnets


def create_retention_ring(params: GeneratorParameters = None) -> "cq.Workplane":
    """
    Create a retention ring to hold magnets in place.
    
    At high rotational speeds, centrifugal force can throw off magnets.
    This thin ring (carbon fiber or stainless steel) keeps them secure.
    
    Parameters:
        params: Generator parameters
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    ring_thickness = 0.5  # mm (thin!)
    
    ring = (
        cq.Workplane("XY")
        .circle(params.rotor_outer_radius + ring_thickness)
        .circle(params.rotor_outer_radius)
        .extrude(params.rotor_length)
    )
    
    return ring


def create_balancing_ring(params: GeneratorParameters = None,
                         z_position: float = 0) -> "cq.Workplane":
    """
    Create a balancing ring with holes for adding weights.
    
    These rings at each end of the rotor allow fine-tuning of balance
    by adding small weights to compensate for manufacturing tolerances.
    
    Parameters:
        params: Generator parameters
        z_position: Axial position of the ring
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    ring_height = 5.0  # mm
    ring_outer = params.rotor_outer_radius - params.magnet_thickness
    ring_inner = params.rotor_inner_radius + 10
    hole_radius = 2.5  # mm
    
    # Main ring
    ring = (
        cq.Workplane("XY")
        .workplane(offset=z_position)
        .circle(ring_outer)
        .circle(ring_inner)
        .extrude(ring_height)
    )
    
    # Add balancing holes (12 holes for fine adjustment)
    for i in range(12):
        angle = math.radians(i * 30)
        hole_distance = ring_outer - 10
        x = hole_distance * math.cos(angle)
        y = hole_distance * math.sin(angle)
        
        hole = (
            cq.Workplane("XY")
            .workplane(offset=z_position)
            .center(x, y)
            .circle(hole_radius)
            .extrude(ring_height)
        )
        ring = ring.cut(hole)
    
    return ring


def create_rotor_assembly(params: GeneratorParameters = None,
                         include_magnets: bool = True,
                         include_retention: bool = False) -> "cq.Workplane":
    """
    Create the complete rotor assembly.
    
    Components:
    1. Rotor core (steel)
    2. Permanent magnets (NdFeB)
    3. Balancing rings at each end
    4. Optional: Retention ring
    
    Parameters:
        params: Generator parameters
        include_magnets: Whether to include magnets in the model
        include_retention: Whether to include retention ring
        
    Returns:
        CadQuery Workplane object (complete assembly)
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Start with rotor core
    assembly = create_rotor_core(params)
    
    # Add magnets
    if include_magnets:
        magnets = create_all_magnets(params)
        assembly = assembly.union(magnets)
    
    # Add balancing rings
    ring_front = create_balancing_ring(params, z_position=0)
    ring_back = create_balancing_ring(params, z_position=params.rotor_length - 5)
    assembly = assembly.union(ring_front).union(ring_back)
    
    # Add retention ring
    if include_retention:
        retention = create_retention_ring(params)
        assembly = assembly.union(retention)
    
    return assembly


def export_rotor(params: GeneratorParameters = None,
                filename: str = "rotor.step",
                include_magnets: bool = True) -> str:
    """
    Export rotor assembly to STEP file.
    
    STEP format is industry standard and can be imported into:
    - FreeCAD
    - Fusion 360
    - SolidWorks
    - Any professional CAD software
    
    Parameters:
        params: Generator parameters
        filename: Output filename (should end in .step)
        include_magnets: Whether to include magnets
        
    Returns:
        Path to exported file
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    rotor = create_rotor_assembly(params, include_magnets=include_magnets)
    
    # Export
    cq.exporters.export(rotor, filename)
    print(f"✅ Exported rotor to: {filename}")
    
    return filename


# For direct testing
if __name__ == "__main__":
    if CADQUERY_AVAILABLE:
        print("Creating rotor assembly...")
        rotor = create_rotor_assembly()
        print("Rotor created successfully!")
        
        # Try to show in viewer (if cq-editor is available)
        try:
            from cadquery import cqgi
            show_object(rotor)
        except:
            # Export instead
            export_rotor(filename="output/rotor.step")
    else:
        print("⚠️  CadQuery not installed!")
        print("   Install with: pip install cadquery-ocp")
