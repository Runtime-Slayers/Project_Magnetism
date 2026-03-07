"""
PERMANENT MAGNET GENERATOR - STATOR CAD MODEL
==============================================
Creates the stator assembly using CadQuery.

The stator consists of:
1. Stator core (laminated silicon steel) - outer ring with teeth
2. Stator teeth - protrusions that concentrate magnetic flux
3. Slots - spaces between teeth where copper windings go
4. Windings - copper wire coils (represented as solid blocks)
5. Slot liners - insulation between windings and steel core

KEY RELATIONSHIPS (for anti-cogging):
=====================================
- The ratio of poles (rotor magnets) to slots (stator teeth) 
  determines cogging torque behavior
- Best ratios use LCM optimization: more common multiples = lower cogging
- Example: 12 poles, 18 slots → LCM = 36, very smooth operation
- See: simulation/cogging_analysis.py for the math

CadQuery Documentation: https://cadquery.readthedocs.io/
"""

try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError:
    CADQUERY_AVAILABLE = False
    print("CadQuery not installed. Install with: pip install cadquery-ocp")

import math
from typing import Optional, List, Tuple
from .parameters import GeneratorParameters, DEFAULT_PARAMS


def create_stator_core(params: GeneratorParameters = None) -> "cq.Workplane":
    """
    Create the stator core with teeth and slots.
    
    The stator core is a hollow cylinder with:
    - Outer ring (back iron) for flux return path
    - Inner teeth that face the rotor
    - Slots between teeth for windings
    
    This is the most complex part to manufacture in a real generator.
    It's made from thin (0.35mm) laminated silicon steel sheets to
    reduce eddy current losses.
    
    Parameters:
        params: Generator parameters (uses defaults if None)
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required for CAD generation")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # ===== GEOMETRY CALCULATIONS =====
    # Back iron (outer ring)
    back_iron_outer = params.stator_outer_radius
    back_iron_inner = params.stator_outer_radius - params.back_iron_thickness
    
    # Tooth geometry
    tooth_tip_inner = params.stator_inner_radius  # Faces the air gap
    tooth_root = back_iron_inner  # Connects to back iron
    tooth_width_deg = params.tooth_width_deg
    slot_opening_deg = params.slot_angle_deg - tooth_width_deg
    
    # ===== CREATE BACK IRON RING =====
    core = (
        cq.Workplane("XY")
        .circle(back_iron_outer)
        .circle(back_iron_inner)
        .extrude(params.stator_length)
    )
    
    # ===== CREATE TEETH =====
    # Each tooth is an arc-shaped extrusion from back iron to air gap
    for i in range(params.n_slots):
        tooth_center_angle = i * params.slot_angle_deg
        half_width = tooth_width_deg / 2
        
        # Create tooth cross-section and revolve
        tooth = (
            cq.Workplane("XZ")
            .center((tooth_root + tooth_tip_inner) / 2, params.stator_length / 2)
            .rect(tooth_root - tooth_tip_inner, params.stator_length)
            .revolve(tooth_width_deg, (0, 0, 0), (0, 0, 1))
            .rotate((0, 0, 0), (0, 0, 1), tooth_center_angle - half_width + tooth_width_deg / 2)
        )
        
        core = core.union(tooth)
    
    return core


def create_slot_profile(params: GeneratorParameters = None,
                       slot_number: int = 0) -> "cq.Workplane":
    """
    Create a single slot for the stator.
    
    The slot shape is critical for:
    1. Winding fit (how much copper we can pack in)
    2. Cooling (wider slots = better airflow)
    3. Cogging (slot opening width affects torque ripple)
    
    Parameters:
        params: Generator parameters
        slot_number: Which slot (0 to n_slots-1)
        
    Returns:
        CadQuery Workplane object representing the void space
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Slot geometry
    slot_center_angle = slot_number * params.slot_angle_deg + params.slot_angle_deg / 2
    slot_opening_deg = params.slot_angle_deg - params.tooth_width_deg
    
    # Slot depth (from air gap to back iron)
    slot_inner = params.stator_inner_radius
    slot_outer = params.stator_outer_radius - params.back_iron_thickness
    
    # Create slot as arc-shaped cutout
    slot = (
        cq.Workplane("XZ")
        .center((slot_outer + slot_inner) / 2, params.stator_length / 2)
        .rect(slot_outer - slot_inner, params.stator_length)
        .revolve(slot_opening_deg, (0, 0, 0), (0, 0, 1))
        .rotate((0, 0, 0), (0, 0, 1), slot_center_angle - slot_opening_deg / 2)
    )
    
    return slot


