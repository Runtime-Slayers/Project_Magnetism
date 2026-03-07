"""
AXIAL FLUX GENERATOR - 3D VISUALIZATION
=========================================

Visualizes the optimized axial flux dual-rotor (YASA-style) generator.

This is the recommended design with:
- 2x current capacity
- 48% lower cost
- 8x power density
- Zero cogging (coreless option)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patches as mpatches
import os

# Optimized Axial Flux Design Parameters
OUTER_DIAMETER = 160.0  # mm
INNER_DIAMETER = 80.0   # mm
TOTAL_THICKNESS = 50.0  # mm

N_POLES = 16  # poles per rotor
N_COILS = 12  # concentrated coils

MAGNET_THICKNESS = 6.0  # mm
ROTOR_BACK_IRON = 5.0   # mm
STATOR_THICKNESS = 15.0 # mm (winding depth)
AIR_GAP = 1.5           # mm per side

SHAFT_DIAMETER = 25.0   # mm


def create_axial_disc(inner_r, outer_r, z_pos, n_points=60):
    """Create a disc/annulus at z position."""
    theta = np.linspace(0, 2*np.pi, n_points)
    
    # Create filled annulus
    r = np.linspace(inner_r, outer_r, 10)
    theta_grid, r_grid = np.meshgrid(theta, r)
    
    x = r_grid * np.cos(theta_grid)
    y = r_grid * np.sin(theta_grid)
    z = np.full_like(x, z_pos)
    
    return x, y, z


def plot_axial_flux_3d(view_type='assembled', show_coreless=False):
    """
    Create 3D visualization of axial flux generator.
    
    Parameters:
        view_type: 'assembled', 'exploded', or 'cross_section'
        show_coreless: If True, shows coreless stator variant
    """
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Radii
    outer_r = OUTER_DIAMETER / 2
    inner_r = INNER_DIAMETER / 2
    shaft_r = SHAFT_DIAMETER / 2
    
    # Z positions (center at 0)
    explode = 20 if view_type == 'exploded' else 0
    
    # Component thicknesses
    z_rotor1_back = -TOTAL_THICKNESS/2
    z_rotor1_magnets = z_rotor1_back + ROTOR_BACK_IRON
    z_stator_start = z_rotor1_magnets + MAGNET_THICKNESS + AIR_GAP
    z_stator_end = z_stator_start + STATOR_THICKNESS
    z_rotor2_magnets = z_stator_end + AIR_GAP
    z_rotor2_back = z_rotor2_magnets + MAGNET_THICKNESS
    
    # =========================================
    # SHAFT (through center)
    # =========================================
    theta = np.linspace(0, 2*np.pi, 30)
    z_shaft = np.linspace(-TOTAL_THICKNESS - 20, TOTAL_THICKNESS + 20, 2)
    theta_grid, z_grid = np.meshgrid(theta, z_shaft)
    x_shaft = shaft_r * np.cos(theta_grid)
    y_shaft = shaft_r * np.sin(theta_grid)
    ax.plot_surface(x_shaft, y_shaft, z_grid, color='dimgray', alpha=0.9, linewidth=0)
    
    # =========================================
    # ROTOR 1 (bottom) - Back iron
    # =========================================
    x, y, z = create_axial_disc(inner_r * 0.8, outer_r, z_rotor1_back - explode)
    ax.plot_surface(x, y, z, color='steelblue', alpha=0.8, linewidth=0)
    
    # Rotor 1 surface (where magnets sit)
    x, y, z = create_axial_disc(inner_r * 0.8, outer_r, z_rotor1_magnets - explode)
    ax.plot_surface(x, y, z, color='steelblue', alpha=0.6, linewidth=0)
    
    # =========================================  
    # MAGNETS - Rotor 1
    # =========================================
    magnet_colors = ['red', 'blue']  # N, S alternating
    
    for i in range(N_POLES):
        angle_center = i * 2 * np.pi / N_POLES
        arc_angle = 2 * np.pi / N_POLES * 0.85  # 85% coverage
        
        n_arc = 15
        theta_mag = np.linspace(angle_center - arc_angle/2, 
                                angle_center + arc_angle/2, n_arc)
        
        # Top face of magnet (visible side)
        r_vals = np.linspace(inner_r, outer_r * 0.95, 8)
        for j in range(len(r_vals) - 1):
            for k in range(len(theta_mag) - 1):
                x_face = [
                    r_vals[j] * np.cos(theta_mag[k]),
                    r_vals[j+1] * np.cos(theta_mag[k]),
                    r_vals[j+1] * np.cos(theta_mag[k+1]),
                    r_vals[j] * np.cos(theta_mag[k+1])
                ]
                y_face = [
                    r_vals[j] * np.sin(theta_mag[k]),
                    r_vals[j+1] * np.sin(theta_mag[k]),
                    r_vals[j+1] * np.sin(theta_mag[k+1]),
                    r_vals[j] * np.sin(theta_mag[k+1])
                ]
                z_face = [z_rotor1_magnets + MAGNET_THICKNESS - explode] * 4
                
                verts = [list(zip(x_face, y_face, z_face))]
                poly = Poly3DCollection(verts, alpha=0.9)
                poly.set_facecolor(magnet_colors[i % 2])
                poly.set_edgecolor('black')
                poly.set_linewidth(0.2)
                ax.add_collection3d(poly)
    
    # =========================================
    # STATOR WITH CONCENTRATED WINDINGS
    # =========================================
    stator_z = (z_stator_start + z_stator_end) / 2
    
    if not show_coreless:
        # Stator core (teeth only, no back iron for dual rotor)
        for i in range(N_COILS):
            tooth_angle = i * 2 * np.pi / N_COILS
            tooth_arc = 2 * np.pi / N_COILS * 0.4  # Tooth is 40% of pitch
            
            n_arc = 8
            theta_tooth = np.linspace(tooth_angle - tooth_arc/2,
                                      tooth_angle + tooth_arc/2, n_arc)
            
            # Tooth faces
            r_vals = np.linspace(inner_r * 1.1, outer_r * 0.9, 5)
            for j in range(len(r_vals) - 1):
                for k in range(len(theta_tooth) - 1):
                    for z_t in [z_stator_start, z_stator_end]:
                        x_face = [
                            r_vals[j] * np.cos(theta_tooth[k]),
                            r_vals[j+1] * np.cos(theta_tooth[k]),
                            r_vals[j+1] * np.cos(theta_tooth[k+1]),
                            r_vals[j] * np.cos(theta_tooth[k+1])
                        ]
                        y_face = [
                            r_vals[j] * np.sin(theta_tooth[k]),
                            r_vals[j+1] * np.sin(theta_tooth[k]),
                            r_vals[j+1] * np.sin(theta_tooth[k+1]),
                            r_vals[j] * np.sin(theta_tooth[k+1])
                        ]
                        z_face = [z_t] * 4
                        
                        verts = [list(zip(x_face, y_face, z_face))]
                        poly = Poly3DCollection(verts, alpha=0.7)
                        poly.set_facecolor('slategray')
                        poly.set_edgecolor('black')
                        poly.set_linewidth(0.3)
                        ax.add_collection3d(poly)
    
    # Concentrated windings (coils around each tooth)
    winding_colors = ['orange', 'gold', 'darkorange']  # 3 phases
    
    for i in range(N_COILS):
        coil_angle = i * 2 * np.pi / N_COILS
        if show_coreless:
            coil_angle += np.pi / N_COILS  # Offset for coreless
        
        coil_arc = 2 * np.pi / N_COILS * 0.35
        
        # Draw coil as thick arc
        n_arc = 12
        theta_coil = np.linspace(coil_angle - coil_arc/2,
                                 coil_angle + coil_arc/2, n_arc)
        
        avg_r = (inner_r + outer_r) / 2
        
        # Coil body
        for z_c in np.linspace(z_stator_start + 2, z_stator_end - 2, 5):
            x_coil = avg_r * np.cos(theta_coil)
            y_coil = avg_r * np.sin(theta_coil)
            z_coil = np.full_like(theta_coil, z_c)
            ax.plot(x_coil, y_coil, z_coil, 
                   color=winding_colors[i % 3], linewidth=4, alpha=0.8)
        
        # End turns (inner and outer)
        for r_end in [inner_r * 1.15, outer_r * 0.85]:
            x_end = r_end * np.cos(theta_coil)
            y_end = r_end * np.sin(theta_coil)
            ax.plot(x_end, y_end, [z_stator_start]*len(theta_coil),
                   color=winding_colors[i % 3], linewidth=3, alpha=0.7)
            ax.plot(x_end, y_end, [z_stator_end]*len(theta_coil),
                   color=winding_colors[i % 3], linewidth=3, alpha=0.7)
    
    # =========================================
    # ROTOR 2 (top) - Magnets
    # =========================================
    for i in range(N_POLES):
        angle_center = i * 2 * np.pi / N_POLES
        arc_angle = 2 * np.pi / N_POLES * 0.85
        
        n_arc = 15
        theta_mag = np.linspace(angle_center - arc_angle/2,
                                angle_center + arc_angle/2, n_arc)
        
        # Bottom face of magnet (facing stator)
        r_vals = np.linspace(inner_r, outer_r * 0.95, 8)
        for j in range(len(r_vals) - 1):
            for k in range(len(theta_mag) - 1):
                x_face = [
                    r_vals[j] * np.cos(theta_mag[k]),
                    r_vals[j+1] * np.cos(theta_mag[k]),
                    r_vals[j+1] * np.cos(theta_mag[k+1]),
                    r_vals[j] * np.cos(theta_mag[k+1])
                ]
                y_face = [
                    r_vals[j] * np.sin(theta_mag[k]),
                    r_vals[j+1] * np.sin(theta_mag[k]),
                    r_vals[j+1] * np.sin(theta_mag[k+1]),
                    r_vals[j] * np.sin(theta_mag[k+1])
                ]
                z_face = [z_rotor2_magnets + explode] * 4
                
                verts = [list(zip(x_face, y_face, z_face))]
                poly = Poly3DCollection(verts, alpha=0.9)
                # Opposite polarity from rotor 1
                poly.set_facecolor(magnet_colors[(i + 1) % 2])  
                poly.set_edgecolor('black')
                poly.set_linewidth(0.2)
                ax.add_collection3d(poly)
    
    # Rotor 2 back iron
    x, y, z = create_axial_disc(inner_r * 0.8, outer_r, z_rotor2_back + ROTOR_BACK_IRON + explode)
    ax.plot_surface(x, y, z, color='steelblue', alpha=0.8, linewidth=0)
    
    # =========================================
    # STYLING
    # =========================================
    max_range = OUTER_DIAMETER * 0.7
    ax.set_xlim(-max_range, max_range)
    ax.set_ylim(-max_range, max_range)
    ax.set_zlim(-max_range, max_range)
    
    ax.set_xlabel('X (mm)', fontsize=10)
    ax.set_ylabel('Y (mm)', fontsize=10)
    ax.set_zlabel('Z (mm)', fontsize=10)
    
    title = "OPTIMIZED Axial Flux Dual-Rotor Generator"
    if view_type == 'exploded':
        title += " (Exploded View)"
    if show_coreless:
        title += "\n[CORELESS STATOR - ZERO COGGING]"
    ax.set_title(title, fontsize=13, fontweight='bold')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='dimgray', label='Shaft'),
        mpatches.Patch(facecolor='steelblue', label='Rotor Back Iron'),
        mpatches.Patch(facecolor='red', label='Magnet (N-pole)'),
        mpatches.Patch(facecolor='blue', label='Magnet (S-pole)'),
        mpatches.Patch(facecolor='slategray', label='Stator Teeth'),
        mpatches.Patch(facecolor='orange', label='Phase A Winding'),
        mpatches.Patch(facecolor='gold', label='Phase B Winding'),
        mpatches.Patch(facecolor='darkorange', label='Phase C Winding'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8)
    
    ax.view_init(elev=25, azim=45)
    
    return fig, ax


def plot_axial_cross_section():
    """Create a detailed cross-section view of the axial flux generator."""
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Dimensions
    outer_r = OUTER_DIAMETER / 2
    inner_r = INNER_DIAMETER / 2
    shaft_r = SHAFT_DIAMETER / 2
    
    # Z positions for cross section (shown as Y in 2D)
    y_base = 0
    y_rotor1_back = y_base
    y_rotor1_top = y_rotor1_back + ROTOR_BACK_IRON
    y_magnet1_top = y_rotor1_top + MAGNET_THICKNESS
    y_gap1_top = y_magnet1_top + AIR_GAP
    y_stator_top = y_gap1_top + STATOR_THICKNESS
    y_gap2_top = y_stator_top + AIR_GAP
    y_magnet2_top = y_gap2_top + MAGNET_THICKNESS
    y_rotor2_top = y_magnet2_top + ROTOR_BACK_IRON
    
    # Draw components (as rectangles in cross-section)
    
    # Function to draw a component
    def draw_component(x_left, x_right, y_bottom, y_top, color, label=None, hatch=None):
        rect = plt.Rectangle((x_left, y_bottom), x_right - x_left, y_top - y_bottom,
                             facecolor=color, edgecolor='black', linewidth=1,
                             label=label, hatch=hatch)
        ax.add_patch(rect)
        # Mirror on other side
        rect2 = plt.Rectangle((-x_right, y_bottom), x_right - x_left, y_top - y_bottom,
                              facecolor=color, edgecolor='black', linewidth=1, hatch=hatch)
        ax.add_patch(rect2)
    
    # Shaft
    draw_component(-shaft_r, shaft_r, -5, y_rotor2_top + 10, 'dimgray', 'Shaft')
    
    # Rotor 1 back iron
    draw_component(inner_r * 0.7, outer_r, y_rotor1_back, y_rotor1_top, 'steelblue', 'Rotor Iron')
    
    # Rotor 1 magnets (alternating colors for poles)
    magnet_width = (outer_r - inner_r) / 8
    for i in range(4):
        x_left = inner_r + i * 2 * magnet_width
        x_right = x_left + magnet_width
        color = 'red' if i % 2 == 0 else 'blue'
        draw_component(x_left, x_right, y_rotor1_top, y_magnet1_top, color,
                      'Magnet N' if i == 0 else ('Magnet S' if i == 1 else None))
    
    # Stator (with teeth pattern)
    draw_component(inner_r * 1.1, outer_r * 0.9, y_gap1_top, y_stator_top, 'slategray', 'Stator')
    
    # Windings (in slots between teeth)
    coil_width = (outer_r - inner_r) / 10
    for i in range(3):
        x_center = inner_r + (i * 2 + 1) * coil_width * 1.5 + coil_width
        colors = ['orange', 'gold', 'darkorange']
        draw_component(x_center - coil_width/2, x_center + coil_width/2,
                      y_gap1_top + 1, y_stator_top - 1, colors[i],
                      f'Phase {"ABC"[i]}' if i < 3 else None, hatch='///')
    
    # Rotor 2 magnets
    for i in range(4):
        x_left = inner_r + i * 2 * magnet_width
        x_right = x_left + magnet_width
        color = 'blue' if i % 2 == 0 else 'red'  # Opposite polarity
        draw_component(x_left, x_right, y_gap2_top, y_magnet2_top, color)
    
    # Rotor 2 back iron
    draw_component(inner_r * 0.7, outer_r, y_magnet2_top, y_rotor2_top, 'steelblue')
    
    # Air gap annotations
    ax.annotate('', xy=(outer_r + 5, y_magnet1_top), xytext=(outer_r + 5, y_gap1_top),
                arrowprops=dict(arrowstyle='<->', color='green', lw=2))
    ax.text(outer_r + 8, (y_magnet1_top + y_gap1_top)/2, f'{AIR_GAP}mm\nAir Gap',
            fontsize=9, color='green', ha='left', va='center')
    
    # Dimension annotations
    ax.annotate('', xy=(0, y_rotor2_top + 5), xytext=(outer_r, y_rotor2_top + 5),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(outer_r/2, y_rotor2_top + 8, f'R = {outer_r:.0f}mm', fontsize=10, ha='center')
    
    # Total thickness
    ax.annotate('', xy=(-outer_r - 15, y_rotor1_back), xytext=(-outer_r - 15, y_rotor2_top),
                arrowprops=dict(arrowstyle='<->', color='purple', lw=2))
    ax.text(-outer_r - 18, (y_rotor1_back + y_rotor2_top)/2, 
            f'Total\n{y_rotor2_top:.0f}mm', fontsize=9, ha='right', va='center', color='purple')
    
    # Flux path arrows
    flux_x = outer_r * 0.7
    for y_start, y_end in [(y_rotor1_top, y_magnet1_top - 1), 
                            (y_magnet1_top + 1, y_stator_top - 5),
                            (y_gap1_top + 5, y_gap2_top - 1),
                            (y_gap2_top + 1, y_magnet2_top - 1)]:
        ax.annotate('', xy=(flux_x, y_end), xytext=(flux_x, y_start),
                    arrowprops=dict(arrowstyle='->', color='purple', lw=1.5, alpha=0.5))
    
    ax.text(flux_x + 3, (y_gap1_top + y_stator_top)/2, 'Flux\nPath', 
            fontsize=8, color='purple', alpha=0.7)
    
    # Styling
    ax.set_xlim(-outer_r - 25, outer_r + 25)
    ax.set_ylim(-10, y_rotor2_top + 15)
    ax.set_aspect('equal')
    ax.set_xlabel('Radius (mm)', fontsize=11)
    ax.set_ylabel('Axial Position (mm)', fontsize=11)
    ax.set_title('Axial Flux Dual-Rotor Generator\nCross-Section View', 
                fontsize=13, fontweight='bold')
    
    # Legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=9)
    
    ax.grid(True, alpha=0.3)
    
    return fig, ax


def plot_design_comparison():
    """Create comparison chart between old and new design."""
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Data
    categories = ['Power\nDensity\n(kW/kg)', 'Current\nCapacity\n(A)', 'Cost\n($)', 
                  'Cogging\n(%)', 'Efficiency\n(%)']
    
    old_design = [0.4, 10.4, 221, 2.5, 96.2]
    new_design = [3.1, 20.8, 115, 0.0, 96.3]
    
    # Normalize for comparison (percentage improvement)
    improvements = []
    for old, new in zip(old_design, new_design):
        if old > new and categories[old_design.index(old)] in ['Cost\n($)', 'Cogging\n(%)']:
            improvements.append((old - new) / old * 100)
        else:
            improvements.append((new - old) / max(old, 0.01) * 100)
    
    # Chart 1: Absolute values comparison
    ax1 = axes[0]
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, old_design, width, label='Original Radial', color='gray', alpha=0.7)
    bars2 = ax1.bar(x + width/2, new_design, width, label='New Axial Flux', color='green', alpha=0.8)
    
    ax1.set_ylabel('Value', fontsize=11)
    ax1.set_title('Design Comparison', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=9)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', fontsize=8)
    
    # Chart 2: Cost breakdown
    ax2 = axes[1]
    
    # Old design costs
    old_costs = ['Magnets\n$7', 'Copper\n$13', 'Steel\n$1', 'Mfg\n$200']
    old_values = [7, 13, 1, 200]
    
    # New design costs  
    new_costs = ['Magnets\n$11', 'Copper\n$4', 'Steel\n$0', 'Mfg\n$100']
    new_values = [11, 4, 0, 100]
    
    x = np.arange(4)
    bars1 = ax2.bar(x - width/2, old_values, width, label='Original', color='gray', alpha=0.7)
    bars2 = ax2.bar(x + width/2, new_values, width, label='New Axial', color='green', alpha=0.8)
    
    ax2.set_ylabel('Cost ($)', fontsize=11)
    ax2.set_title('Cost Breakdown', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(['Magnets', 'Copper', 'Steel', 'Manufacturing'], fontsize=9)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Chart 3: Key improvements (bar chart)
    ax3 = axes[2]
    
    improvements_data = {
        'Power Density': (0.4, 3.1, 'kW/kg'),
        'Current': (10.4, 20.8, 'A'),
        'Cost': (221, 115, '$'),
        'Cogging': (2.5, 0.0, '%'),
    }
    
    names = list(improvements_data.keys())
    multipliers = []
    for name, (old, new, unit) in improvements_data.items():
        if name in ['Cost', 'Cogging']:
            mult = old / max(new, 0.01)
            multipliers.append(min(mult, 10))  # Cap at 10x for display
        else:
            multipliers.append(new / old)
    
    colors = ['green' if m > 1 else 'red' for m in multipliers]
    bars = ax3.barh(names, multipliers, color=colors, alpha=0.8)
    
    ax3.axvline(x=1, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax3.set_xlabel('Improvement Factor (x times better)', fontsize=11)
    ax3.set_title('Improvement Over Original', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # Add labels
    for bar, mult in zip(bars, multipliers):
        width = bar.get_width()
        label = f'{mult:.1f}x' if mult < 10 else '∞'
        ax3.annotate(label, xy=(width, bar.get_y() + bar.get_height()/2),
                    xytext=(5, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    return fig


def create_all_axial_views():
    """Generate all visualization views for the axial flux design."""
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("OPTIMIZED AXIAL FLUX GENERATOR - VISUALIZATION")
    print("=" * 60)
    
    # 1. 3D assembled view
    print("\n[1/5] Creating 3D assembled view...")
    fig1, _ = plot_axial_flux_3d(view_type='assembled')
    fig1.savefig(os.path.join(output_dir, "axial_flux_3d.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/axial_flux_3d.png")
    
    # 2. 3D exploded view
    print("\n[2/5] Creating 3D exploded view...")
    fig2, _ = plot_axial_flux_3d(view_type='exploded')
    fig2.savefig(os.path.join(output_dir, "axial_flux_exploded.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/axial_flux_exploded.png")
    
    # 3. Coreless variant
    print("\n[3/5] Creating coreless stator view (ZERO COGGING)...")
    fig3, _ = plot_axial_flux_3d(view_type='assembled', show_coreless=True)
    fig3.savefig(os.path.join(output_dir, "axial_flux_coreless.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/axial_flux_coreless.png")
    
    # 4. Cross section
    print("\n[4/5] Creating cross-section view...")
    fig4, _ = plot_axial_cross_section()
    fig4.savefig(os.path.join(output_dir, "axial_flux_cross_section.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/axial_flux_cross_section.png")
    
    # 5. Comparison chart
    print("\n[5/5] Creating design comparison chart...")
    fig5 = plot_design_comparison()
    fig5.savefig(os.path.join(output_dir, "design_comparison.png"), dpi=150, bbox_inches='tight')
    print(f"      Saved: {output_dir}/design_comparison.png")
    
    print("\n" + "=" * 60)
    print("ALL VIEWS GENERATED!")
    print("=" * 60)
    print(f"\nFiles saved to: {os.path.abspath(output_dir)}/")
    
    # Show
    plt.show()


if __name__ == "__main__":
    create_all_axial_views()
