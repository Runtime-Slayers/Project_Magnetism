/*
 * PERMANENT MAGNET GENERATOR - STATOR ASSEMBLY
 * =============================================
 * Complete stator with slots, teeth, and windings
 * 
 * Features:
 * - Optimized slot geometry for low cogging
 * - 3-phase distributed winding
 * - Semi-closed slots
 * - Integrated cooling channels
 */

include <params.scad>;

// ============================================================
// STATOR CORE (LAMINATED SILICON STEEL)
// ============================================================

module stator_core() {
    color(color_stator_iron)
    difference() {
        // Outer cylinder (yoke)
        cylinder(h = rotor_length, r = stator_outer_radius);
        
        // Inner bore
        translate([0, 0, -1])
        cylinder(h = rotor_length + 2, r = stator_inner_radius);
        
        // Slots
        for (i = [0 : n_slots - 1]) {
            rotate([0, 0, i * slot_pitch_deg])
            stator_slot();
        }
    }
}

// ============================================================
// INDIVIDUAL SLOT PROFILE
// ============================================================

module stator_slot() {
    // Semi-closed slot design for low cogging
    
    // Slot parameters
    slot_width_opening = slot_opening;
    slot_width_body = (2 * PI * (stator_inner_radius + slot_depth/2) / n_slots) - tooth_width;
    slot_radius = stator_inner_radius;
    
    translate([0, 0, -1])
    linear_extrude(height = rotor_length + 2) {
        union() {
            // Slot opening (narrow)
            translate([slot_radius + 0.5, -slot_width_opening/2, 0])
            square([2, slot_width_opening]);
            
            // Slot body (trapezoidal)
            translate([slot_radius + 2, 0, 0])
            polygon([
                [-0.1, -slot_width_opening/2],
                [slot_depth, -slot_width_body/2],
                [slot_depth, slot_width_body/2],
                [-0.1, slot_width_opening/2]
            ]);
            
            // Round bottom
            translate([slot_radius + slot_depth, 0, 0])
            circle(r = slot_width_body/2);
        }
    }
}

// ============================================================
// STATOR TOOTH
// ============================================================

module stator_tooth_profile() {
    // Used for visualization
    tooth_base_width = 2 * PI * stator_inner_radius / n_slots - slot_opening;
    tooth_tip_width = slot_opening / 2;
    
    polygon([
        [stator_inner_radius, -tooth_base_width/2],
        [stator_inner_radius + slot_depth - 2, -tooth_base_width/2],
        [stator_inner_radius + slot_depth, -tooth_tip_width/2],
        [stator_inner_radius + slot_depth, tooth_tip_width/2],
        [stator_inner_radius + slot_depth - 2, tooth_base_width/2],
        [stator_inner_radius, tooth_base_width/2]
    ]);
}

// ============================================================
// WINDING COIL (SIMPLIFIED REPRESENTATION)
// ============================================================

module winding_coil(slot_number) {
    // Determine phase from slot number
    phase = slot_number % n_phases;
    
    // Phase colors
    phase_colors = [
        [1, 0, 0],    // Phase A - Red
        [1, 1, 0],    // Phase B - Yellow
        [0, 0, 1]     // Phase C - Blue
    ];
    
    // Slot position
    angle = slot_number * slot_pitch_deg;
    
    // Coil in slot
    slot_width_body = (2 * PI * (stator_inner_radius + slot_depth/2) / n_slots) - tooth_width;
    
    color(phase_colors[phase], 0.8)
    rotate([0, 0, angle])
    translate([stator_inner_radius + 4, 0, 0])
    linear_extrude(height = rotor_length)
    translate([0, -slot_width_body/4, 0])
    square([slot_depth - 8, slot_width_body/2]);
}

// ============================================================
// ALL WINDINGS
// ============================================================

module all_windings() {
    for (i = [0 : n_slots - 1]) {
        winding_coil(i);
    }
}

// ============================================================
// END WINDINGS (SIMPLIFIED)
// ============================================================

module end_windings(z_offset, direction = 1) {
    for (i = [0 : n_slots - 1]) {
        phase = i % n_phases;
        phase_colors = [[1,0,0], [1,1,0], [0,0,1]];
        
        color(phase_colors[phase], 0.6)
        rotate([0, 0, i * slot_pitch_deg])
        translate([stator_inner_radius + slot_depth/2, 0, z_offset])
        rotate([90 * direction, 0, 0])
        rotate_extrude(angle = slot_pitch_deg * 1.5, $fn = 20)
        translate([15, 0, 0])
        circle(r = 3);
    }
}

// ============================================================
// SLOT WEDGE (TO HOLD WINDINGS)
// ============================================================

module slot_wedge(slot_number) {
    angle = slot_number * slot_pitch_deg;
    
    color([0.8, 0.8, 0.7])  // Insulation color
    rotate([0, 0, angle])
    translate([stator_inner_radius + 1, 0, 1])
    linear_extrude(height = rotor_length - 2)
    translate([0, -slot_opening/2, 0])
    square([2, slot_opening]);
}

module all_slot_wedges() {
    for (i = [0 : n_slots - 1]) {
        slot_wedge(i);
    }
}

// ============================================================
// STATOR HOUSING INTERFACE FEATURES
// ============================================================

module stator_mounting_features() {
    // Keyway for locating in housing
    color(color_stator_iron)
    translate([stator_outer_radius - 3, -5, 0])
    cube([3.1, 10, rotor_length]);
}

// ============================================================
// COOLING CHANNELS (OPTIONAL)
// ============================================================

module cooling_channels() {
    for (i = [0 : 5]) {
        rotate([0, 0, i * 60 + 30])
        translate([stator_outer_radius - 8, 0, -1])
        cylinder(h = rotor_length + 2, r = 4);
    }
}

module stator_with_cooling() {
    difference() {
        stator_core();
        cooling_channels();
    }
}

// ============================================================
// COMPLETE STATOR ASSEMBLY
// ============================================================

module stator_assembly(show_windings = true, with_cooling = false) {
    union() {
        // Core (with or without cooling)
        if (with_cooling) {
            stator_with_cooling();
        } else {
            stator_core();
        }
        
        // Windings
        if (show_windings) {
            all_windings();
            end_windings(rotor_length, 1);
            end_windings(0, -1);
            all_slot_wedges();
        }
        
        // Mounting feature
        stator_mounting_features();
    }
}

// ============================================================
// RENDER
// ============================================================

show_windings = true;
with_cooling = true;

if (show_cross_section) {
    difference() {
        stator_assembly(show_windings, with_cooling);
        translate([0, -200, -1])
        cube([200, 400, rotor_length + 10]);
    }
} else {
    stator_assembly(show_windings, with_cooling);
}
