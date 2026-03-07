#!/usr/bin/env python3
"""
PERMANENT MAGNET GENERATOR - MAIN SIMULATION RUNNER
=====================================================
Project Magnetism: High-Efficiency PMG Design

This is the main entry point for running the complete generator simulation.

Usage:
    python main.py                    # Run with defaults
    python main.py --rpm 3000         # Specify RPM
    python main.py --power 1000       # Specify target power
    python main.py --optimize         # Run optimization
    python main.py --report-only      # Generate reports without simulation

Author: Project Magnetism Team
Date: 2024
"""

import sys
import os
import argparse
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import project modules
from physics.constants import N52_NEODYMIUM, BR_NEODYMIUM
from physics.energy_balance import (GeneratorSpecs, calculate_efficiency, 
                                    calculate_all_losses, energy_conservation_proof,
                                    EnergyFlowDiagram)
from physics.coulomb_forces import compare_charge_forces_all_cases

from simulation.rotor_dynamics import RotorParameters
from simulation.cogging_analysis import (GeneratorGeometry, 
                                         generate_anti_cogging_report,
                                         optimize_pole_slot_combination,
                                         halbach_array_design)
from simulation.resonance_analysis import (MechanicalSystem,
                                           generate_resonance_report,
                                           calculate_Campbell_diagram)
from simulation.full_system_sim import (GeneratorInputs, run_full_simulation,
                                        analyze_results, generate_full_report)

from optimization.genetic_optimizer import (GeneticOptimizer, DesignParameters,
                                            quick_optimize)
from optimization.loss_minimizer import LossMinimizer, LossBreakdown


