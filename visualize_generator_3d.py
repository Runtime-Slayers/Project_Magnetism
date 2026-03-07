"""
3D GENERATOR VISUALIZATION
===========================
Creates a 3D interactive view of the PM generator using matplotlib.
No CAD software needed - just Python!

Run this script to see your generator in 3D.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patches as mpatches

# Generator Parameters (mm)
ROTOR_OUTER_RADIUS = 45.0
ROTOR_INNER_RADIUS = 20.0
ROTOR_LENGTH = 80.0
MAGNET_THICKNESS = 5.0
N_POLES = 12

STATOR_OUTER_RADIUS = 70.0
STATOR_INNER_RADIUS = 47.0  # Air gap = 2mm
STATOR_LENGTH = 80.0
N_SLOTS = 18
TOOTH_WIDTH = 8.0

SHAFT_RADIUS = 15.0
SHAFT_LENGTH = 160.0

HOUSING_OUTER_RADIUS = 85.0
HOUSING_LENGTH = 100.0


def create_cylinder_surface(radius, length, z_offset=0, n_points=50):
    """Create a cylindrical surface for 3D plotting."""
    theta = np.linspace(0, 2*np.pi, n_points)
    z = np.linspace(z_offset, z_offset + length, 2)
    theta, z = np.meshgrid(theta, z)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    return x, y, z


def create_disc(inner_radius, outer_radius, z_pos, n_points=50):
    """Create a disc (annulus) for end caps."""
    theta = np.linspace(0, 2*np.pi, n_points)
    r = np.array([inner_radius, outer_radius])
    theta, r = np.meshgrid(theta, r)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.full_like(x, z_pos)
    return x, y, z


def create_arc_segment(inner_r, outer_r, start_angle, end_angle, z_start, z_end, n_theta=10, n_z=2):
    """Create an arc segment (for magnets)."""
    theta = np.linspace(start_angle, end_angle, n_theta)
    z = np.linspace(z_start, z_end, n_z)
    
    # Create vertices for the curved surfaces
    vertices = []
    
    # Outer curved surface
    for i in range(len(theta) - 1):
        for j in range(len(z) - 1):
            v = [
                [outer_r * np.cos(theta[i]), outer_r * np.sin(theta[i]), z[j]],
                [outer_r * np.cos(theta[i+1]), outer_r * np.sin(theta[i+1]), z[j]],
                [outer_r * np.cos(theta[i+1]), outer_r * np.sin(theta[i+1]), z[j+1]],
                [outer_r * np.cos(theta[i]), outer_r * np.sin(theta[i]), z[j+1]],
            ]
            vertices.append(v)
    
    return vertices


def plot_generator_3d(view_type='full', show_cross_section=False):
    """
    Create 3D visualization of the generator.
    
    Parameters:
        view_type: 'full', 'exploded', or 'cutaway'
        show_cross_section: If True, shows internal components
    """
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Explosion offset
    explode = 30 if view_type == 'exploded' else 0
    
    # Z positions
    z_center = 0
    z_rotor_start = -ROTOR_LENGTH / 2
    z_stator_start = -STATOR_LENGTH / 2
    z_housing_start = -HOUSING_LENGTH / 2
    z_shaft_start = -SHAFT_LENGTH / 2
    
    # =========================================
    # SHAFT (center, dark gray)
    # =========================================
    x, y, z = create_cylinder_surface(SHAFT_RADIUS, SHAFT_LENGTH, z_shaft_start - explode*0.5)
    ax.plot_surface(x, y, z, color='dimgray', alpha=0.9, linewidth=0)
    
    # Shaft end caps
    theta = np.linspace(0, 2*np.pi, 30)
    for z_pos in [z_shaft_start - explode*0.5, z_shaft_start + SHAFT_LENGTH - explode*0.5]:
        x_cap = SHAFT_RADIUS * np.cos(theta)
        y_cap = SHAFT_RADIUS * np.sin(theta)
        z_cap = np.full_like(theta, z_pos)
        ax.plot_trisurf(x_cap, y_cap, z_cap, color='gray', alpha=0.9)
    
    # =========================================
    # ROTOR CORE (inner cylinder, steel blue)
    # =========================================
    rotor_core_outer = ROTOR_OUTER_RADIUS - MAGNET_THICKNESS
    x, y, z = create_cylinder_surface(rotor_core_outer, ROTOR_LENGTH, z_rotor_start)
    ax.plot_surface(x, y, z, color='steelblue', alpha=0.8, linewidth=0)
    
    # =========================================
    # PERMANENT MAGNETS (alternating N/S colors)
    # =========================================
    magnet_arc = 2 * np.pi / N_POLES * 0.85  # 85% pole coverage
    colors_magnets = ['red', 'blue']  # N = red, S = blue
    
    for i in range(N_POLES):
        angle_center = i * 2 * np.pi / N_POLES
        angle_start = angle_center - magnet_arc / 2
        angle_end = angle_center + magnet_arc / 2
        
        # Create magnet as arc segment
        n_arc = 15
        theta_mag = np.linspace(angle_start, angle_end, n_arc)
        
        inner_r = rotor_core_outer
        outer_r = ROTOR_OUTER_RADIUS
        
        # Top and bottom arcs
        for z_pos in [z_rotor_start, z_rotor_start + ROTOR_LENGTH]:
            x_arc = np.concatenate([inner_r * np.cos(theta_mag), outer_r * np.cos(theta_mag[::-1])])
            y_arc = np.concatenate([inner_r * np.sin(theta_mag), outer_r * np.sin(theta_mag[::-1])])
            z_arc = np.full_like(x_arc, z_pos)
            
            # Create polygon
            verts = [list(zip(x_arc, y_arc, z_arc))]
            poly = Poly3DCollection(verts, alpha=0.9)
            poly.set_facecolor(colors_magnets[i % 2])
            poly.set_edgecolor('black')
            poly.set_linewidth(0.5)
            ax.add_collection3d(poly)
        
        # Outer curved surface of magnet
        for j in range(n_arc - 1):
            x_face = [
                outer_r * np.cos(theta_mag[j]), outer_r * np.cos(theta_mag[j+1]),
                outer_r * np.cos(theta_mag[j+1]), outer_r * np.cos(theta_mag[j])
            ]
            y_face = [
                outer_r * np.sin(theta_mag[j]), outer_r * np.sin(theta_mag[j+1]),
                outer_r * np.sin(theta_mag[j+1]), outer_r * np.sin(theta_mag[j])
            ]
            z_face = [z_rotor_start, z_rotor_start, z_rotor_start + ROTOR_LENGTH, z_rotor_start + ROTOR_LENGTH]
            
            verts = [list(zip(x_face, y_face, z_face))]
            poly = Poly3DCollection(verts, alpha=0.9)
            poly.set_facecolor(colors_magnets[i % 2])
            poly.set_edgecolor('black')
            poly.set_linewidth(0.3)
            ax.add_collection3d(poly)
    
    # =========================================
    # STATOR (with teeth and slots)
    # =========================================
    if not show_cross_section or view_type == 'exploded':
        # Full stator outer surface
        x, y, z = create_cylinder_surface(STATOR_OUTER_RADIUS, STATOR_LENGTH, 
                                          z_stator_start + explode*0.5)
        ax.plot_surface(x, y, z, color='darkslategray', alpha=0.6, linewidth=0)
    
    # Stator teeth (inner surface with slots)
    slot_angle = 2 * np.pi / N_SLOTS
    tooth_arc = slot_angle * 0.6  # Tooth is 60% of slot pitch
    
    for i in range(N_SLOTS):
        angle_center = i * slot_angle
        angle_start = angle_center - tooth_arc / 2
        angle_end = angle_center + tooth_arc / 2
        
        n_arc = 8
        theta_tooth = np.linspace(angle_start, angle_end, n_arc)
        
        # Inner surface of tooth
        for j in range(n_arc - 1):
            x_face = [
                STATOR_INNER_RADIUS * np.cos(theta_tooth[j]), 
                STATOR_INNER_RADIUS * np.cos(theta_tooth[j+1]),
                STATOR_INNER_RADIUS * np.cos(theta_tooth[j+1]), 
                STATOR_INNER_RADIUS * np.cos(theta_tooth[j])
            ]
            y_face = [
                STATOR_INNER_RADIUS * np.sin(theta_tooth[j]), 
                STATOR_INNER_RADIUS * np.sin(theta_tooth[j+1]),
                STATOR_INNER_RADIUS * np.sin(theta_tooth[j+1]), 
                STATOR_INNER_RADIUS * np.sin(theta_tooth[j])
            ]
            z_face = [z_stator_start + explode*0.5, z_stator_start + explode*0.5, 
                     z_stator_start + STATOR_LENGTH + explode*0.5, 
                     z_stator_start + STATOR_LENGTH + explode*0.5]
            
            verts = [list(zip(x_face, y_face, z_face))]
            poly = Poly3DCollection(verts, alpha=0.8)
            poly.set_facecolor('slategray')
            poly.set_edgecolor('black')
            poly.set_linewidth(0.3)
            ax.add_collection3d(poly)
    
    # =========================================
    # COPPER WINDINGS (in slots)
    # =========================================
    winding_inner_r = STATOR_INNER_RADIUS + 2
    winding_outer_r = STATOR_OUTER_RADIUS - 10
    
    for i in range(N_SLOTS):
        angle_center = i * slot_angle + slot_angle * 0.5  # Center of slot
        slot_width_angle = slot_angle * 0.3
        
        # Simplified winding representation
        theta_wind = np.linspace(angle_center - slot_width_angle/2, 
                                 angle_center + slot_width_angle/2, 5)
        
        for j in range(len(theta_wind) - 1):
            for r in [winding_inner_r, winding_outer_r]:
                x_w = r * np.cos(theta_wind[j:j+2])
                y_w = r * np.sin(theta_wind[j:j+2])
                z_w = [z_stator_start + 5 + explode*0.5, 
                       z_stator_start + STATOR_LENGTH - 5 + explode*0.5]
                ax.plot(x_w[[0,0]], y_w[[0,0]], z_w, color='orange', linewidth=2, alpha=0.8)
    
    # =========================================
    # HOUSING (outer shell with fins)
    # =========================================
    if view_type != 'cutaway':
        x, y, z = create_cylinder_surface(HOUSING_OUTER_RADIUS, HOUSING_LENGTH, 
                                          z_housing_start + explode)
        ax.plot_surface(x, y, z, color='silver', alpha=0.3, linewidth=0)
        
        # Cooling fins
        n_fins = 12
        fin_height = 8
        for i in range(n_fins):
            if i % 3 == 0:  # Skip some for visibility
                continue
            angle = i * 2 * np.pi / n_fins
            x_fin = [(HOUSING_OUTER_RADIUS) * np.cos(angle), 
                     (HOUSING_OUTER_RADIUS + fin_height) * np.cos(angle)]
            y_fin = [(HOUSING_OUTER_RADIUS) * np.sin(angle), 
                     (HOUSING_OUTER_RADIUS + fin_height) * np.sin(angle)]
            z_fin = [z_housing_start + explode, z_housing_start + HOUSING_LENGTH + explode]
            
            ax.plot([x_fin[1], x_fin[1]], [y_fin[1], y_fin[1]], z_fin, 
                   color='gray', linewidth=3, alpha=0.7)
    
    # =========================================
    # END CAPS & BEARINGS
    # =========================================
    bearing_or = 26
    bearing_ir = 15
    
    for z_mult, z_off in [(-1, -explode), (1, explode)]:
        z_pos = z_housing_start + (0 if z_mult == -1 else HOUSING_LENGTH) + z_off
        
        # End cap disc
        theta = np.linspace(0, 2*np.pi, 40)
        for r in np.linspace(bearing_or + 5, HOUSING_OUTER_RADIUS, 5):
            x_cap = r * np.cos(theta)
            y_cap = r * np.sin(theta)
            z_cap = np.full_like(theta, z_pos)
            ax.plot(x_cap, y_cap, z_cap, color='silver', linewidth=0.5, alpha=0.5)
        
        # Bearing (simplified)
        x_b, y_b, z_b = create_cylinder_surface(bearing_or, 15, z_pos + z_mult * 5)
        ax.plot_surface(x_b, y_b, z_b, color='gold', alpha=0.8, linewidth=0)
    
    # =========================================
    # STYLING
    # =========================================
    ax.set_xlabel('X (mm)', fontsize=10)
    ax.set_ylabel('Y (mm)', fontsize=10)
    ax.set_zlabel('Z (mm)', fontsize=10)
    
    # Set equal aspect ratio
    max_range = max(HOUSING_OUTER_RADIUS, SHAFT_LENGTH/2) * 1.2
    ax.set_xlim(-max_range, max_range)
    ax.set_ylim(-max_range, max_range)
    ax.set_zlim(-max_range, max_range)
    
    # Title
    title = "Permanent Magnet Generator - 3D View"
    if view_type == 'exploded':
        title += " (Exploded)"
    elif view_type == 'cutaway':
        title += " (Cutaway)"
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='dimgray', label='Shaft'),
        mpatches.Patch(facecolor='steelblue', label='Rotor Core'),
        mpatches.Patch(facecolor='red', label='Magnet (N)'),
        mpatches.Patch(facecolor='blue', label='Magnet (S)'),
        mpatches.Patch(facecolor='slategray', label='Stator'),
        mpatches.Patch(facecolor='orange', label='Windings'),
        mpatches.Patch(facecolor='silver', label='Housing'),
        mpatches.Patch(facecolor='gold', label='Bearings'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8)
    
    # Set viewing angle
    ax.view_init(elev=25, azim=45)
    
    return fig, ax


def plot_cross_section_2d():
    """Create a detailed 2D cross-section view."""
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Draw from inside out
    components = []
    
    # Shaft
    shaft = plt.Circle((0, 0), SHAFT_RADIUS, color='dimgray', label='Shaft')
    ax.add_patch(shaft)
    
    # Rotor core
    rotor_core = plt.Circle((0, 0), ROTOR_OUTER_RADIUS - MAGNET_THICKNESS, 
                            color='steelblue', label='Rotor Core')
    ax.add_patch(rotor_core)
    # Cut out shaft hole
    shaft_hole = plt.Circle((0, 0), SHAFT_RADIUS, color='dimgray')
    ax.add_patch(shaft_hole)
    
    # Magnets
    magnet_arc_deg = 360 / N_POLES * 0.85
    colors = ['red', 'blue']
    for i in range(N_POLES):
        angle = i * 360 / N_POLES
        wedge = plt.matplotlib.patches.Wedge(
            (0, 0), ROTOR_OUTER_RADIUS, 
            angle - magnet_arc_deg/2, angle + magnet_arc_deg/2,
            width=MAGNET_THICKNESS,
            color=colors[i % 2],
            label='Magnet N' if i == 0 else ('Magnet S' if i == 1 else None)
        )
        ax.add_patch(wedge)
    
    # Air gap (just space, shown as white ring)
    air_gap = plt.Circle((0, 0), STATOR_INNER_RADIUS, color='white', fill=False, 
                         linestyle='--', linewidth=2, label='Air Gap')
    ax.add_patch(air_gap)
    
    # Stator with teeth
    stator_outer = plt.Circle((0, 0), STATOR_OUTER_RADIUS, color='slategray', 
                              label='Stator Core')
    ax.add_patch(stator_outer)
    
    # Stator teeth and slots
    slot_angle_deg = 360 / N_SLOTS
    tooth_arc_deg = slot_angle_deg * 0.6
    slot_arc_deg = slot_angle_deg * 0.4
    
    # Cut out slots (show as different color)
    for i in range(N_SLOTS):
        slot_center = i * slot_angle_deg + slot_angle_deg * 0.5
        wedge = plt.matplotlib.patches.Wedge(
            (0, 0), STATOR_OUTER_RADIUS - 5,
            slot_center - slot_arc_deg/2, slot_center + slot_arc_deg/2,
            width=STATOR_OUTER_RADIUS - STATOR_INNER_RADIUS - 8,
            color='orange', alpha=0.8
        )
        ax.add_patch(wedge)
    
    # Draw teeth outlines
    for i in range(N_SLOTS):
        tooth_center = i * slot_angle_deg
        for r in [STATOR_INNER_RADIUS, STATOR_INNER_RADIUS + 15]:
            theta1 = np.radians(tooth_center - tooth_arc_deg/2)
            theta2 = np.radians(tooth_center + tooth_arc_deg/2)
            
            x1, y1 = r * np.cos(theta1), r * np.sin(theta1)
            x2, y2 = r * np.cos(theta2), r * np.sin(theta2)
            ax.plot([x1, x2], [y1, y2], 'k-', linewidth=0.5)
    
    # Housing
    housing = plt.Circle((0, 0), HOUSING_OUTER_RADIUS, color='silver', 
                         fill=False, linewidth=8, label='Housing')
    ax.add_patch(housing)
    
    # Cooling fins
    n_fins = 16
    for i in range(n_fins):
        angle = np.radians(i * 360 / n_fins)
        x1 = HOUSING_OUTER_RADIUS * np.cos(angle)
        y1 = HOUSING_OUTER_RADIUS * np.sin(angle)
        x2 = (HOUSING_OUTER_RADIUS + 10) * np.cos(angle)
        y2 = (HOUSING_OUTER_RADIUS + 10) * np.sin(angle)
        ax.plot([x1, x2], [y1, y2], color='gray', linewidth=4)
    
    # Add dimension annotations
    # Rotor OD
    ax.annotate('', xy=(ROTOR_OUTER_RADIUS, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(ROTOR_OUTER_RADIUS/2, -5, f'R={ROTOR_OUTER_RADIUS}mm', fontsize=8, ha='center')
    
    # Air gap
    ax.annotate('', xy=(ROTOR_OUTER_RADIUS, 50), xytext=(STATOR_INNER_RADIUS, 50),
                arrowprops=dict(arrowstyle='<->', color='green', lw=2))
    ax.text((ROTOR_OUTER_RADIUS + STATOR_INNER_RADIUS)/2, 55, 
            f'Gap={STATOR_INNER_RADIUS - ROTOR_OUTER_RADIUS}mm', 
            fontsize=9, ha='center', color='green', fontweight='bold')
    
    # Labels
    ax.set_xlim(-110, 110)
    ax.set_ylim(-110, 110)
    ax.set_aspect('equal')
    ax.set_xlabel('X (mm)', fontsize=11)
    ax.set_ylabel('Y (mm)', fontsize=11)
    ax.set_title('PM Generator Cross-Section\n12 Poles / 18 Slots', fontsize=14, fontweight='bold')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='dimgray', label='Shaft'),
        mpatches.Patch(facecolor='steelblue', label='Rotor Core'),
        mpatches.Patch(facecolor='red', label='Magnet (N-pole)'),
        mpatches.Patch(facecolor='blue', label='Magnet (S-pole)'),
        mpatches.Patch(facecolor='slategray', label='Stator Core'),
        mpatches.Patch(facecolor='orange', label='Cu Windings'),
        mpatches.Patch(facecolor='silver', label='Housing'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    ax.grid(True, alpha=0.3)
    
    return fig, ax


def create_all_views():
    """Generate all visualization views and save them."""
    import os
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("PERMANENT MAGNET GENERATOR - 3D VISUALIZATION")
    print("=" * 60)
    
    # 1. Cross-section 2D
    print("\n[1/4] Creating 2D cross-section view...")
    fig1, _ = plot_cross_section_2d()
    fig1.savefig(os.path.join(output_dir, "generator_cross_section.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/generator_cross_section.png")
    
    # 2. 3D assembled view
    print("\n[2/4] Creating 3D assembled view...")
    fig2, _ = plot_generator_3d(view_type='full')
    fig2.savefig(os.path.join(output_dir, "generator_3d_assembled.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/generator_3d_assembled.png")
    
    # 3. 3D exploded view
    print("\n[3/4] Creating 3D exploded view...")
    fig3, _ = plot_generator_3d(view_type='exploded')
    fig3.savefig(os.path.join(output_dir, "generator_3d_exploded.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/generator_3d_exploded.png")
    
    # 4. Cutaway view
    print("\n[4/4] Creating cutaway view...")
    fig4, _ = plot_generator_3d(view_type='cutaway', show_cross_section=True)
    fig4.savefig(os.path.join(output_dir, "generator_3d_cutaway.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/generator_3d_cutaway.png")
    
    print("\n" + "=" * 60)
    print("ALL VIEWS GENERATED!")
    print("=" * 60)
    print(f"\nFiles saved to: {os.path.abspath(output_dir)}/")
    print("\nShowing interactive 3D view...")
    
    # Show interactive view
    plt.show()


if __name__ == "__main__":
    create_all_views()
