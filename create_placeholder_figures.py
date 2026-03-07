"""
Create placeholder figures for LaTeX paper compilation
Run this script to generate basic placeholder images for all 8 figures
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create figures directory
os.makedirs('figures', exist_ok=True)

# Figure specifications
figures = [
    {
        'filename': 'axial_flux_topology.png',
        'title': 'Figure 1: Axial Flux Topology',
        'subtitle': 'Dual-rotor configuration with\nexploded view and flux paths'
    },
    {
        'filename': 'charge_configurations.png',
        'title': 'Figure 2: Charge Configurations',
        'subtitle': 'Six fundamental charge interaction\ncases with force vectors'
    },
    {
        'filename': 'force_magnitude_comparison.png',
        'title': 'Figure 3: Force Comparison',
        'subtitle': 'Logarithmic plot spanning\n42 orders of magnitude'
    },
    {
        'filename': 'feynman_diagram.png',
        'title': 'Figure 4: Feynman Diagrams',
        'subtitle': 'Virtual photon exchange and\nQED corrections'
    },
    {
        'filename': 'dual_rotor_schematic.png',
        'title': 'Figure 5: Dual-Rotor Schematic',
        'subtitle': 'Cross-section and 3D view with\nmagnet pole arrangement'
    },
    {
        'filename': 'performance_comparison.png',
        'title': 'Figure 6: Performance Comparison',
        'subtitle': 'Current, power density, cost\nand efficiency analysis'
    },
    {
        'filename': 'ev_motor_placement.png',
        'title': 'Figure 7: EV Motor Placement',
        'subtitle': 'Ferrari SF90 motor configuration\nwith power distribution'
    },
    {
        'filename': 'efficiency_breakdown.png',
        'title': 'Figure 8: Efficiency Breakdown',
        'subtitle': 'Loss mechanisms and thermal\nanalysis comparison'
    }
]

def create_placeholder(filename, title, subtitle):
    """Create a professional-looking placeholder image"""
    
    # Image dimensions
    width, height = 1200, 800
    
    # Create white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    border_color = (100, 100, 100)
    draw.rectangle([20, 20, width-20, height-20], outline=border_color, width=4)
    
    # Draw diagonal lines (draft pattern)
    for i in range(-height, width, 50):
        draw.line([(i, 0), (i + height, height)], fill=(230, 230, 230), width=1)
    
    # Draw inner box
    draw.rectangle([100, 100, width-100, height-100], outline=border_color, width=2)
    
    # Try to use a nice font, fall back to default if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 28)
        label_font = ImageFont.truetype("arial.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
    
    # Draw title
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 200), title, fill=(0, 0, 0), font=title_font)
    
    # Draw subtitle (handle multiline)
    subtitle_y = 280
    for line in subtitle.split('\n'):
        line_bbox = draw.textbbox((0, 0), line, font=subtitle_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        draw.text((line_x, subtitle_y), line, fill=(80, 80, 80), font=subtitle_font)
        subtitle_y += 40
    
    # Draw placeholder label
    label_text = "[Placeholder - Replace with actual figure]"
    label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_width = label_bbox[2] - label_bbox[0]
    label_x = (width - label_width) // 2
    draw.text((label_x, height - 150), label_text, fill=(150, 150, 150), font=label_font)
    
    # Draw image icon (simple representation)
    icon_size = 60
    icon_x = (width - icon_size) // 2
    icon_y = 450
    draw.rectangle([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], 
                   outline=(180, 180, 180), width=3)
    draw.line([icon_x, icon_y + icon_size, icon_x + icon_size//2, icon_y + icon_size//2], 
              fill=(180, 180, 180), width=2)
    draw.line([icon_x + icon_size//2, icon_y + icon_size//2, icon_x + icon_size, icon_y + icon_size], 
              fill=(180, 180, 180), width=2)
    draw.ellipse([icon_x + 10, icon_y + 10, icon_x + 25, icon_y + 25], 
                 outline=(180, 180, 180), width=2)
    
    # Save the image
    filepath = os.path.join('figures', filename)
    img.save(filepath, 'PNG', dpi=(300, 300))
    print(f"✓ Created: {filepath}")

def main():
    print("=" * 60)
    print("Creating Placeholder Figures for LaTeX Paper")
    print("=" * 60)
    print()
    
    for fig in figures:
        create_placeholder(fig['filename'], fig['title'], fig['subtitle'])
    
    print()
    print("=" * 60)
    print("✅ All 8 placeholder figures created successfully!")
    print("=" * 60)
    print()
    print("📂 Location: figures/")
    print("📄 Your paper.tex can now be compiled!")
    print()
    print("Next steps:")
    print("1. Upload paper.tex and figures/ folder to Overleaf")
    print("2. Or compile locally with: pdflatex paper.tex")
    print("3. Replace placeholders with actual figures later")
    print()

if __name__ == "__main__":
    main()