def print_header():
    """Print program header"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗               ║
║     ██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝               ║
║     ██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║                  ║
║     ██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║                  ║
║     ██║     ██║  ██║╚██████╔╝╚█████╔╝███████╗╚██████╗   ██║                  ║
║     ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚════╝ ╚══════╝ ╚═════╝   ╚═╝                  ║
║                                                                              ║
║                      M A G N E T I S M                                       ║
║                                                                              ║
║             High-Efficiency Permanent Magnet Generator                       ║
║                    Design & Simulation Suite                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def answer_charge_question():
    """Answer the original question about charge forces"""
    print("\n" + "=" * 70)
    print("ANSWER TO YOUR ORIGINAL QUESTION: CHARGE FORCE ASYMMETRIES")
    print("=" * 70)
    
    # Calculate at 1cm distance
    results = compare_charge_forces_all_cases(r=0.01)
    
    print(f"\nDistance: {results['distance_cm']:.1f} cm")
    print("\n" + "-" * 50)
    
    print("\nCASE 1: Two Positive Charges (+e, +e)")
    case1 = results["case_1_pos_pos"]
    print(f"  Direction: {case1['direction']}")
    print(f"  Classical Force: {case1['F_classical']:.4e} N")
    print(f"  If electrons: {case1['F_total_electrons']:.4e} N")
    print(f"  If protons:   {case1['F_total_protons']:.4e} N")
    print(f"  DIFFERENCE:   {case1['difference_e_vs_p']:.4e} N")
    
    print("\nCASE 2: Two Negative Charges (-e, -e)")
    case2 = results["case_2_neg_neg"]
    print(f"  Direction: {case2['direction']}")
    print(f"  Total Force: {case2['F_total']:.4e} N")
    
    print("\nCASE 3: Opposite Charges (+e, -e)")
    case3 = results["case_3_pos_neg"]
    print(f"  Direction: {case3['direction']}")
    print(f"  Total Force: {case3['F_total']:.4e} N")
    
    print("\nCASE 4 & 5: Charge + Neutral")
    case4 = results["case_4_pos_neutral"]
    print(f"  Direction: {case4['direction']}")
    print(f"  Force: {case4['F_polarization']:.4e} N")
    
    print("\nCASE 6: Both Neutral")
    case6 = results["case_6_neutral_neutral"]
    print(f"  Direction: {case6['direction']}")
    print(f"  Force: {case6['F_vdw']:.4e} N")
    
    print("\n" + "=" * 50)
    print("KEY FINDING:")
    print("=" * 50)
    key = results["KEY_FINDING"]
    print(f"\n{key['message']}")
    print(f"\nDifference: {key['difference']:.4e} N")
    print(f"Ratio: {key['ratio']:.1f}×")
    print(f"\nReason: {key['reason']}")
    print("\n" + "=" * 70)


def run_quick_design(target_power: float, target_rpm: float):
    """Run quick design optimization"""
    print("\n" + "=" * 70)
    print(f"QUICK DESIGN: {target_power} W @ {target_rpm} RPM")
    print("=" * 70)
    
    design = quick_optimize(target_power, target_rpm)
    
    print(f"\nOptimal Design:")
    print(f"  Poles: {design.n_poles}")
    print(f"  Slots: {design.n_slots}")
    print(f"  Rotor radius: {design.rotor_radius*1000:.1f} mm")
    print(f"  Axial length: {design.axial_length*1000:.0f} mm")
    print(f"  Magnet arc: {design.magnet_arc:.2f}")
    print(f"  Skew angle: {design.skew_angle:.1f}°")
    print(f"  Turns per coil: {design.n_turns}")
    
    return design


def run_full_analysis(inputs: GeneratorInputs):
    """Run complete generator analysis"""
    
    print("\n" + "=" * 70)
    print("STARTING FULL GENERATOR ANALYSIS")
    print("=" * 70)
    
    # 1. Run dynamic simulation
    print("\n[1/5] Running time-domain simulation...")
    results = run_full_simulation(inputs)
    
    # 2. Analyze results
    print("\n[2/5] Analyzing results...")
    analysis = analyze_results(results, inputs)
    
    # 3. Generate cogging report
    print("\n[3/5] Analyzing cogging torque...")
    geom = GeneratorGeometry(
        n_poles=inputs.n_poles,
        n_slots=inputs.n_slots,
        rotor_radius=inputs.rotor_radius,
        stator_radius=inputs.stator_radius,
        magnet_arc=0.85,
        skew_angle=inputs.skew_angle
    )
    cogging_report = generate_anti_cogging_report(geom)
    
    # 4. Generate resonance report
    print("\n[4/5] Analyzing resonance conditions...")
    mech = MechanicalSystem(
        rotor_mass=inputs.rotor_mass,
        rotor_radius=inputs.rotor_radius,
        shaft_radius=inputs.shaft_radius,
        n_poles=inputs.n_poles,
        n_slots=inputs.n_slots
    )
    resonance_report = generate_resonance_report(mech, inputs.target_rpm)
    
    # 5. Generate main report
    print("\n[5/5] Generating reports...")
    main_report = generate_full_report(results, inputs, analysis)
    
    # Print all reports
    print("\n" + main_report)
    print(cogging_report)
    print(resonance_report)
    
    # Energy conservation proof
    print(energy_conservation_proof())
    
    return results, analysis


def run_optimization():
    """Run genetic algorithm optimization"""
    print("\n" + "=" * 70)
    print("RUNNING GENETIC ALGORITHM OPTIMIZATION")
    print("=" * 70)
    
    optimizer = GeneticOptimizer(
        population_size=30,
        n_generations=50,
        mutation_rate=0.15
    )
    
    best = optimizer.run()
    
    return best


def generate_reports_only():
    """Generate example reports without full simulation"""
    print("\n" + "=" * 70)
    print("GENERATING EXAMPLE REPORTS")
    print("=" * 70)
    
    # Cogging report for common configurations
    print("\n--- COGGING ANALYSIS (12-pole, 18-slot) ---")
    geom = GeneratorGeometry(n_poles=12, n_slots=18)
    print(generate_anti_cogging_report(geom))
    
    # Halbach array design
    print("\n--- HALBACH ARRAY DESIGN ---")
    halbach = halbach_array_design(12, segments_per_pole=4)
    print(f"Magnets: {halbach['n_magnets']}")
    print(f"Field concentration: {halbach['field_concentration_factor']:.2f}×")
    print(f"Cogging reduction: {100*halbach['cogging_reduction']:.0f}%")
    
    # Best pole-slot combinations
    print("\n--- OPTIMAL POLE-SLOT COMBINATIONS ---")
    combos = optimize_pole_slot_combination(1000)[:10]
    print(f"{'Poles':<6} {'Slots':<6} {'Cog Order':<10} {'q':<8} {'Recommended'}")
    print("-" * 45)
    for c in combos:
        rec = "✓" if c["recommended"] else ""
        print(f"{c['poles']:<6} {c['slots']:<6} {c['cogging_order']:<10} "
              f"{c['slots_per_pole_per_phase']:<8.2f} {rec}")
    
    # Resonance for typical design
    print("\n--- RESONANCE ANALYSIS (3000 RPM) ---")
    mech = MechanicalSystem()
    print(generate_resonance_report(mech, 3000))
    
    # Energy flow example
    print("\n--- ENERGY FLOW DIAGRAM ---")
    flow = EnergyFlowDiagram(
        input_mechanical_W=1100,
        output_electrical_W=1000,
        copper_loss_W=30,
        iron_loss_W=40,
        friction_loss_W=15,
        windage_loss_W=15
    )
    print(flow)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Permanent Magnet Generator Design & Simulation Suite"
    )
    
    parser.add_argument("--rpm", type=float, default=3000,
                       help="Target operating RPM (default: 3000)")
    parser.add_argument("--power", type=float, default=1000,
                       help="Target output power in Watts (default: 1000)")
    parser.add_argument("--optimize", action="store_true",
                       help="Run genetic algorithm optimization")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick heuristic design")
    parser.add_argument("--report-only", action="store_true",
                       help="Generate example reports only")
    parser.add_argument("--charge-question", action="store_true",
                       help="Answer the charge force question")
    parser.add_argument("--no-plots", action="store_true",
                       help="Skip generating plots")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Output directory for results")
    
    args = parser.parse_args()
    
    # Print header
    print_header()
    
    # Always answer the charge question first
    answer_charge_question()
    
    if args.charge_question:
        return
    
    if args.report_only:
        generate_reports_only()
        return
    
    if args.optimize:
        best_design = run_optimization()
        # Create inputs from optimized design
        inputs = GeneratorInputs(
            n_poles=best_design.n_poles,
            n_slots=best_design.n_slots,
            rotor_radius=best_design.rotor_radius,
            magnet_arc=best_design.magnet_arc,
            skew_angle=best_design.skew_angle,
            axial_length=best_design.axial_length,
            n_turns=best_design.n_turns,
            target_rpm=args.rpm
        )
    elif args.quick:
        design = run_quick_design(args.power, args.rpm)
        inputs = GeneratorInputs(
            n_poles=design.n_poles,
            n_slots=design.n_slots,
            rotor_radius=design.rotor_radius,
            magnet_arc=design.magnet_arc,
            skew_angle=design.skew_angle,
            axial_length=design.axial_length,
            n_turns=design.n_turns,
            target_rpm=args.rpm
        )
    else:
        # Use defaults
        inputs = GeneratorInputs(target_rpm=args.rpm)
    
    # Run full analysis
    results, analysis = run_full_analysis(inputs)
    
    # Generate plots
    if not args.no_plots:
        print("\nGenerating plots...")
        try:
            from visualization.plot_results import create_all_plots
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            create_all_plots(results, inputs, str(output_dir))
            print(f"Plots saved to: {output_dir}")
        except ImportError as e:
            print(f"Could not create plots (matplotlib not installed): {e}")
        except Exception as e:
            print(f"Error creating plots: {e}")
    
    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)
    print(f"\nFinal Efficiency: {analysis['power']['efficiency_percent']:.1f}%")
    print(f"Output Power: {analysis['power']['electrical_output_W']:.1f} W")
    print(f"Operating Speed: {analysis['steady_state']['rpm_mean']:.0f} RPM")
    
    print("\n📁 Check 'cad/' folder for OpenSCAD 3D models")
    print("📊 Check 'output/' folder for plots (if generated)")
    print("\n👋 Thank you for using Project Magnetism!\n")


if __name__ == "__main__":
    main()
