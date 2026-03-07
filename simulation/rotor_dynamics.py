"""
Rotor Dynamics Simulation
==========================
Complete rotational mechanics including:
- Angular motion with torque profiles
- Startup transients
- Steady-state operation
- Dynamic load response
"""

import numpy as np
from typing import Tuple, Callable, Dict, List
from dataclasses import dataclass
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks


@dataclass
class RotorParameters:
    """Physical parameters of the rotor"""
    mass: float = 2.0              # kg
    radius: float = 0.05           # m (outer radius)
    inner_radius: float = 0.02     # m (shaft)
    length: float = 0.10           # m
    material_density: float = 7500 # kg/m³ (NdFeB + steel)
    
    @property
    def moment_of_inertia(self) -> float:
        """Calculate moment of inertia for hollow cylinder"""
        # I = 0.5 * m * (r_outer² + r_inner²)
        return 0.5 * self.mass * (self.radius**2 + self.inner_radius**2)
    
    @property
    def volume(self) -> float:
        """Calculate rotor volume"""
        return np.pi * (self.radius**2 - self.inner_radius**2) * self.length


def simulate_rotor_dynamics(rotor: RotorParameters,
                           torque_func: Callable[[float, float], float],
                           friction_func: Callable[[float], float],
                           t_span: Tuple[float, float] = (0, 5),
                           initial_omega: float = 0.0,
                           dt: float = 0.001) -> Dict:
    """
    Simulate rotor angular dynamics over time.
    
    Equation of motion:
    I * dω/dt = τ_applied - τ_friction - τ_load
    
    Parameters:
    -----------
    rotor : RotorParameters
        Physical rotor parameters
    torque_func : Callable
        Function τ(t, θ) returning applied torque
    friction_func : Callable
        Function τ_f(ω) returning friction torque
    t_span : Tuple
        Time interval (start, end) in seconds
    initial_omega : float
        Initial angular velocity (rad/s)
    dt : float
        Time step for output
        
    Returns:
    --------
    Dict with time, angle, angular velocity, and torque arrays
    """
    I = rotor.moment_of_inertia
    
    def dynamics(t, y):
        """State: y = [θ, ω]"""
        theta, omega = y
        
        # Applied torque (from magnets/motor)
        tau_applied = torque_func(t, theta)
        
        # Friction torque (opposes motion)
        tau_friction = friction_func(omega)
        
        # Angular acceleration
        alpha = (tau_applied - tau_friction) / I
        
        return [omega, alpha]
    
    # Initial conditions
    y0 = [0.0, initial_omega]
    
    # Solve ODE
    t_eval = np.arange(t_span[0], t_span[1], dt)
    solution = solve_ivp(dynamics, t_span, y0, t_eval=t_eval, method='RK45')
    
    # Calculate torques at each time step
    torques = [torque_func(t, th) for t, th in zip(solution.t, solution.y[0])]
    friction_torques = [friction_func(w) for w in solution.y[1]]
    
    return {
        "time": solution.t,
        "angle": solution.y[0],
        "omega": solution.y[1],
        "rpm": solution.y[1] * 60 / (2 * np.pi),
        "torque_applied": np.array(torques),
        "torque_friction": np.array(friction_torques),
        "angular_acceleration": np.gradient(solution.y[1], solution.t)
    }


def create_startup_torque_profile(max_torque: float, 
                                  ramp_time: float = 1.0) -> Callable:
    """
    Create a smooth startup torque profile.
    
    Uses S-curve acceleration for smooth startup.
    """
    def torque_func(t: float, theta: float) -> float:
        if t < ramp_time:
            # Smooth S-curve ramp
            s = t / ramp_time
            factor = 3 * s**2 - 2 * s**3  # Smoothstep
            return max_torque * factor
        return max_torque
    
    return torque_func


def create_friction_model(bearing_friction: float = 0.01,
                         viscous_friction: float = 0.001,
                         windage_coefficient: float = 1e-6) -> Callable:
    """
    Create a comprehensive friction model.
    
    τ_friction = τ_bearing × sign(ω) + b × ω + c × ω²
    
    - Coulomb friction (constant, direction-dependent)
    - Viscous friction (linear with speed)
    - Windage (quadratic with speed)
    """
    def friction_func(omega: float) -> float:
        # Coulomb friction
        tau_coulomb = bearing_friction * np.sign(omega)
        
        # Viscous friction
        tau_viscous = viscous_friction * omega
        
        # Windage (air drag)
        tau_windage = windage_coefficient * omega**2 * np.sign(omega)
        
        return tau_coulomb + tau_viscous + tau_windage
    
    return friction_func


