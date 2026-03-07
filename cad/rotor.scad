/*
 * PERMANENT MAGNET GENERATOR - ROTOR ASSEMBLY
 * =============================================
 * Complete rotor with magnets and shaft interface
 * 
 * Features:
 * - Optimized pole geometry
 * - Halbach array option
 * - Skewed magnets for anti-cogging
 * - Integrated balancing features
 */

include <params.scad>;

// ============================================================
// ROTOR CORE (LAMINATED STEEL)
// ============================================================

module rotor_core() {
    color(color_rotor_iron)
    difference() {
        // Main cylinder
        cylinder(h = rotor_length, r = rotor_outer_radius - magnet_thickness);
        
        // Shaft bore
        translate([0, 0, -1])
        cylinder(h = rotor_length + 2, r = rotor_inner_radius);
        
        // Keyway
        translate([rotor_inner_radius - keyway_depth, -keyway_width/2, -1])
        cube([keyway_depth + 1, keyway_width, rotor_length + 2]);
        
        // Weight reduction holes (optional, for balancing)
        for (i = [0:5]) {
            rotate([0, 0, i * 60 + 30])
            translate([25, 0, -1])
            cylinder(h = rotor_length + 2, r = 8);
        }
    }
}

// ============================================================
// MAGNET SEGMENT
// ============================================================

module magnet_segment(pole_number) {
    // Determine magnet polarity (alternating N/S)
    is_north = (pole_number % 2 == 0);
    
    // Calculate angular position
    angle = pole_number * pole_pitch_deg;
    
    // Skew: linear twist along length
    skew_per_mm = magnet_skew_deg / rotor_length;
    
    color(is_north ? color_magnet_n : color_magnet_s)
    rotate([0, 0, angle])
    translate([rotor_outer_radius - magnet_thickness, 0, 0])
    
    // Create skewed magnet using hull of top and bottom arcs
    // (Simplified as rectangular for now - can be made arc-shaped)
    for (z = [0 : 1 : magnet_length]) {
        translate([0, 0, z + (rotor_length - magnet_length)/2])
        rotate([0, 0, skew_per_mm * z])
        rotate_extrude(angle = magnet_angle, $fn = 36)
        translate([-rotor_outer_radius + magnet_thickness, 0, 0])
        square([magnet_thickness, 1]);
    }
}

// Alternative: Simple magnet block
module magnet_block(pole_number) {
    is_north = (pole_number % 2 == 0);
    angle = pole_number * pole_pitch_deg;
    
    color(is_north ? color_magnet_n : color_magnet_s)
    rotate([0, 0, angle])
    translate([0, 0, (rotor_length - magnet_length)/2])
    rotate([0, 0, -magnet_angle/2])
    rotate_extrude(angle = magnet_angle, $fn = 72)
    translate([rotor_outer_radius - magnet_thickness, 0, 0])
    square([magnet_thickness, magnet_length]);
}

// ============================================================
// ALL MAGNETS
// ============================================================

module all_magnets() {
    for (i = [0 : n_poles - 1]) {
        magnet_block(i);
    }
}

// ============================================================
// HALBACH ARRAY OPTION
// ============================================================

module halbach_magnet(segment_number, segments_per_pole = 4) {
    // Halbach array segments with rotating magnetization
    pole = floor(segment_number / segments_per_pole);
    segment_in_pole = segment_number % segments_per_pole;
    
    // Angular position
    segment_angle = 360 / (n_poles * segments_per_pole);
    angle = segment_number * segment_angle;
    
    // Magnetization direction (for visualization)
    // In real Halbach, this determines the arrow direction
    mag_direction = (segment_in_pole + 1) * 90;
    
    // Color based on magnetization direction
    mag_colors = [
        [1, 0, 0],      // Outward radial (N)
        [1, 0.5, 0],    // Tangential CW
        [0, 0, 1],      // Inward radial (S)
        [0, 0.5, 1]     // Tangential CCW
    ];
    
    color(mag_colors[segment_in_pole])
    rotate([0, 0, angle])
    translate([0, 0, (rotor_length - magnet_length)/2])
    rotate([0, 0, -segment_angle/2])
    rotate_extrude(angle = segment_angle * 0.95, $fn = 36)
    translate([rotor_outer_radius - magnet_thickness, 0, 0])
    square([magnet_thickness, magnet_length]);
}

module halbach_array(segments_per_pole = 4) {
    total_segments = n_poles * segments_per_pole;
    for (i = [0 : total_segments - 1]) {
        halbach_magnet(i, segments_per_pole);
    }
}

// ============================================================
// MAGNET RETENTION RING
// ============================================================

module retention_ring() {
    color([0.2, 0.2, 0.2])  // Carbon fiber or fiberglass
    difference() {
        cylinder(h = rotor_length, r = rotor_outer_radius + 0.5);
        translate([0, 0, -1])
        cylinder(h = rotor_length + 2, r = rotor_outer_radius - 0.1);
    }
}

// ============================================================
// BALANCING RINGS
// ============================================================

module balancing_ring(z_position) {
    translate([0, 0, z_position])
    color(color_shaft)
    difference() {
        cylinder(h = 5, r = rotor_outer_radius - magnet_thickness);
        translate([0, 0, -1])
        cylinder(h = 7, r = rotor_inner_radius + 10);
        
        // Balancing holes (for adding weight)
        for (i = [0:11]) {
            rotate([0, 0, i * 30])
            translate([rotor_outer_radius - magnet_thickness - 10, 0, -1])
            cylinder(h = 7, r = 2.5);
        }
    }
}

// ============================================================
// COMPLETE ROTOR ASSEMBLY
// ============================================================

module rotor_assembly(use_halbach = false) {
    union() {
        // Core
        rotor_core();
        
        // Magnets
        if (use_halbach) {
            halbach_array(4);
        } else {
            all_magnets();
        }
        
        // Retention ring (optional, for high-speed)
        // retention_ring();
        
        // Balancing rings at each end
        balancing_ring(0);
        balancing_ring(rotor_length - 5);
    }
}

// ============================================================
// RENDER
// ============================================================

// Show rotor (toggle between standard and Halbach)
use_halbach = false;  // Set true for Halbach array

if (show_cross_section) {
    difference() {
        rotor_assembly(use_halbach);
        translate([0, -200, -1])
        cube([200, 400, rotor_length + 10]);
    }
} else {
    rotor_assembly(use_halbach);
}
