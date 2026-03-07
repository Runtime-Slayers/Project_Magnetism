/*
 * PERMANENT MAGNET GENERATOR - COMPLETE ASSEMBLY
 * ================================================
 * Full generator with all components:
 * - Rotor with magnets
 * - Stator with windings
 * - Shaft
 * - Bearings
 * - Housing with cooling
 * - End plates
 * 
 * This is the main file to render for a complete view.
 */

include <params.scad>;
use <rotor.scad>;
use <stator.scad>;

// ============================================================
// SHAFT
// ============================================================

module shaft() {
    color(color_shaft)
    difference() {
        union() {
            // Main shaft body
            translate([0, 0, -shaft_length/2 + rotor_length/2])
            cylinder(h = shaft_length, r = shaft_diameter/2);
            
            // Bearing seats (slightly smaller)
            translate([0, 0, -30])
            cylinder(h = 20, r = bearing_id/2);
            
            translate([0, 0, rotor_length + 10])
            cylinder(h = 20, r = bearing_id/2);
        }
        
        // Keyway along rotor length
        translate([shaft_diameter/2 - keyway_depth, -keyway_width/2, -1])
        cube([keyway_depth + 1, keyway_width, rotor_length + 2]);
        
        // Drive end keyway
        translate([shaft_diameter/2 - keyway_depth, -keyway_width/2, rotor_length + 30])
        cube([keyway_depth + 1, keyway_width, 30]);
    }
}

// ============================================================
// BEARING
// ============================================================

module bearing() {
    color(color_bearing) {
        difference() {
            // Outer race
            cylinder(h = bearing_width, r = bearing_od/2);
            
            // Inner race
            translate([0, 0, -1])
            cylinder(h = bearing_width + 2, r = bearing_id/2);
        }
        
        // Balls (simplified)
        for (i = [0:7]) {
            rotate([0, 0, i * 45])
            translate([(bearing_od + bearing_id)/4, 0, bearing_width/2])
            sphere(r = (bearing_od - bearing_id)/8);
        }
    }
}

// ============================================================
// HOUSING MAIN BODY
// ============================================================

module housing_body() {
    color(color_housing)
    difference() {
        union() {
            // Main cylindrical housing
            cylinder(h = rotor_length + 20, r = housing_outer_diameter/2);
            
            // Cooling fins
            for (i = [0 : fin_count - 1]) {
                rotate([0, 0, i * 360/fin_count])
                translate([housing_outer_diameter/2, -fin_thickness/2, 0])
                cube([fin_height, fin_thickness, rotor_length + 20]);
            }
            
            // Mounting feet
            for (i = [-1, 1]) {
                translate([i * (housing_outer_diameter/2 - 10), 0, -10])
                cube([30, 40, 10], center = true);
            }
        }
        
        // Stator bore
        translate([0, 0, 10])
        cylinder(h = rotor_length + 1, r = stator_outer_radius + 0.1);
        
        // Through bore for bearing housings
        translate([0, 0, -1])
        cylinder(h = rotor_length + 22, r = bearing_housing_od/2 + 5);
        
        // Mounting holes in feet
        for (i = [-1, 1]) {
            for (j = [-1, 1]) {
                translate([i * (housing_outer_diameter/2 - 10), j * 12, -15])
                cylinder(h = 20, r = 4);
            }
        }
        
        // Terminal box cutout
        translate([0, housing_outer_diameter/2, rotor_length/2 + 10])
        cube([40, 30, 60], center = true);
    }
}

// ============================================================
// END PLATES (DRIVE END AND NON-DRIVE END)
// ============================================================

module end_plate(is_drive_end = true) {
    color(color_housing)
    difference() {
        // Plate body
        cylinder(h = end_cap_thickness, r = housing_outer_diameter/2);
        
        // Center bore for bearing housing
        translate([0, 0, -1])
        cylinder(h = end_cap_thickness + 2, r = bearing_housing_od/2);
        
        // Mounting bolt holes
        for (i = [0:5]) {
            rotate([0, 0, i * 60 + 30])
            translate([housing_outer_diameter/2 - 15, 0, -1])
            cylinder(h = end_cap_thickness + 2, r = 4);
        }
        
        // Ventilation holes
        for (i = [0:11]) {
            rotate([0, 0, i * 30])
            translate([housing_outer_diameter/4, 0, -1])
            cylinder(h = end_cap_thickness + 2, r = 5);
        }
        
        // Shaft seal groove
        translate([0, 0, end_cap_thickness - 2])
        difference() {
            cylinder(h = 2.1, r = bearing_housing_od/2 + 5);
            translate([0, 0, -0.1])
            cylinder(h = 2.3, r = bearing_housing_od/2);
        }
    }
    
    // Bearing housing boss
    color(color_housing)
    difference() {
        cylinder(h = 15, r = bearing_housing_od/2);
        translate([0, 0, -1])
        cylinder(h = 17, r = bearing_housing_id/2);
    }
    
    // Grease fitting boss (drive end only)
    if (is_drive_end) {
        translate([bearing_housing_od/2 + 5, 0, 5])
        rotate([0, 90, 0])
        color(color_housing)
        cylinder(h = 10, r = 3);
    }
}

