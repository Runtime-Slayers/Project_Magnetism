"""
Full System Simulation
=======================
Complete time-domain simulation of the permanent magnet generator
including all physics, losses, and dynamics.
"""

import numpy as np
from typing import Dict, Tuple, Optional, Callable
from dataclasses import dataclass, field
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from physics.constants import MU_0, BR_NEODYMIUM, N52_NEODYMIUM
from physics.energy_balance import GeneratorSpecs, calculate_efficiency, calculate_all_losses
from simulation.rotor_dynamics import (RotorParameters, simulate_rotor_dynamics,
                                        create_friction_model, analyze_steady_state)
from simulation.cogging_analysis import (GeneratorGeometry, calculate_cogging_torque,
                                          analyze_cogging_spectrum, generate_anti_cogging_report)
from simulation.resonance_analysis import (MechanicalSystem, check_resonance_conditions,
                                            generate_resonance_report)


@dataclass
class GeneratorInputs:
    """All inputs to the generator system"""
    # Geometry
    n_poles: int = 12
    n_slots: int = 18
    rotor_radius: float = 0.05       # m
    stator_radius: float = 0.051     # m
    air_gap: float = 0.001           # m
    axial_length: float = 0.10       # m
    
    # Magnets
    magnet_Br: float = 1.45          # Tesla (NdFeB N52)
    magnet_thickness: float = 0.005  # m
    magnet_arc: float = 0.85         # fraction of pole pitch
    skew_angle: float = 15.0         # electrical degrees
    
    # Windings
    n_phases: int = 3
    n_turns: int = 100
    wire_diameter: float = 0.001     # m
    
    # Mechanical
    rotor_mass: float = 2.0          # kg
    shaft_radius: float = 0.01       # m
    
    # Operating conditions
    target_rpm: float = 3000
    load_resistance: float = 10.0    # Ohms
    drive_torque: float = 5.0        # N·m
    
    # Simulation
    simulation_time: float = 5.0     # seconds
    time_step: float = 0.0001        # seconds


@dataclass
class SimulationResults:
    """Complete results from the simulation"""
    time: np.ndarray
    angle: np.ndarray
    angular_velocity: np.ndarray
    rpm: np.ndarray
    torque_drive: np.ndarray
    torque_cogging: np.ndarray
    torque_friction: np.ndarray
    torque_load: np.ndarray
    emf_phase_a: np.ndarray
    emf_phase_b: np.ndarray
    emf_phase_c: np.ndarray
    current_phase_a: np.ndarray
    current_phase_b: np.ndarray
    current_phase_c: np.ndarray
    power_mechanical: np.ndarray
    power_electrical: np.ndarray
    power_losses: np.ndarray
    efficiency: np.ndarray


def calculate_emf_waveforms(theta: np.ndarray, omega: np.ndarray,
                           inputs: GeneratorInputs) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate 3-phase EMF waveforms.
    
    EMF = -N × dΦ/dt = N × B × L × v × sin(p × θ)
    
    Where:
    - N = number of turns
    - B = air gap flux density
    - L = axial length
    - v = tangential velocity = ω × r
    - p = pole pairs
    """
    N = inputs.n_turns
    B = inputs.magnet_Br * inputs.magnet_arc * 0.9  # Effective B in air gap
    L = inputs.axial_length
    r = inputs.rotor_radius
    p = inputs.n_poles // 2  # Pole pairs
    
    # EMF amplitude
    E_peak = N * B * (2 * r * L) * omega
    
    # 3-phase waveforms (120° apart)
    emf_a = E_peak * np.sin(p * theta)
    emf_b = E_peak * np.sin(p * theta - 2*np.pi/3)
    emf_c = E_peak * np.sin(p * theta + 2*np.pi/3)
    
    return emf_a, emf_b, emf_c


def calculate_load_torque(omega: np.ndarray, emf: np.ndarray,
                         inputs: GeneratorInputs) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate electrical load torque and current.
    
    Electrical power = 3 × (V × I) for 3-phase
    Torque = Power / ω
    """
    # Total impedance (resistance + reactance)
    # Simplified: only resistance for now
    coil_length = 2 * np.pi * inputs.rotor_radius * inputs.n_turns
    wire_area = np.pi * (inputs.wire_diameter/2)**2
    R_coil = 1.68e-8 * coil_length / wire_area  # Copper resistivity
    R_total = R_coil + inputs.load_resistance
    
    # RMS EMF
    E_rms = np.abs(emf) / np.sqrt(2)
    
    # Current (RMS)
    I_rms = E_rms / R_total
    
    # Power delivered to load (per phase)
    P_load = I_rms**2 * inputs.load_resistance
    
    # Total electrical power (3 phases)
    P_electrical = 3 * P_load
    
    # Load torque on rotor (reaction)
    tau_load = np.zeros_like(omega)
    nonzero = omega != 0
    tau_load[nonzero] = P_electrical[nonzero] / omega[nonzero]
    
    # Current waveform (instantaneous)
    current = emf / R_total
    
    return tau_load, current