def analyze_steady_state(dynamics_result: Dict,
                        steady_state_threshold: float = 0.01) -> Dict:
    """
    Analyze steady-state behavior from simulation results.
    
    Detects:
    - Time to reach steady state
    - Average steady-state speed
    - Speed ripple
    - Oscillation frequency
    """
    omega = dynamics_result["omega"]
    time = dynamics_result["time"]
    
    # Find when steady state is reached
    # (when rate of change falls below threshold)
    d_omega = np.abs(np.gradient(omega, time))
    
    steady_indices = np.where(d_omega < steady_state_threshold)[0]
    if len(steady_indices) > 0:
        steady_start_idx = steady_indices[0]
        steady_start_time = time[steady_start_idx]
    else:
        steady_start_idx = len(time) // 2
        steady_start_time = time[steady_start_idx]
    
    # Analyze steady-state region
    omega_steady = omega[steady_start_idx:]
    omega_mean = np.mean(omega_steady)
    omega_std = np.std(omega_steady)
    ripple_percent = 100 * omega_std / omega_mean if omega_mean > 0 else 0
    
    # Find oscillation frequency from peaks
    peaks, _ = find_peaks(omega_steady)
    if len(peaks) > 1:
        dt = time[1] - time[0]
        peak_spacing = np.mean(np.diff(peaks)) * dt
        oscillation_freq = 1 / peak_spacing if peak_spacing > 0 else 0
    else:
        oscillation_freq = 0
    
    return {
        "time_to_steady_state": steady_start_time,
        "steady_state_omega": omega_mean,
        "steady_state_rpm": omega_mean * 60 / (2 * np.pi),
        "speed_ripple_percent": ripple_percent,
        "oscillation_frequency_Hz": oscillation_freq
    }


def analyze_energy_transfer(dynamics_result: Dict,
                           rotor: RotorParameters) -> Dict:
    """
    Analyze energy flow during rotation.
    
    Kinetic Energy: KE = 0.5 × I × ω²
    Work done: W = ∫ τ × dθ
    Power: P = τ × ω
    """
    I = rotor.moment_of_inertia
    omega = dynamics_result["omega"]
    theta = dynamics_result["angle"]
    time = dynamics_result["time"]
    tau = dynamics_result["torque_applied"]
    tau_f = dynamics_result["torque_friction"]
    
    # Kinetic energy over time
    KE = 0.5 * I * omega**2
    
    # Power
    power_in = tau * omega
    power_loss = tau_f * omega
    power_net = power_in - power_loss
    
    # Work done (cumulative)
    work_in = np.cumsum(power_in) * (time[1] - time[0])
    work_loss = np.cumsum(power_loss) * (time[1] - time[0])
    
    return {
        "kinetic_energy": KE,
        "power_in": power_in,
        "power_loss": power_loss,
        "power_net": power_net,
        "work_in": work_in,
        "work_loss": work_loss,
        "energy_efficiency": (KE[-1] + work_loss[-1]) / work_in[-1] if work_in[-1] > 0 else 0
    }


class MultiRotorSimulator:
    """
    Simulate multiple interacting rotors (for complex generator designs).
    """
    
    def __init__(self, rotors: List[RotorParameters], 
                 coupling_matrix: np.ndarray = None):
        """
        Parameters:
        -----------
        rotors : List[RotorParameters]
            List of rotor parameters
        coupling_matrix : np.ndarray
            Matrix defining magnetic coupling between rotors
            K[i,j] = coupling stiffness between rotor i and j
        """
        self.rotors = rotors
        self.n_rotors = len(rotors)
        
        if coupling_matrix is None:
            self.K = np.zeros((self.n_rotors, self.n_rotors))
        else:
            self.K = coupling_matrix
    
    def simulate(self, t_span: Tuple[float, float],
                 external_torques: List[Callable],
                 initial_conditions: np.ndarray = None) -> Dict:
        """
        Simulate coupled rotor dynamics.
        
        System equations:
        I_i × d²θ_i/dt² = τ_i - Σ_j K_ij × (θ_i - θ_j)
        """
        if initial_conditions is None:
            # [θ_1, ω_1, θ_2, ω_2, ...]
            initial_conditions = np.zeros(2 * self.n_rotors)
        
        def coupled_dynamics(t, y):
            """State: y = [θ_1, ω_1, θ_2, ω_2, ...]"""
            dydt = np.zeros_like(y)
            
            for i in range(self.n_rotors):
                theta_i = y[2*i]
                omega_i = y[2*i + 1]
                
                # External torque
                tau_ext = external_torques[i](t, theta_i)
                
                # Coupling torque
                tau_coupling = 0
                for j in range(self.n_rotors):
                    if i != j:
                        theta_j = y[2*j]
                        tau_coupling -= self.K[i, j] * (theta_i - theta_j)
                
                # Equations of motion
                I = self.rotors[i].moment_of_inertia
                
                dydt[2*i] = omega_i
                dydt[2*i + 1] = (tau_ext + tau_coupling) / I
            
            return dydt
        
        # Solve
        solution = solve_ivp(coupled_dynamics, t_span, initial_conditions,
                            method='RK45', dense_output=True)
        
        results = {
            "time": solution.t,
            "rotors": []
        }
        
        for i in range(self.n_rotors):
            results["rotors"].append({
                "angle": solution.y[2*i],
                "omega": solution.y[2*i + 1],
                "rpm": solution.y[2*i + 1] * 60 / (2 * np.pi)
            })
        
        return results