// ============================================================
// TERMINAL BOX
// ============================================================

module terminal_box() {
    color(color_housing)
    translate([0, housing_outer_diameter/2 + 10, rotor_length/2 + 10])
    difference() {
        cube([50, 30, 70], center = true);
        translate([0, 5, 0])
        cube([44, 25, 64], center = true);
    }
    
    // Cable gland holes
    translate([0, housing_outer_diameter/2 + 25, rotor_length/2 - 20])
    rotate([90, 0, 0])
    color([0.2, 0.2, 0.2])
    cylinder(h = 10, r = 8);
}

// ============================================================
// OUTPUT COUPLING
// ============================================================

module output_coupling() {
    translate([0, 0, rotor_length + 35])
    color([0.3, 0.3, 0.3]) {
        difference() {
            cylinder(h = 25, r = 25);
            translate([0, 0, -1])
            cylinder(h = 27, r = shaft_diameter/2);
            
            // Keyway
            translate([shaft_diameter/2 - keyway_depth, -keyway_width/2, -1])
            cube([keyway_depth + 1, keyway_width, 27]);
            
            // Clamping slot
            translate([-2, 20, -1])
            cube([4, 10, 27]);
        }
        
        // Clamping bolt
        translate([0, 28, 12.5])
        rotate([90, 0, 0])
        cylinder(h = 15, r = 3);
    }
}

// ============================================================
// COMPLETE GENERATOR ASSEMBLY
// ============================================================

module generator_assembly(explode = 0) {
    // Shaft
    translate([0, 0, explode * 0.2])
    shaft();
    
    // Rotor (mounted on shaft)
    translate([0, 0, 0])
    rotor_assembly(use_halbach = false);
    
    // Stator (in housing)
    translate([0, 0, explode * 0.5])
    translate([0, 0, 0])
    stator_assembly(show_windings = true, with_cooling = true);
    
    // Housing body
    translate([0, 0, explode * 1.0])
    translate([0, 0, -10])
    housing_body();
    
    // Non-drive end plate and bearing
    translate([0, 0, -explode * 0.3]) {
        translate([0, 0, -end_cap_thickness - 5])
        end_plate(is_drive_end = false);
        
        translate([0, 0, -20])
        bearing();
    }
    
    // Drive end plate and bearing
    translate([0, 0, explode * 0.3]) {
        translate([0, 0, rotor_length + 15])
        end_plate(is_drive_end = true);
        
        translate([0, 0, rotor_length + 15])
        bearing();
    }
    
    // Terminal box
    translate([0, 0, explode * 0.5])
    terminal_box();
    
    // Output coupling
    translate([0, 0, explode * 0.5])
    output_coupling();
}

// ============================================================
// ASSEMBLY VIEWS
// ============================================================

module show_cross_section_assembly() {
    difference() {
        generator_assembly(0);
        translate([0, -200, -100])
        cube([400, 400, 400]);
    }
}

module show_exploded_view() {
    generator_assembly(50);  // 50mm explosion distance
}

// ============================================================
// RENDER OPTIONS
// ============================================================

// Select view mode:
view_mode = "assembled";  // "assembled", "cross_section", "exploded"

if (view_mode == "cross_section") {
    show_cross_section_assembly();
} else if (view_mode == "exploded") {
    show_exploded_view();
} else {
    generator_assembly(explode_distance);
}

// ============================================================
// BILL OF MATERIALS (as comments)
// ============================================================

/*
BILL OF MATERIALS - PMG Generator
==================================

1. Rotor Assembly
   - Rotor core (laminated silicon steel)    : 1 pc
   - NdFeB N52 magnets (arc segments)        : 12 pcs
   - Retention ring (carbon fiber)           : 1 pc
   - Rotor key (steel)                       : 1 pc

2. Stator Assembly
   - Stator core (laminated silicon steel)   : 1 pc
   - Magnet wire (copper, AWG 18)            : ~50m
   - Slot wedges (fiberglass)                : 18 pcs
   - Slot liner (Nomex)                      : 18 pcs
   - Phase insulation                        : 3 sets

3. Mechanical Components
   - Shaft (4140 steel)                      : 1 pc
   - Bearings (6004-2RS)                     : 2 pcs
   - Bearing housing O-rings                 : 2 pcs
   - Shaft seal (lip seal)                   : 2 pcs
   - Shaft key                               : 2 pcs

4. Housing
   - Main housing (cast aluminum)            : 1 pc
   - Drive end plate (cast aluminum)         : 1 pc
   - Non-drive end plate (cast aluminum)     : 1 pc
   - Terminal box                            : 1 pc
   - Mounting bolts M8x25                    : 12 pcs
   - Housing feet bolts M10                  : 4 pcs

5. Electrical
   - Terminal block                          : 1 pc
   - Cable glands PG16                       : 2 pcs
   - Phase leads                             : 3 pcs
   - Ground terminal                         : 1 pc

6. Miscellaneous
   - Output coupling                         : 1 pc
   - Grease fittings                         : 2 pcs
   - Nameplate                               : 1 pc
   - Hardware kit                            : 1 set

*/
