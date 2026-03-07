"""
CAD Module for Permanent Magnet Generator
==========================================

Using CadQuery and build123d for parametric 3D modeling.

We use Python-based CAD (CadQuery) instead of OpenSCAD because:
1. Errors can be debugged interactively in Python
2. Parameters come directly from our physics calculations
3. STEP export works with all professional CAD software
4. Full programming language with numpy, scipy integration

The old .scad files are kept for reference but are deprecated.

Quick Start:
-----------
    from cad.generator_assembly import export_generator_assembly
    export_generator_assembly(output_dir="output")

This creates:
- output/generator_assembly.step (complete model)
- output/rotor.step
- output/stator.step
- output/shaft.step
- output/housing.step
- ...and more individual components

View STEP files in FreeCAD, Fusion 360, or any CAD software.
"""

# Import everything for easy access
try:
    from .parameters import GeneratorParameters, DEFAULT_PARAMS
    from .rotor_cad import (
        create_rotor_core,
        create_single_magnet,
        create_all_magnets,
        create_rotor_assembly,
        export_rotor,
    )
    from .stator_cad import (
        create_stator_core,
        create_winding_in_slot,
        create_all_windings,
        create_stator_assembly,
        export_stator,
        calculate_slot_fill,
    )
    from .generator_assembly import (
        create_shaft,
        create_bearing,
        create_housing,
        create_end_cap,
        create_cooling_fan,
        create_generator_assembly,
        export_generator_assembly,
        get_bill_of_materials,
    )
    
    CADQUERY_AVAILABLE = True

except ImportError as e:
    CADQUERY_AVAILABLE = False
    print(f"⚠️  CadQuery not available: {e}")
    print("   Install with: pip install cadquery-ocp")
    print("   The simulation modules work without CadQuery.")

