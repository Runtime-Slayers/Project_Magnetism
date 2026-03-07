/*
 * PERMANENT MAGNET GENERATOR - DESIGN PARAMETERS
 * ================================================
 * Central parameter file for all CAD components
 * 
 * UNITS: All dimensions in millimeters (mm)
 * 
 * To customize your generator, modify these values.
 * The 3D models will automatically update.
 */

// ============================================================
// MAIN DESIGN PARAMETERS
// ============================================================

// Number of magnetic poles (must be even)
n_poles = 12;

// Number of stator slots (typically 1.5× poles for 3-phase)
n_slots = 18;

// Number of phases
n_phases = 3;

// ============================================================
// ROTOR DIMENSIONS
// ============================================================

// Rotor outer radius (where magnets are mounted)
rotor_outer_radius = 50;  // mm

// Rotor inner radius (shaft bore)
rotor_inner_radius = 15;  // mm

// Rotor active length (axial)
rotor_length = 100;  // mm

// Rotor back-iron thickness
rotor_back_iron = 8;  // mm

// ============================================================
// MAGNET DIMENSIONS
// ============================================================

// Magnet thickness (radial direction)
magnet_thickness = 5;  // mm

// Magnet arc ratio (0.5-0.9, fraction of pole pitch)
magnet_arc_ratio = 0.85;

// Magnet length (axial, should be close to rotor_length)
magnet_length = 96;  // mm

// Magnet skew angle (electrical degrees, for anti-cogging)
magnet_skew_deg = 15;  // degrees

// ============================================================
// STATOR DIMENSIONS
// ============================================================

// Air gap between rotor and stator
air_gap = 1.5;  // mm (critical for performance!)

// Stator inner radius (calculated)
stator_inner_radius = rotor_outer_radius + air_gap;

// Stator outer radius
stator_outer_radius = 80;  // mm

// Stator yoke thickness (back iron)
stator_yoke = 10;  // mm

// Stator tooth width (at narrowest point)
tooth_width = 5;  // mm

// Slot opening width
slot_opening = 2;  // mm

// Slot depth
slot_depth = stator_outer_radius - stator_inner_radius - stator_yoke - 2;

// ============================================================
// SHAFT DIMENSIONS
// ============================================================

// Shaft diameter
shaft_diameter = 20;  // mm

// Shaft total length
shaft_length = 200;  // mm

// Keyway dimensions
keyway_width = 6;
keyway_depth = 3;

// ============================================================
// WINDING PARAMETERS
// ============================================================

// Wire diameter (AWG or mm)
wire_diameter = 1.0;  // mm

// Number of turns per coil
turns_per_coil = 50;

// Coil span (slots)
coil_span = n_slots / n_poles;  // Should equal 1.5 for 12P/18S

// ============================================================
// HOUSING DIMENSIONS
// ============================================================

// Housing wall thickness
housing_wall = 5;  // mm

// Housing outer diameter
housing_outer_diameter = 2 * stator_outer_radius + 2 * housing_wall;

// End cap thickness
end_cap_thickness = 10;  // mm

// Bearing housing diameter
bearing_housing_od = 40;  // mm
bearing_housing_id = 22;  // mm (bearing OD)

// Cooling fins
fin_count = 12;
fin_height = 15;
fin_thickness = 3;

// ============================================================
// BEARING PARAMETERS
// ============================================================

// Bearing type: 6004-2RS equivalent
bearing_od = 42;
bearing_id = 20;
bearing_width = 12;

// ============================================================
// CALCULATED PARAMETERS (DO NOT MODIFY)
// ============================================================

// Pole pitch (angular)
pole_pitch_deg = 360 / n_poles;
pole_pitch_rad = pole_pitch_deg * PI / 180;

// Slot pitch (angular)
slot_pitch_deg = 360 / n_slots;
slot_pitch_rad = slot_pitch_deg * PI / 180;

// Magnet angular extent
magnet_angle = magnet_arc_ratio * pole_pitch_deg;

// Effective air gap (including magnet)
effective_air_gap = air_gap + magnet_thickness / 4;

// Cogging order (LCM of poles and slots)
// Note: OpenSCAD doesn't have LCM, this is for reference
// cogging_order = 36 for 12P/18S

// ============================================================
// MATERIAL COLORS (for visualization)
// ============================================================

color_rotor_iron = [0.3, 0.3, 0.35];      // Dark steel
color_stator_iron = [0.4, 0.4, 0.45];     // Lighter steel
color_magnet_n = [1.0, 0.0, 0.0];         // Red for North
color_magnet_s = [0.0, 0.0, 1.0];         // Blue for South
color_copper = [0.8, 0.5, 0.2];           // Copper windings
color_shaft = [0.5, 0.5, 0.55];           // Steel shaft
color_housing = [0.6, 0.6, 0.65];         // Aluminum housing
color_bearing = [0.4, 0.4, 0.4];          // Bearing steel

// ============================================================
// QUALITY SETTINGS
// ============================================================

// Circle resolution ($fn)
$fn = 100;  // Increase for smoother circles (slower render)

// Minimum feature size
min_feature = 0.1;  // mm

// ============================================================
// DEBUG FLAGS
// ============================================================

// Show cross-section
show_cross_section = false;

// Show wireframe
show_wireframe = false;

// Exploded view distance
explode_distance = 0;  // Set > 0 for exploded view
