"""
ULTIMATE NEXT-GENERATION PM GENERATOR DESIGN
============================================

This module integrates ALL cutting-edge technologies into one design:

1. MAGNETIC BEARINGS - Zero friction (no mechanical contact)
2. NANOCRYSTALLINE CORE - 90% lower core losses
3. HALBACH ARRAY MAGNETS - Stronger field, less cogging
4. ACTIVE RECTIFICATION - 99% conversion efficiency
5. MPPT - Maximum energy capture
6. LIQUID COOLING - Higher power density
7. ANTI-COGGING OPTIMIZATION - Smooth, vibration-free operation

This represents the absolute state-of-the-art as of 2026.

PERFORMANCE TARGETS:
- Overall efficiency: >96% (vs 85% conventional)
- Cogging torque: <1% of rated torque
- Power density: >5 kW/kg (vs 1-2 kW/kg conventional)
- Lifetime: >100,000 hours (vs 20,000 hours conventional)
- Maintenance: Near-zero (magnetic bearings, no lubricants)

APPLICATIONS:
- High-efficiency wind turbines
- Aerospace generators
- Premium electric vehicles
- Industrial automation
- Research equipment
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto

# Import all our advanced modules
from physics.advanced_materials import (
    CoreMaterial, MagnetMaterial, ConductorMaterial, BearingTechnology, CoolingSystem,
    NANOCRYSTALLINE, METGLAS_2605SA1, HIPERCO_50,
    N52, N48SH, SM2CO17,
    COPPER_ANNEALED, LITZ_WIRE, YBCO_HTS,
    MAGNETIC_BEARING_ACTIVE, CERAMIC_HYBRID_BEARING,
    LIQUID_JACKET, TWO_PHASE_COOLING,
    select_optimal_materials
)
from physics.magnetic_bearings import (
    PassiveMagneticBearing, ActiveMagneticBearing, 
    HybridMagneticBearingSystem, design_magnetic_bearing_for_generator
)
from physics.power_electronics import (
    AdvancedPowerElectronicsSystem, GeneratorMPPT, ActiveRectifier
)
from physics.thermal_management import (
    GeneratorLosses, ThermalNetwork, ThermalSimulator,
    LiquidCoolingJacket, CoolingType
)
from simulation.cogging_analysis import (
    CoggingAnalyzer, GeneratorGeometry, find_optimal_pole_slot_combination
)


class TechnologyLevel(Enum):
    """Technology level selection."""
    CONVENTIONAL = auto()  # Current commercial technology
    ADVANCED = auto()      # Best available today (2026)
    CUTTING_EDGE = auto()  # Lab/prototype stage
    FUTURISTIC = auto()    # Theoretical/experimental


@dataclass
class UltimateGeneratorSpecs:
    """Complete specifications for the ultimate generator."""
    
    # Performance targets
    target_power_W: float = 1000.0
    target_rpm: float = 2000.0
    target_efficiency: float = 0.96
    
    # Technology level
    tech_level: TechnologyLevel = TechnologyLevel.ADVANCED
    
    # Override specific technologies
    use_magnetic_bearings: bool = True
    use_superconducting_windings: bool = False  # Only at FUTURISTIC level
    use_halbach_magnets: bool = True
    use_active_rectifier: bool = True
    use_liquid_cooling: bool = True
    
    # Geometry constraints
    max_outer_diameter_mm: float = 200.0
    max_length_mm: float = 150.0
    max_mass_kg: float = 15.0


@dataclass
class DesignResult:
    """Complete design result."""
    
    # Core design
    n_poles: int = 12
    n_slots: int = 18
    rotor_od_mm: float = 100.0
    rotor_id_mm: float = 40.0
    stator_od_mm: float = 160.0
    stator_id_mm: float = 102.0
    active_length_mm: float = 80.0
    air_gap_mm: float = 1.0
    
    # Materials
    core_material: str = "Nanocrystalline"
    magnet_material: str = "N52 NdFeB"
    conductor_material: str = "Litz Wire"
    
    # Performance
    power_output_W: float = 1000.0
    efficiency: float = 0.96
    cogging_torque_percent: float = 0.5
    power_density_kW_kg: float = 5.0
    
    # Systems
    bearing_type: str = "Hybrid Magnetic"
    cooling_type: str = "Liquid Jacket"
    electronics_efficiency: float = 0.98
    
    # Losses breakdown
    copper_loss_W: float = 20.0
    core_loss_W: float = 10.0
    bearing_loss_W: float = 1.0
    electronics_loss_W: float = 10.0
    total_loss_W: float = 41.0
    
    # Cost estimate
    estimated_cost_usd: float = 5000.0


class UltimateGeneratorDesigner:
    """
    Master designer class that integrates all subsystems.
    
    This is the main entry point for designing a next-generation generator.
    """
    
    def __init__(self, specs: UltimateGeneratorSpecs):
        """Initialize designer with specifications."""
        self.specs = specs
        self.design_history: List[DesignResult] = []
    
    def design(self) -> DesignResult:
        """
        Execute complete design process.
        
        Returns:
            Optimized generator design
        """
        print("\n" + "="*70)
        print("ULTIMATE NEXT-GENERATION PM GENERATOR DESIGN")
        print("="*70)
        print(f"Target: {self.specs.target_power_W}W @ {self.specs.target_rpm} RPM")
        print(f"Efficiency target: {self.specs.target_efficiency*100:.1f}%")
        print(f"Technology level: {self.specs.tech_level.name}")
        print("="*70)
        
        result = DesignResult()
        
        # Step 1: Electromagnetic design (poles, slots, geometry)
        print("\n📐 STEP 1: Electromagnetic Design")
        print("-"*50)
        result = self._design_electromagnetics(result)
        
        # Step 2: Material selection
        print("\n🧪 STEP 2: Material Selection")
        print("-"*50)
        result = self._select_materials(result)
        
        # Step 3: Anti-cogging optimization
        print("\n🔧 STEP 3: Anti-Cogging Optimization")
        print("-"*50)
        result = self._optimize_cogging(result)
        
        # Step 4: Bearing system design
        print("\n⚙️ STEP 4: Bearing System Design")
        print("-"*50)
        result = self._design_bearings(result)
        
        # Step 5: Thermal management
        print("\n🌡️ STEP 5: Thermal Management")
        print("-"*50)
        result = self._design_cooling(result)
        
        # Step 6: Power electronics
        print("\n⚡ STEP 6: Power Electronics")
        print("-"*50)
        result = self._design_electronics(result)
        
        # Step 7: Integration and validation
        print("\n✅ STEP 7: System Integration")
        print("-"*50)
        result = self._integrate_systems(result)
        
        # Store result
        self.design_history.append(result)
        
        return result
    
    def _design_electromagnetics(self, result: DesignResult) -> DesignResult:
        """Design electromagnetic circuit."""
        
        # Calculate required torque
        omega = self.specs.target_rpm * 2 * np.pi / 60
        torque_Nm = self.specs.target_power_W / omega
        
        print(f"  Required torque: {torque_Nm:.2f} Nm")
        
        # Size rotor based on shear stress (typical: 20-40 kN/m² for PM machines)
        shear_stress = 35000  # N/m² (aggressive for high-performance)
        
        # Rotor volume needed: V = T / (2 * σ)
        V_rotor = torque_Nm / (2 * shear_stress)
        
        # Assume L/D ratio of 0.5
        D_rotor = (4 * V_rotor / (0.5 * np.pi))**(1/3)
        L_active = 0.5 * D_rotor
        
        # Convert to mm
        result.rotor_od_mm = D_rotor * 1000
        result.active_length_mm = L_active * 1000
        
        # Inner diameter (~40% of outer for optimal)
        result.rotor_id_mm = result.rotor_od_mm * 0.4
        
        # Air gap (mechanical clearance + magnetic optimization)
        result.air_gap_mm = max(0.5, result.rotor_od_mm * 0.01)  # ~1% of diameter
        
        # Stator sizing
        result.stator_id_mm = result.rotor_od_mm + 2 * result.air_gap_mm
        result.stator_od_mm = result.stator_id_mm * 1.6  # Typical ratio
        
        # Pole-slot selection for low cogging
        # Use our anti-cogging algorithm
        best_combo = find_optimal_pole_slot_combination(
            min_poles=8, max_poles=20,
            min_slots=9, max_slots=36,
            target_power=self.specs.target_power_W
        )
        
        result.n_poles = best_combo['poles']
        result.n_slots = best_combo['slots']
        
        print(f"  Rotor OD: {result.rotor_od_mm:.1f} mm")
        print(f"  Active length: {result.active_length_mm:.1f} mm")
        print(f"  Air gap: {result.air_gap_mm:.2f} mm")
        print(f"  Poles/Slots: {result.n_poles}/{result.n_slots}")
        print(f"  LCM: {best_combo['lcm']} (higher = less cogging)")
        
        return result
    
    def _select_materials(self, result: DesignResult) -> DesignResult:
        """Select optimal materials based on technology level."""
        
        # Get recommendations
        allow_experimental = self.specs.tech_level in [
            TechnologyLevel.CUTTING_EDGE, TechnologyLevel.FUTURISTIC
        ]
        
        recommendations = select_optimal_materials(
            target_efficiency=self.specs.target_efficiency,
            max_cost_factor=50 if allow_experimental else 10,
            max_temp_C=120,
            allow_experimental=allow_experimental
        )
        
        result.core_material = recommendations['core_material'].name
        result.magnet_material = recommendations['magnet_material'].name
        
        # Conductor selection
        if self.specs.use_superconducting_windings and self.specs.tech_level == TechnologyLevel.FUTURISTIC:
            result.conductor_material = "YBCO HTS"
        else:
            result.conductor_material = "Litz Wire"
        
        print(f"  Core: {result.core_material}")
        print(f"  Magnets: {result.magnet_material}")
        print(f"  Conductor: {result.conductor_material}")
        
        return result
    
    def _optimize_cogging(self, result: DesignResult) -> DesignResult:
        """Optimize anti-cogging features."""
        
        geometry = GeneratorGeometry(
            n_poles=result.n_poles,
            n_slots=result.n_slots,
            magnet_arc_deg=0.8 * 360 / result.n_poles,  # 80% pole coverage
        )
        
        analyzer = CoggingAnalyzer(geometry)
        
        # Find optimal skew
        optimal_skew = analyzer.optimize_skew_angle()
        
        # Calculate cogging with optimization
        baseline_cogging = analyzer.calculate_cogging_amplitude(skew_angle_deg=0)
        optimized_cogging = analyzer.calculate_cogging_amplitude(skew_angle_deg=optimal_skew)
        
        # Apply Halbach if enabled
        if self.specs.use_halbach_magnets:
            optimized_cogging *= 0.7  # Halbach reduces cogging by ~30%
        
        # Calculate as percentage of rated torque
        omega = self.specs.target_rpm * 2 * np.pi / 60
        rated_torque = self.specs.target_power_W / omega
        
        result.cogging_torque_percent = optimized_cogging / rated_torque * 100
        
        print(f"  Optimal skew angle: {optimal_skew:.2f}°")
        print(f"  Baseline cogging: {baseline_cogging:.3f} Nm")
        print(f"  Optimized cogging: {optimized_cogging:.3f} Nm")
        print(f"  Cogging as % of rated: {result.cogging_torque_percent:.2f}%")
        if self.specs.use_halbach_magnets:
            print(f"  Halbach array: Enabled (additional 30% reduction)")
        
        return result
    
    def _design_bearings(self, result: DesignResult) -> DesignResult:
        """Design bearing system."""
        
        if self.specs.use_magnetic_bearings:
            # Estimate rotor mass
            V_rotor = np.pi * (result.rotor_od_mm/2000)**2 * (result.active_length_mm/1000)
            rho_rotor = 7500  # kg/m³ (steel + magnets)
            rotor_mass = V_rotor * rho_rotor
            
            # Design hybrid magnetic bearing
            bearing_system = design_magnetic_bearing_for_generator(
                rotor_mass_kg=rotor_mass,
                rotor_od_mm=result.rotor_od_mm,
                max_speed_rpm=self.specs.target_rpm * 1.5,  # 50% margin
                axial_thrust_N=30
            )
            
            specs = bearing_system.get_system_specifications()
            
            result.bearing_type = "Hybrid Magnetic"
            result.bearing_loss_W = specs['total_power_consumption_W']
            
            print(f"  Bearing type: {result.bearing_type}")
            print(f"  Bearing power: {result.bearing_loss_W:.1f} W")
            print(f"  Friction coefficient: 0 (contactless!)")
        else:
            result.bearing_type = "Ceramic Hybrid"
            result.bearing_loss_W = 5.0  # Estimate
            print(f"  Bearing type: {result.bearing_type}")
            print(f"  Bearing loss: {result.bearing_loss_W:.1f} W")
        
        return result
    
    def _design_cooling(self, result: DesignResult) -> DesignResult:
        """Design thermal management system."""
        
        if self.specs.use_liquid_cooling:
            # Design liquid cooling jacket
            jacket = LiquidCoolingJacket(
                stator_od_mm=result.stator_od_mm,
                flow_rate_lpm=5.0
            )
            
            specs = jacket.get_specifications()
            
            result.cooling_type = "Liquid Jacket"
            print(f"  Cooling type: {result.cooling_type}")
            print(f"  Heat capacity: {specs['heat_capacity_W']:.0f} W")
            print(f"  Thermal resistance: {specs['thermal_resistance_K_W']:.3f} K/W")
        else:
            result.cooling_type = "Forced Air"
            print(f"  Cooling type: {result.cooling_type}")
        
        return result
    
    def _design_electronics(self, result: DesignResult) -> DesignResult:
        """Design power electronics."""
        
        if self.specs.use_active_rectifier:
            # Advanced power electronics
            pe_system = AdvancedPowerElectronicsSystem()
            
            eff_result = pe_system.calculate_system_efficiency(
                self.specs.target_power_W,
                self.specs.target_rpm
            )
            
            result.electronics_efficiency = eff_result['total_efficiency']
            result.electronics_loss_W = eff_result['total_losses_W']
            
            print(f"  Rectifier: SiC Active (Synchronous)")
            print(f"  DC-DC: LLC Resonant with ZVS")
            print(f"  MPPT: Perturb & Observe")
            print(f"  Electronics efficiency: {result.electronics_efficiency*100:.1f}%")
        else:
            result.electronics_efficiency = 0.85
            result.electronics_loss_W = self.specs.target_power_W * 0.15
            print(f"  Rectifier: Diode Bridge")
            print(f"  Electronics efficiency: 85%")
        
        return result
    
    def _integrate_systems(self, result: DesignResult) -> DesignResult:
        """Integrate all systems and calculate final performance."""
        
        # Calculate losses
        losses = GeneratorLosses(
            stator_outer_radius_mm=result.stator_od_mm / 2,
            stator_inner_radius_mm=result.stator_id_mm / 2,
            rotor_outer_radius_mm=result.rotor_od_mm / 2,
            active_length_mm=result.active_length_mm,
            n_poles=result.n_poles,
            n_slots=result.n_slots
        )
        
        # Estimate current from power
        V_estimate = 50  # V
        I_estimate = self.specs.target_power_W / (V_estimate * 0.9)
        
        loss_data = losses.total_loss(I_estimate, self.specs.target_rpm)
        
        result.copper_loss_W = loss_data['copper_W']
        result.core_loss_W = loss_data['core_W']
        
        # Apply material improvements
        if "Nanocrystalline" in result.core_material:
            result.core_loss_W *= 0.1  # 90% reduction
        elif "Metglas" in result.core_material:
            result.core_loss_W *= 0.2  # 80% reduction
        
        # Total losses
        result.total_loss_W = (result.copper_loss_W + result.core_loss_W + 
                              result.bearing_loss_W + loss_data['windage_W'])
        
        # Account for electronics
        generator_efficiency = self.specs.target_power_W / (self.specs.target_power_W + result.total_loss_W)
        result.efficiency = generator_efficiency * result.electronics_efficiency
        
        # Power output
        input_power = self.specs.target_power_W / result.efficiency
        result.power_output_W = self.specs.target_power_W
        
        # Mass estimate
        V_total = np.pi * (result.stator_od_mm/2000)**2 * (result.active_length_mm/1000)
        mass_kg = V_total * 5000  # Approximate average density
        result.power_density_kW_kg = result.power_output_W / 1000 / mass_kg
        
        # Cost estimate (rough)
        base_cost = 500  # Base manufacturing
        material_cost = mass_kg * 50  # $50/kg average
        electronics_cost = result.power_output_W * 0.5  # $0.50/W
        if self.specs.use_magnetic_bearings:
            bearing_cost = 1000
        else:
            bearing_cost = 100
        
        result.estimated_cost_usd = base_cost + material_cost + electronics_cost + bearing_cost
        
        print(f"\n  FINAL PERFORMANCE:")
        print(f"  ─────────────────────────────")
        print(f"  Power output:     {result.power_output_W:.0f} W")
        print(f"  Overall efficiency: {result.efficiency*100:.1f}%")
        print(f"  Cogging torque:   {result.cogging_torque_percent:.2f}%")
        print(f"  Power density:    {result.power_density_kW_kg:.1f} kW/kg")
        print(f"  Estimated cost:   ${result.estimated_cost_usd:.0f}")
        
        print(f"\n  LOSS BREAKDOWN:")
        print(f"  ─────────────────────────────")
        print(f"  Copper losses:    {result.copper_loss_W:.1f} W")
        print(f"  Core losses:      {result.core_loss_W:.1f} W")
        print(f"  Bearing losses:   {result.bearing_loss_W:.1f} W")
        print(f"  Electronics:      {result.electronics_loss_W:.1f} W")
        print(f"  Total losses:     {result.total_loss_W + result.electronics_loss_W:.1f} W")
        
        return result
    
    def generate_report(self, result: DesignResult) -> str:
        """Generate comprehensive design report."""
        
        report = []
        report.append("="*70)
        report.append("ULTIMATE PM GENERATOR DESIGN REPORT")
        report.append("="*70)
        report.append("")
        
        report.append("1. DESIGN SPECIFICATIONS")
        report.append("-"*50)
        report.append(f"   Target Power:          {self.specs.target_power_W} W")
        report.append(f"   Target Speed:          {self.specs.target_rpm} RPM")
        report.append(f"   Technology Level:      {self.specs.tech_level.name}")
        report.append("")
        
        report.append("2. ELECTROMAGNETIC DESIGN")
        report.append("-"*50)
        report.append(f"   Number of Poles:       {result.n_poles}")
        report.append(f"   Number of Slots:       {result.n_slots}")
        report.append(f"   Rotor OD:             {result.rotor_od_mm:.1f} mm")
        report.append(f"   Stator OD:            {result.stator_od_mm:.1f} mm")
        report.append(f"   Active Length:        {result.active_length_mm:.1f} mm")
        report.append(f"   Air Gap:              {result.air_gap_mm:.2f} mm")
        report.append("")
        
        report.append("3. MATERIALS")
        report.append("-"*50)
        report.append(f"   Core Material:        {result.core_material}")
        report.append(f"   Magnet Material:      {result.magnet_material}")
        report.append(f"   Conductor:            {result.conductor_material}")
        report.append("")
        
        report.append("4. SUBSYSTEMS")
        report.append("-"*50)
        report.append(f"   Bearing System:       {result.bearing_type}")
        report.append(f"   Cooling System:       {result.cooling_type}")
        report.append(f"   Power Electronics:    {'Active Rect + LLC ZVS' if self.specs.use_active_rectifier else 'Standard'}")
        report.append("")
        
        report.append("5. PERFORMANCE")
        report.append("-"*50)
        report.append(f"   Power Output:         {result.power_output_W:.0f} W")
        report.append(f"   Overall Efficiency:   {result.efficiency*100:.1f}%")
        report.append(f"   Cogging Torque:       {result.cogging_torque_percent:.2f}%")
        report.append(f"   Power Density:        {result.power_density_kW_kg:.1f} kW/kg")
        report.append("")
        
        report.append("6. COMPARISON WITH CONVENTIONAL")
        report.append("-"*50)
        conv_eff = 0.85
        report.append(f"   Conventional efficiency:  {conv_eff*100:.0f}%")
        report.append(f"   This design efficiency:   {result.efficiency*100:.1f}%")
        report.append(f"   Improvement:              +{(result.efficiency-conv_eff)*100:.1f}%")
        report.append(f"   Energy saved per year:    {(result.efficiency-conv_eff) * 8760 * result.power_output_W / 1000:.0f} kWh")
        report.append("")
        
        report.append("7. TECHNOLOGIES EMPLOYED")
        report.append("-"*50)
        techs = []
        if "Nanocrystalline" in result.core_material or "Metglas" in result.core_material:
            techs.append("✓ Advanced low-loss core materials")
        if self.specs.use_magnetic_bearings:
            techs.append("✓ Magnetic bearings (zero friction)")
        if self.specs.use_halbach_magnets:
            techs.append("✓ Halbach magnet array")
        if self.specs.use_active_rectifier:
            techs.append("✓ Active (synchronous) rectification")
            techs.append("✓ Maximum Power Point Tracking")
            techs.append("✓ Zero-Voltage Switching DC-DC")
        if self.specs.use_liquid_cooling:
            techs.append("✓ Liquid cooling jacket")
        techs.append("✓ Optimized pole-slot combination")
        techs.append("✓ Skewed magnets for low cogging")
        
        for tech in techs:
            report.append(f"   {tech}")
        
        report.append("")
        report.append("="*70)
        
        return "\n".join(report)


def compare_generations():
    """Compare conventional vs next-gen generator."""
    
    print("\n" + "="*70)
    print("GENERATIONAL COMPARISON: Conventional vs Next-Gen")
    print("="*70)
    
    target_power = 1000
    target_rpm = 2000
    
    # Conventional design
    print("\n" + "-"*70)
    print("CONVENTIONAL GENERATOR (Current Technology)")
    print("-"*70)
    
    conv_specs = UltimateGeneratorSpecs(
        target_power_W=target_power,
        target_rpm=target_rpm,
        tech_level=TechnologyLevel.CONVENTIONAL,
        use_magnetic_bearings=False,
        use_halbach_magnets=False,
        use_active_rectifier=False,
        use_liquid_cooling=False
    )
    conv_designer = UltimateGeneratorDesigner(conv_specs)
    conv_result = conv_designer.design()
    
    # Next-generation design
    print("\n" + "-"*70)
    print("NEXT-GENERATION GENERATOR (Advanced Technology)")
    print("-"*70)
    
    nextgen_specs = UltimateGeneratorSpecs(
        target_power_W=target_power,
        target_rpm=target_rpm,
        tech_level=TechnologyLevel.ADVANCED,
        use_magnetic_bearings=True,
        use_halbach_magnets=True,
        use_active_rectifier=True,
        use_liquid_cooling=True
    )
    nextgen_designer = UltimateGeneratorDesigner(nextgen_specs)
    nextgen_result = nextgen_designer.design()
    
    # Comparison table
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print(f"{'Metric':<30} {'Conventional':<20} {'Next-Gen':<20}")
    print("-"*70)
    print(f"{'Efficiency':<30} {conv_result.efficiency*100:.1f}% {' '*14} {nextgen_result.efficiency*100:.1f}%")
    print(f"{'Cogging Torque':<30} {conv_result.cogging_torque_percent:.2f}% {' '*13} {nextgen_result.cogging_torque_percent:.2f}%")
    print(f"{'Power Density':<30} {conv_result.power_density_kW_kg:.1f} kW/kg {' '*9} {nextgen_result.power_density_kW_kg:.1f} kW/kg")
    print(f"{'Bearing Friction':<30} {'Finite':<20} {'ZERO':<20}")
    print(f"{'Total Losses':<30} {conv_result.total_loss_W:.0f} W {' '*14} {nextgen_result.total_loss_W:.0f} W")
    print(f"{'Estimated Cost':<30} ${conv_result.estimated_cost_usd:.0f} {' '*12} ${nextgen_result.estimated_cost_usd:.0f}")
    print("-"*70)
    
    # Calculate improvement
    eff_improvement = (nextgen_result.efficiency - conv_result.efficiency) / conv_result.efficiency * 100
    loss_reduction = (conv_result.total_loss_W - nextgen_result.total_loss_W) / conv_result.total_loss_W * 100
    
    print(f"\nIMPROVEMENTS:")
    print(f"  Efficiency increased by:  {eff_improvement:.1f}%")
    print(f"  Losses reduced by:        {loss_reduction:.1f}%")
    print(f"  Annual energy saved:      {(nextgen_result.efficiency - conv_result.efficiency) * 8760 * target_power / 1000:.0f} kWh")
    
    return conv_result, nextgen_result


if __name__ == "__main__":
    # Run comparison
    conv, nextgen = compare_generations()
    
    # Generate full report
    print("\n")
    specs = UltimateGeneratorSpecs(target_power_W=1000, target_rpm=2000)
    designer = UltimateGeneratorDesigner(specs)
    result = designer.design()
    report = designer.generate_report(result)
    print(report)