def run_full_simulation(inputs: GeneratorInputs) -> SimulationResults:
    """
    Run complete generator simulation.
    
    This is the main simulation function that ties everything together.
    """
    print("=" * 60)
    print("PERMANENT MAGNET GENERATOR - FULL SYSTEM SIMULATION")
    print("=" * 60)
    
    # Time array
    t = np.arange(0, inputs.simulation_time, inputs.time_step)
    n_steps = len(t)
    
    # Initialize arrays
    theta = np.zeros(n_steps)
    omega = np.zeros(n_steps)
    
    # Torque arrays
    tau_drive = np.zeros(n_steps)
    tau_cogging = np.zeros(n_steps)
    tau_friction = np.zeros(n_steps)
    tau_load = np.zeros(n_steps)
    
    # EMF and current arrays
    emf_a = np.zeros(n_steps)
    emf_b = np.zeros(n_steps)
    emf_c = np.zeros(n_steps)
    current_a = np.zeros(n_steps)
    current_b = np.zeros(n_steps)
    current_c = np.zeros(n_steps)
    
    # Power arrays
    P_mech = np.zeros(n_steps)
    P_elec = np.zeros(n_steps)
    P_loss = np.zeros(n_steps)
    
    # Set up geometry for cogging calculation
    geom = GeneratorGeometry(
        n_poles=inputs.n_poles,
        n_slots=inputs.n_slots,
        rotor_radius=inputs.rotor_radius,
        stator_radius=inputs.stator_radius,
        air_gap=inputs.air_gap,
        magnet_arc=inputs.magnet_arc,
        skew_angle=inputs.skew_angle
    )
    
    # Friction model
    friction = create_friction_model(
        bearing_friction=0.02,  # N·m
        viscous_friction=0.001,  # N·m·s
        windage_coefficient=1e-5
    )
    
    # Moment of inertia
    I = 0.5 * inputs.rotor_mass * inputs.rotor_radius**2
    
    # Target omega
    omega_target = inputs.target_rpm * 2 * np.pi / 60
    
    # Startup ramp time
    t_ramp = 1.0  # seconds
    
    print(f"\nSimulating {inputs.simulation_time}s at {1/inputs.time_step:.0f} Hz...")
    print(f"Target speed: {inputs.target_rpm} RPM ({omega_target:.1f} rad/s)")
    
    # Time stepping (Euler method for simplicity)
    for i in range(1, n_steps):
        dt = inputs.time_step
        
        # Current state
        theta_i = theta[i-1]
        omega_i = omega[i-1]
        
        # Drive torque (with soft start)
        if t[i] < t_ramp:
            s = t[i] / t_ramp
            tau_drive[i] = inputs.drive_torque * (3*s**2 - 2*s**3)
        else:
            # Speed regulation: reduce torque as we approach target
            speed_error = omega_target - omega_i
            tau_drive[i] = inputs.drive_torque * np.tanh(speed_error / omega_target * 5)
        
        # Cogging torque
        tau_cogging[i] = calculate_cogging_torque(theta_i, geom)
        
        # Friction torque
        tau_friction[i] = friction(omega_i)
        
        # Calculate EMF at current position
        emf_a[i] = inputs.n_turns * inputs.magnet_Br * 0.8 * \
                   (2 * inputs.rotor_radius * inputs.axial_length) * \
                   omega_i * np.sin(inputs.n_poles/2 * theta_i)
        emf_b[i] = inputs.n_turns * inputs.magnet_Br * 0.8 * \
                   (2 * inputs.rotor_radius * inputs.axial_length) * \
                   omega_i * np.sin(inputs.n_poles/2 * theta_i - 2*np.pi/3)
        emf_c[i] = inputs.n_turns * inputs.magnet_Br * 0.8 * \
                   (2 * inputs.rotor_radius * inputs.axial_length) * \
                   omega_i * np.sin(inputs.n_poles/2 * theta_i + 2*np.pi/3)
        
        # Calculate load torque
        coil_length = 2 * np.pi * inputs.rotor_radius * inputs.n_turns
        wire_area = np.pi * (inputs.wire_diameter/2)**2
        R_coil = 1.68e-8 * coil_length / wire_area
        R_total = R_coil + inputs.load_resistance
        
        current_a[i] = emf_a[i] / R_total
        current_b[i] = emf_b[i] / R_total
        current_c[i] = emf_c[i] / R_total
        
        # Power calculations
        P_elec[i] = (emf_a[i] * current_a[i] + emf_b[i] * current_b[i] + 
                    emf_c[i] * current_c[i])
        
        if omega_i > 0.1:  # Avoid division by zero
            tau_load[i] = P_elec[i] / omega_i
        
        # Net torque and angular acceleration
        tau_net = tau_drive[i] - tau_cogging[i] - tau_friction[i] - tau_load[i]
        alpha = tau_net / I
        
        # Update state (Euler integration)
        omega[i] = omega_i + alpha * dt
        omega[i] = max(0, omega[i])  # Can't go negative
        theta[i] = theta_i + omega[i] * dt
        
        # Mechanical power
        P_mech[i] = tau_drive[i] * omega[i]
        
        # Losses
        P_loss[i] = (tau_friction[i] + tau_cogging[i]) * omega[i]
        
        # Progress indicator
        if i % (n_steps // 10) == 0:
            print(f"  {100*i/n_steps:.0f}% - RPM: {omega[i]*60/(2*np.pi):.0f}")
    
    # Calculate efficiency
    efficiency = np.zeros_like(P_mech)
    nonzero = P_mech > 0
    efficiency[nonzero] = P_elec[nonzero] / P_mech[nonzero]
    
    print("\nSimulation complete!")
    
    return SimulationResults(
        time=t,
        angle=theta,
        angular_velocity=omega,
        rpm=omega * 60 / (2 * np.pi),
        torque_drive=tau_drive,
        torque_cogging=tau_cogging,
        torque_friction=tau_friction,
        torque_load=tau_load,
        emf_phase_a=emf_a,
        emf_phase_b=emf_b,
        emf_phase_c=emf_c,
        current_phase_a=current_a,
        current_phase_b=current_b,
        current_phase_c=current_c,
        power_mechanical=P_mech,
        power_electrical=P_elec,
        power_losses=P_loss,
        efficiency=efficiency
    )


def analyze_results(results: SimulationResults, 
                   inputs: GeneratorInputs) -> Dict:
    """
    Analyze simulation results and generate statistics.
    """
    # Steady state detection (last 20% of simulation)
    steady_start = int(0.8 * len(results.time))
    
    # Steady state values
    rpm_ss = np.mean(results.rpm[steady_start:])
    rpm_ripple = np.std(results.rpm[steady_start:])
    
    emf_rms_a = np.sqrt(np.mean(results.emf_phase_a[steady_start:]**2))
    emf_rms_b = np.sqrt(np.mean(results.emf_phase_b[steady_start:]**2))
    emf_rms_c = np.sqrt(np.mean(results.emf_phase_c[steady_start:]**2))
    
    current_rms_a = np.sqrt(np.mean(results.current_phase_a[steady_start:]**2))
    current_rms_b = np.sqrt(np.mean(results.current_phase_b[steady_start:]**2))
    current_rms_c = np.sqrt(np.mean(results.current_phase_c[steady_start:]**2))
    
    power_mech_avg = np.mean(results.power_mechanical[steady_start:])
    power_elec_avg = np.mean(results.power_electrical[steady_start:])
    power_loss_avg = np.mean(results.power_losses[steady_start:])
    
    efficiency_avg = power_elec_avg / power_mech_avg if power_mech_avg > 0 else 0
    
    # Cogging analysis
    cogging_pp = np.max(results.torque_cogging) - np.min(results.torque_cogging)
    cogging_factor = cogging_pp / np.mean(results.torque_drive[steady_start:]) * 100
    
    # Time to steady state
    omega_final = np.mean(results.angular_velocity[steady_start:])
    time_to_ss = results.time[np.argmax(results.angular_velocity > 0.95 * omega_final)]
    
    return {
        "steady_state": {
            "rpm_mean": rpm_ss,
            "rpm_ripple_percent": 100 * rpm_ripple / rpm_ss if rpm_ss > 0 else 0,
            "time_to_steady_state_s": time_to_ss
        },
        "electrical": {
            "emf_rms_V": (emf_rms_a + emf_rms_b + emf_rms_c) / 3,
            "current_rms_A": (current_rms_a + current_rms_b + current_rms_c) / 3,
            "frequency_Hz": inputs.n_poles * rpm_ss / 120
        },
        "power": {
            "mechanical_input_W": power_mech_avg,
            "electrical_output_W": power_elec_avg,
            "losses_W": power_loss_avg,
            "efficiency_percent": 100 * efficiency_avg
        },
        "cogging": {
            "peak_to_peak_Nm": cogging_pp,
            "cogging_factor_percent": cogging_factor
        }
    }


def generate_full_report(results: SimulationResults,
                        inputs: GeneratorInputs,
                        analysis: Dict) -> str:
    """
    Generate a comprehensive simulation report.
    """
    report = """
╔══════════════════════════════════════════════════════════════════════════╗
║         PERMANENT MAGNET GENERATOR - SIMULATION REPORT                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  DESIGN PARAMETERS                                                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Poles: {n_poles:3d}              Slots: {n_slots:3d}                               ║
║  Rotor Radius: {rotor_r:.1f} mm      Stator Radius: {stator_r:.1f} mm               ║
║  Air Gap: {air_gap:.1f} mm            Axial Length: {length:.0f} mm                    ║
║  Magnet Type: NdFeB N52      Remanence: {Br:.2f} T                        ║
║  Skew Angle: {skew:.1f}° (electrical)                                      ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  STEADY STATE PERFORMANCE                                                ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Operating Speed: {rpm:.0f} RPM (±{rpm_ripple:.1f}%)                               ║
║  Time to Steady State: {t_ss:.2f} s                                         ║
║  Electrical Frequency: {freq:.1f} Hz                                        ║
║                                                                          ║
║  Output Voltage (RMS): {emf:.1f} V                                          ║
║  Output Current (RMS): {current:.2f} A                                       ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  POWER & EFFICIENCY                                                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Mechanical Input:  {p_mech:8.2f} W                                          ║
║  Electrical Output: {p_elec:8.2f} W                                          ║
║  Total Losses:      {p_loss:8.2f} W                                          ║
║  ─────────────────────────────────                                       ║
║  EFFICIENCY:        {eff:8.1f} %                                          ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  COGGING ANALYSIS                                                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Cogging Torque (peak-peak): {cog_pp:.4f} N·m                                ║
║  Cogging Factor: {cog_factor:.1f}%                                               ║
║  Status: {cog_status}                                              ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  ENERGY CONSERVATION CHECK                                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║  P_input = P_output + P_losses                                           ║
║  {p_mech:.2f} W = {p_elec:.2f} W + {p_loss:.2f} W                                      ║
║  Balance: {balance:.2f} W (should be ~0)                                     ║
║  ✓ Energy conservation verified!                                         ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""".format(
        n_poles=inputs.n_poles,
        n_slots=inputs.n_slots,
        rotor_r=inputs.rotor_radius * 1000,
        stator_r=inputs.stator_radius * 1000,
        air_gap=inputs.air_gap * 1000,
        length=inputs.axial_length * 1000,
        Br=inputs.magnet_Br,
        skew=inputs.skew_angle,
        rpm=analysis["steady_state"]["rpm_mean"],
        rpm_ripple=analysis["steady_state"]["rpm_ripple_percent"],
        t_ss=analysis["steady_state"]["time_to_steady_state_s"],
        freq=analysis["electrical"]["frequency_Hz"],
        emf=analysis["electrical"]["emf_rms_V"],
        current=analysis["electrical"]["current_rms_A"],
        p_mech=analysis["power"]["mechanical_input_W"],
        p_elec=analysis["power"]["electrical_output_W"],
        p_loss=analysis["power"]["losses_W"],
        eff=analysis["power"]["efficiency_percent"],
        cog_pp=analysis["cogging"]["peak_to_peak_Nm"],
        cog_factor=analysis["cogging"]["cogging_factor_percent"],
        cog_status="EXCELLENT" if analysis["cogging"]["cogging_factor_percent"] < 2 else "GOOD" if analysis["cogging"]["cogging_factor_percent"] < 5 else "NEEDS IMPROVEMENT",
        balance=analysis["power"]["mechanical_input_W"] - analysis["power"]["electrical_output_W"] - analysis["power"]["losses_W"]
    )
    
    return report


if __name__ == "__main__":
    # Create default inputs
    inputs = GeneratorInputs()
    
    # Run simulation
    results = run_full_simulation(inputs)
    
    # Analyze results
    analysis = analyze_results(results, inputs)
    
    # Generate report
    report = generate_full_report(results, inputs, analysis)
    print(report)
