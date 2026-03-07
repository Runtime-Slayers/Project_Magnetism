# Figures Guide for Academic Paper

## Required Figures (8 Total)

Your paper now includes **8 figure placeholders** that need to be created. Here's what each should contain:

---

### Figure 1: Axial Flux Topology (`figures/axial_flux_topology.png`)
**Location:** After Introduction section  
**Required Elements:**
- (a) Exploded view showing two rotor discs and central stator
- (b) Magnetic flux path arrows (perpendicular to rotation)
- (c) Side-by-side comparison with radial flux configuration
- Labels: rotor, stator, magnets, windings, flux direction

**Suggested Tools:** PowerPoint, Draw.io, Inkscape, or engineering CAD

---

### Figure 2: Charge Configurations (`figures/charge_configurations.png`)
**Location:** Before Case 1 in Charge Analysis  
**Required Elements:**
- 6 panels showing:
  - (a) +q, +q with repulsive arrows
  - (b) -q, -q with repulsive arrows
  - (c) +q, -q with attractive arrows
  - (d) +q, neutral with induced dipole
  - (e) -q, neutral with induced dipole
  - (f) neutral-neutral with Van der Waals indication
- Electric field lines for each configuration
- Force vectors clearly shown

**Suggested Tools:** Python (matplotlib), TikZ (LaTeX), or manual drawing

---

### Figure 3: Force Magnitude Comparison (`figures/force_magnitude_comparison.png`)
**Location:** After Case 6 (Van der Waals)  
**Required Elements:**
- Logarithmic scale graph (y-axis: Force in N, x-axis: Distance)
- 6 curves representing each charge case
- Span: 10^-54 N to 10^2 N (42 orders of magnitude!)
- Distance range: 0.1 nm to 10 cm
- Legend identifying each case
- Grid lines for readability

**Suggested Tools:** Python matplotlib, MATLAB, Origin, or Excel with log scale

**Python Example:**
```python
import matplotlib.pyplot as plt
import numpy as np

r = np.logspace(-10, -1, 100)  # 0.1 nm to 10 cm
k_e = 8.987551787e9
q = 1e-6

# Case 1-3: Charged-charged
F_charged = k_e * q**2 / r**2

# Plot with logarithmic scales
plt.figure(figsize=(10, 6))
plt.loglog(r, F_charged, label='Cases 1-3: ±q,±q')
plt.xlabel('Distance (m)')
plt.ylabel('Force (N)')
plt.legend()
plt.grid(True, which="both", ls="-", alpha=0.2)
plt.savefig('force_magnitude_comparison.png', dpi=300)
```

---

### Figure 4: Feynman Diagrams (`figures/feynman_diagram.png`)
**Location:** After QED section  
**Required Elements:**
- (a) Two fermion lines with wavy photon exchange
- (b) Virtual e+e- loop (vacuum polarization)
- (c) Vertex correction diagram
- Proper notation: wavy lines = photons, solid lines = fermions
- Time flows left to right or bottom to top

**Suggested Tools:** TikZ-Feynman (LaTeX), FeynDiagram, or JaxoDraw

---

### Figure 5: Dual Rotor Schematic (`figures/dual_rotor_schematic.png`)
**Location:** Start of Dual-Rotor section  
**Required Elements:**
- (a) Cross-section showing flux paths through rotors and stator
- (b) 3D exploded view
- (c) Magnet pole arrangement (N-S-N-S pattern)
- (d) Stator winding configuration
- Dimensions and air gap labeled
- Color coding: magnets (red/blue for N/S), stator (green), windings (copper)

**Suggested Tools:** SolidWorks, Fusion 360, FreeCAD, or PowerPoint 3D

---

### Figure 6: Performance Comparison (`figures/performance_comparison.png`)
**Location:** After Cost Analysis  
**Required Elements:**
- 4 panels:
  - (a) Bar chart: Current (10.4A vs 20.8A)
  - (b) Bar chart: Power density (8× improvement)
  - (c) Cost comparison ($221 vs $115)
  - (d) Efficiency curves (load % vs efficiency %)
- Clear labels and units
- Color differentiation: single-rotor vs dual-rotor

**Suggested Tools:** Python matplotlib, Excel, or R ggplot2

---

### Figure 7: EV Motor Placement (`figures/ev_motor_placement.png`)
**Location:** Electric Vehicle Integration section  
**Required Elements:**
- Top-down view of Ferrari SF90
- Three motor positions clearly marked:
  - Front motor (220 HP) - circle/icon
  - Rear Motor 1 (165 HP) - circle/icon
  - Rear Motor 2 (165 HP) - circle/icon
- Power output for each motor
- V8 engine position (780 HP)
- Arrows showing power flow

**Suggested Tools:** PowerPoint, Inkscape, or vehicle diagram + annotations

---

### Figure 8: Efficiency Breakdown (`figures/efficiency_breakdown.png`)
**Location:** After Loss Mechanisms  
**Required Elements:**
- 4 panels:
  - (a) Pie chart: Loss distribution (copper, eddy, hysteresis, friction)
  - (b) Efficiency vs speed curve
  - (c) Thermal distribution heat map
  - (d) Comparison bar: YASA vs radial flux efficiency
- Percentages clearly labeled
- Professional color scheme

**Suggested Tools:** Python matplotlib, Excel, or professional plotting software

---

## Quick Solutions

### Option 1: Use Overleaf Directly
When you upload to Overleaf, you can:
1. Comment out figure lines temporarily (add `%` before `\includegraphics`)
2. Compile without figures to see text
3. Add figures later

### Option 2: Create Placeholder Figures
Create simple placeholder images:
```python
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('figures', exist_ok=True)

# Create placeholder
img = Image.new('RGB', (800, 600), color='white')
d = ImageDraw.Draw(img)
d.rectangle([10, 10, 790, 590], outline='black', width=3)
d.text((400, 300), "Figure Placeholder", fill='black', anchor='mm')
img.save('figures/axial_flux_topology.png')
```

### Option 3: Download Similar Figures
Search for similar academic papers on:
- IEEE Xplore
- Google Scholar
- arXiv
- ResearchGate

Create original figures inspired by published work.

---

## Directory Structure Needed

```
Project_Magnetism/
├── paper.tex
├── figures/
│   ├── axial_flux_topology.png
│   ├── charge_configurations.png
│   ├── force_magnitude_comparison.png
│   ├── feynman_diagram.png
│   ├── dual_rotor_schematic.png
│   ├── performance_comparison.png
│   ├── ev_motor_placement.png
│   └── efficiency_breakdown.png
└── paper.pdf (after compilation)
```

---

## For Immediate Compilation

If you want to compile NOW without figures:

1. Comment out all `\includegraphics` lines in paper.tex
2. Or create empty placeholder images
3. Or use `\usepackage[demo]{graphicx}` (shows black boxes)

**Quick fix in LaTeX:**
```latex
% Add this to preamble instead of \usepackage{graphicx}:
\usepackage[demo]{graphicx}  % Creates placeholder boxes
```

---

## Paper Status

✅ **8 figures referenced** with proper captions  
✅ **42 citations** throughout the text  
✅ **Professional structure** maintained  
⏳ **Figures need creation** (or use demo mode)  

Your paper is publication-ready in structure! Create figures as time permits or use demo mode for immediate PDF generation.