def create_winding_in_slot(params: GeneratorParameters = None,
                          slot_number: int = 0,
                          fill_factor: float = 0.4) -> "cq.Workplane":
    """
    Create copper winding representation for a slot.
    
    Real windings are complex coils of insulated wire, but for
    visualization we represent them as solid blocks filling the slot.
    
    The fill factor (typically 0.3-0.5) represents how much of the
    slot area is actually copper vs air/insulation.
    
    Parameters:
        params: Generator parameters
        slot_number: Which slot (0 to n_slots-1)
        fill_factor: Ratio of slot filled with copper (default 0.4 = 40%)
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Winding geometry (slightly smaller than slot)
    slot_center_angle = slot_number * params.slot_angle_deg + params.slot_angle_deg / 2
    slot_opening_deg = params.slot_angle_deg - params.tooth_width_deg
    winding_angle = slot_opening_deg * 0.8  # Leave some room
    
    # Radial dimensions
    slot_inner = params.stator_inner_radius + 1.0  # 1mm clearance from air gap
    slot_outer = params.stator_outer_radius - params.back_iron_thickness - 1.0
    winding_thickness = (slot_outer - slot_inner) * fill_factor
    winding_inner = slot_inner + 0.5  # Slot liner space
    winding_outer = winding_inner + winding_thickness
    
    # End winding overhang
    overhang = params.stator_length + 15  # 15mm per side
    
    winding = (
        cq.Workplane("XZ")
        .center((winding_outer + winding_inner) / 2, overhang / 2)
        .rect(winding_outer - winding_inner, overhang)
        .revolve(winding_angle, (0, 0, 0), (0, 0, 1))
        .rotate((0, 0, 0), (0, 0, 1), slot_center_angle - winding_angle / 2)
    )
    
    # Shift to center on stator
    z_offset = (params.stator_length - overhang) / 2 + 7.5
    winding = winding.translate((0, 0, z_offset))
    
    return winding


def create_all_windings(params: GeneratorParameters = None) -> "cq.Workplane":
    """
    Create all windings for all slots.
    
    In a real 3-phase generator, windings are connected in a 
    specific pattern (e.g., distributed or concentrated winding).
    Here we just show them as separate blocks per slot.
    
    Parameters:
        params: Generator parameters
        
    Returns:
        CadQuery Workplane object (all windings combined)
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    all_windings = None
    
    for i in range(params.n_slots):
        winding = create_winding_in_slot(params, i)
        
        if all_windings is None:
            all_windings = winding
        else:
            all_windings = all_windings.union(winding)
    
    return all_windings


def create_slot_liner(params: GeneratorParameters = None,
                     slot_number: int = 0) -> "cq.Workplane":
    """
    Create slot liner (insulation) for a slot.
    
    Slot liners are thin sheets of insulating material (Nomex, Kapton)
    that prevent electrical contact between copper and steel.
    
    They're essential for safety and preventing short circuits.
    
    Parameters:
        params: Generator parameters
        slot_number: Which slot
        
    Returns:
        CadQuery Workplane object
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    liner_thickness = 0.3  # mm (typical Nomex thickness)
    
    # Same geometry as slot but slightly smaller
    slot_center_angle = slot_number * params.slot_angle_deg + params.slot_angle_deg / 2
    slot_opening_deg = params.slot_angle_deg - params.tooth_width_deg
    
    slot_inner = params.stator_inner_radius + 0.5
    slot_outer = params.stator_outer_radius - params.back_iron_thickness - 0.5
    
    # Outer shell of liner
    outer_liner = (
        cq.Workplane("XZ")
        .center((slot_outer + slot_inner) / 2, params.stator_length / 2)
        .rect(slot_outer - slot_inner, params.stator_length)
        .revolve(slot_opening_deg, (0, 0, 0), (0, 0, 1))
        .rotate((0, 0, 0), (0, 0, 1), slot_center_angle - slot_opening_deg / 2)
    )
    
    # Inner cutout (liner is hollow)
    inner_slot_inner = slot_inner + liner_thickness
    inner_slot_outer = slot_outer - liner_thickness
    inner_liner = (
        cq.Workplane("XZ")
        .center((inner_slot_outer + inner_slot_inner) / 2, params.stator_length / 2)
        .rect(inner_slot_outer - inner_slot_inner - liner_thickness * 2, params.stator_length)
        .revolve(slot_opening_deg - 0.5, (0, 0, 0), (0, 0, 1))
        .rotate((0, 0, 0), (0, 0, 1), slot_center_angle - (slot_opening_deg - 0.5) / 2)
    )
    
    liner = outer_liner.cut(inner_liner)
    
    return liner


def create_stator_assembly(params: GeneratorParameters = None,
                          include_windings: bool = True,
                          include_liners: bool = False) -> "cq.Workplane":
    """
    Create the complete stator assembly.
    
    Components:
    1. Stator core (laminated steel with teeth and slots)
    2. Copper windings in each slot
    3. Optional: Slot liners for insulation
    
    Parameters:
        params: Generator parameters
        include_windings: Whether to show copper windings
        include_liners: Whether to show slot liners
        
    Returns:
        CadQuery Workplane object (complete assembly)
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    if params is None:
        params = DEFAULT_PARAMS
    
    # Start with stator core
    assembly = create_stator_core(params)
    
    # Add windings
    if include_windings:
        windings = create_all_windings(params)
        assembly = assembly.union(windings)
    
    # Add slot liners
    if include_liners:
        for i in range(params.n_slots):
            liner = create_slot_liner(params, i)
            assembly = assembly.union(liner)
    
    return assembly


