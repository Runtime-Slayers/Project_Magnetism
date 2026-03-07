"""
Visualization Module for PMG Simulation Results
=================================================
Plotting functions for all simulation outputs.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Optional, Tuple
from pathlib import Path


def setup_plot_style():
    """Configure matplotlib for nice plots"""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'figure.figsize': (12, 8),
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.dpi': 100
    })


def plot_rotor_dynamics(time: np.ndarray, rpm: np.ndarray,
                       torques: Dict[str, np.ndarray],
                       save_path: Optional[str] = None):
    """
    Plot rotor speed and torque components over time.
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Speed plot
    ax1 = axes[0]
    ax1.plot(time, rpm, 'b-', linewidth=1.5, label='Rotor Speed')
    ax1.set_ylabel('Speed (RPM)')
    ax1.set_title('Rotor Speed vs Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Torque plot
    ax2 = axes[1]
    colors = ['g', 'r', 'orange', 'purple']
    for (name, values), color in zip(torques.items(), colors):
        ax2.plot(time, values, color, linewidth=1, label=name, alpha=0.7)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Torque (N·m)')
    ax2.set_title('Torque Components vs Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_electrical_waveforms(time: np.ndarray,
                             emf_a: np.ndarray, emf_b: np.ndarray, emf_c: np.ndarray,
                             current_a: np.ndarray, current_b: np.ndarray, current_c: np.ndarray,
                             n_cycles: int = 5,
                             save_path: Optional[str] = None):
    """
    Plot 3-phase EMF and current waveforms.
    """
    # Find steady state region and plot just a few cycles
    start_idx = int(0.8 * len(time))
    end_idx = min(start_idx + n_cycles * 100, len(time))
    
    t = time[start_idx:end_idx] - time[start_idx]
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # EMF plot
    ax1 = axes[0]
    ax1.plot(t * 1000, emf_a[start_idx:end_idx], 'r-', label='Phase A', linewidth=1)
    ax1.plot(t * 1000, emf_b[start_idx:end_idx], 'g-', label='Phase B', linewidth=1)
    ax1.plot(t * 1000, emf_c[start_idx:end_idx], 'b-', label='Phase C', linewidth=1)
    ax1.set_ylabel('EMF (V)')
    ax1.set_title('Three-Phase EMF Waveforms (Steady State)')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Current plot
    ax2 = axes[1]
    ax2.plot(t * 1000, current_a[start_idx:end_idx], 'r-', label='Phase A', linewidth=1)
    ax2.plot(t * 1000, current_b[start_idx:end_idx], 'g-', label='Phase B', linewidth=1)
    ax2.plot(t * 1000, current_c[start_idx:end_idx], 'b-', label='Phase C', linewidth=1)
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Current (A)')
    ax2.set_title('Three-Phase Current Waveforms')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_power_efficiency(time: np.ndarray,
                         P_mech: np.ndarray, P_elec: np.ndarray, P_loss: np.ndarray,
                         efficiency: np.ndarray,
                         save_path: Optional[str] = None):
    """
    Plot power flow and efficiency over time.
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Power plot
    ax1 = axes[0]
    ax1.fill_between(time, 0, P_mech, alpha=0.3, color='blue', label='Mechanical Input')
    ax1.fill_between(time, 0, P_elec, alpha=0.3, color='green', label='Electrical Output')
    ax1.fill_between(time, 0, P_loss, alpha=0.3, color='red', label='Losses')
    ax1.plot(time, P_mech, 'b-', linewidth=1)
    ax1.plot(time, P_elec, 'g-', linewidth=1)
    ax1.set_ylabel('Power (W)')
    ax1.set_title('Power Flow')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Efficiency plot
    ax2 = axes[1]
    ax2.plot(time, efficiency * 100, 'k-', linewidth=1.5)
    ax2.fill_between(time, 0, efficiency * 100, alpha=0.2, color='green')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Efficiency (%)')
    ax2.set_title('Generator Efficiency')
    ax2.set_ylim([0, 100])
    ax2.grid(True, alpha=0.3)
    
    # Add steady-state efficiency annotation
    if len(efficiency) > 0:
        ss_eff = np.mean(efficiency[int(0.8*len(efficiency)):])
        ax2.axhline(y=ss_eff*100, color='r', linestyle='--', linewidth=1)
        ax2.annotate(f'Steady State: {ss_eff*100:.1f}%', 
                    xy=(time[-1]*0.7, ss_eff*100 + 5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_cogging_analysis(theta: np.ndarray, torque: np.ndarray,
                         harmonics: Optional[Dict] = None,
                         save_path: Optional[str] = None):
    """
    Plot cogging torque and harmonic content.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Cogging torque vs angle
    ax1 = axes[0]
    ax1.plot(np.degrees(theta), torque * 1000, 'b-', linewidth=1)
    ax1.fill_between(np.degrees(theta), 0, torque * 1000, alpha=0.2)
    ax1.set_xlabel('Rotor Angle (degrees)')
    ax1.set_ylabel('Cogging Torque (mN·m)')
    ax1.set_title('Cogging Torque vs Rotor Position')
    ax1.grid(True, alpha=0.3)
    
    # Peak-to-peak annotation
    pp = (np.max(torque) - np.min(torque)) * 1000
    ax1.annotate(f'Peak-to-Peak: {pp:.2f} mN·m', 
                xy=(180, np.max(torque)*1000), ha='center')
    
    # Harmonic spectrum
    ax2 = axes[1]
    if len(torque) > 0:
        from scipy.fft import fft
        spectrum = np.abs(fft(torque))[:len(torque)//2]
        orders = np.arange(len(spectrum))
        
        # Plot only significant harmonics
        significant = spectrum > 0.01 * np.max(spectrum)
        ax2.bar(orders[significant], spectrum[significant] * 1000, 
               color='steelblue', alpha=0.7)
        ax2.set_xlabel('Harmonic Order')
        ax2.set_ylabel('Amplitude (mN·m)')
        ax2.set_title('Cogging Torque Harmonic Spectrum')
        ax2.set_xlim([0, 100])
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_campbell_diagram(rpm_values: np.ndarray,
                         natural_freqs: Dict[str, np.ndarray],
                         forcing_freqs: Dict[str, np.ndarray],
                         intersections: list,
                         save_path: Optional[str] = None):
    """
    Plot Campbell diagram showing resonance conditions.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot natural frequencies (horizontal lines)
    colors_nat = plt.cm.Blues(np.linspace(0.4, 0.8, len(natural_freqs)))
    for (name, freq), color in zip(natural_freqs.items(), colors_nat):
        ax.axhline(y=freq, color=color, linestyle='-', linewidth=2, label=f'Natural: {name}')
    
    # Plot forcing frequencies (diagonal lines)
    colors_force = plt.cm.Reds(np.linspace(0.4, 0.9, len(forcing_freqs)))
    for (name, freq), color in zip(forcing_freqs.items(), colors_force):
        ax.plot(rpm_values, freq, color=color, linestyle='--', linewidth=1.5, 
               label=f'Forcing: {name}')
    
    # Mark intersections
    for inter in intersections:
        ax.plot(inter["rpm"], inter["frequency_Hz"], 'ko', markersize=10, 
               markerfacecolor='yellow', markeredgewidth=2)
        ax.annotate(f'{inter["rpm"]:.0f} RPM', 
                   xy=(inter["rpm"], inter["frequency_Hz"]),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=8, color='red')
    
    ax.set_xlabel('Rotor Speed (RPM)')
    ax.set_ylabel('Frequency (Hz)')
    ax.set_title('Campbell Diagram - Resonance Analysis')
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([rpm_values[0], rpm_values[-1]])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_loss_breakdown(losses: Dict[str, float],
                       save_path: Optional[str] = None):
    """
    Plot pie chart and bar chart of loss breakdown.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Pie chart
    ax1 = axes[0]
    labels = list(losses.keys())
    values = list(losses.values())
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    explode = [0.05] * len(labels)
    
    ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, 
           explode=explode, shadow=True)
    ax1.set_title('Loss Distribution')
    
    # Bar chart
    ax2 = axes[1]
    bars = ax2.bar(labels, values, color=colors)
    ax2.set_ylabel('Power Loss (W)')
    ax2.set_title('Loss Components')
    ax2.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax2.annotate(f'{val:.2f} W',
                    xy=(bar.get_x() + bar.get_width()/2, val),
                    xytext=(0, 3), textcoords='offset points',
                    ha='center', fontsize=9)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_magnetic_field_2d(X: np.ndarray, Y: np.ndarray,
                          Bx: np.ndarray, By: np.ndarray,
                          save_path: Optional[str] = None):
    """
    Plot 2D magnetic field distribution.
    """
    B_mag = np.sqrt(Bx**2 + By**2)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Magnitude contour
    ax1 = axes[0]
    contour = ax1.contourf(X*1000, Y*1000, B_mag, levels=20, cmap='magma')
    plt.colorbar(contour, ax=ax1, label='|B| (T)')
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')
    ax1.set_title('Magnetic Field Magnitude')
    ax1.set_aspect('equal')
    
    # Vector field
    ax2 = axes[1]
    # Subsample for clarity
    skip = 5
    ax2.quiver(X[::skip, ::skip]*1000, Y[::skip, ::skip]*1000,
              Bx[::skip, ::skip], By[::skip, ::skip],
              B_mag[::skip, ::skip], cmap='viridis')
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Y (mm)')
    ax2.set_title('Magnetic Field Vectors')
    ax2.set_aspect('equal')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_optimization_history(history: list,
                             save_path: Optional[str] = None):
    """
    Plot optimization algorithm convergence.
    """
    generations = [h["generation"] for h in history]
    best_fitness = [h["best_fitness"] for h in history]
    mean_fitness = [h["mean_fitness"] for h in history]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(generations, best_fitness, 'b-', linewidth=2, label='Best Fitness')
    ax.plot(generations, mean_fitness, 'g--', linewidth=1, label='Mean Fitness')
    ax.fill_between(generations, mean_fitness, best_fitness, alpha=0.2)
    
    ax.set_xlabel('Generation')
    ax.set_ylabel('Fitness Score')
    ax.set_title('Optimization Convergence')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def create_all_plots(results, inputs, output_dir: str = None):
    """
    Create all plots from simulation results.
    """
    setup_plot_style()
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = None
    
    plots = {}
    
    # Rotor dynamics
    torques = {
        "Drive": results.torque_drive,
        "Cogging": results.torque_cogging,
        "Friction": results.torque_friction,
        "Load": results.torque_load
    }
    plots["dynamics"] = plot_rotor_dynamics(
        results.time, results.rpm, torques,
        save_path=str(output_path / "rotor_dynamics.png") if output_path else None
    )
    
    # Electrical waveforms
    plots["electrical"] = plot_electrical_waveforms(
        results.time,
        results.emf_phase_a, results.emf_phase_b, results.emf_phase_c,
        results.current_phase_a, results.current_phase_b, results.current_phase_c,
        save_path=str(output_path / "electrical_waveforms.png") if output_path else None
    )
    
    # Power and efficiency
    plots["power"] = plot_power_efficiency(
        results.time,
        results.power_mechanical, results.power_electrical, results.power_losses,
        results.efficiency,
        save_path=str(output_path / "power_efficiency.png") if output_path else None
    )
    
    return plots