def export_stator(params: GeneratorParameters = None,
                 filename: str = "stator.step",
                 include_windings: bool = True) -> str:
    """
    Export stator assembly to STEP file.
    
    STEP format is industry standard for CAD exchange.
    
    Parameters:
        params: Generator parameters
        filename: Output filename (should end in .step)
        include_windings: Whether to include copper windings
        
    Returns:
        Path to exported file
    """
    if not CADQUERY_AVAILABLE:
        raise ImportError("CadQuery is required")
    
    stator = create_stator_assembly(params, include_windings=include_windings)
    
    cq.exporters.export(stator, filename)
    print(f"✅ Exported stator to: {filename}")
    
    return filename


def calculate_slot_fill(params: GeneratorParameters = None,
                       wire_diameter: float = 0.8,
                       num_turns: int = 50) -> dict:
    """
    Calculate how well the windings fill the slot.
    
    This is important for thermal design - more copper = more heat,
    but also more power output capability.
    
    Parameters:
        params: Generator parameters
        wire_diameter: Copper wire diameter in mm
        num_turns: Number of turns per slot
        
    Returns:
        Dictionary with fill factor analysis
    """
    if params is None:
        params = DEFAULT_PARAMS
    
    # Calculate slot area (approximate as rectangular)
    slot_opening_deg = params.slot_angle_deg - params.tooth_width_deg
    slot_depth = params.stator_outer_radius - params.back_iron_thickness - params.stator_inner_radius
    slot_width_at_mid = 2 * math.pi * (params.stator_inner_radius + slot_depth / 2) * (slot_opening_deg / 360)
    slot_area = slot_depth * slot_width_at_mid
    
    # Calculate wire area
    wire_area = math.pi * (wire_diameter / 2) ** 2
    total_wire_area = wire_area * num_turns
    
    # Fill factor
    fill_factor = total_wire_area / slot_area
    
    return {
        "slot_area_mm2": slot_area,
        "wire_diameter_mm": wire_diameter,
        "num_turns": num_turns,
        "total_wire_area_mm2": total_wire_area,
        "fill_factor": fill_factor,
        "fill_percent": fill_factor * 100,
        "is_feasible": fill_factor < 0.6,  # Above 60% is very hard to wind
        "recommendation": "Good" if fill_factor < 0.45 else ("Tight" if fill_factor < 0.55 else "Too full - reduce turns or wire size")
    }


# For direct testing
if __name__ == "__main__":
    if CADQUERY_AVAILABLE:
        print("Creating stator assembly...")
        stator = create_stator_assembly()
        print("Stator created successfully!")
        
        # Calculate fill factor
        fill_info = calculate_slot_fill()
        print(f"\nSlot Fill Analysis:")
        print(f"  Slot area: {fill_info['slot_area_mm2']:.1f} mm²")
        print(f"  Fill factor: {fill_info['fill_percent']:.1f}%")
        print(f"  Recommendation: {fill_info['recommendation']}")
        
        try:
            from cadquery import cqgi
            show_object(stator)
        except:
            export_stator(filename="output/stator.step")
    else:
        print("⚠️  CadQuery not installed!")
        print("   Install with: pip install cadquery-ocp")
