"""
Genetic Algorithm Optimizer for Generator Design
=================================================
Multi-objective optimization for:
- Maximum efficiency
- Minimum cogging
- Minimum weight
- Maximum power density
"""

import numpy as np
from typing import Dict, List, Tuple, Callable, Optional
from dataclasses import dataclass
import random
from copy import deepcopy


@dataclass
class DesignParameters:
    """Design parameters that can be optimized"""
    n_poles: int = 12
    n_slots: int = 18
    rotor_radius: float = 0.05
    magnet_thickness: float = 0.005
    magnet_arc: float = 0.85
    air_gap: float = 0.001
    skew_angle: float = 0.0
    axial_length: float = 0.10
    n_turns: int = 100
    
    def to_array(self) -> np.ndarray:
        """Convert to array for optimization"""
        return np.array([
            self.n_poles,
            self.n_slots,
            self.rotor_radius * 1000,  # mm
            self.magnet_thickness * 1000,
            self.magnet_arc,
            self.air_gap * 1000,
            self.skew_angle,
            self.axial_length * 1000,
            self.n_turns
        ])
    
    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'DesignParameters':
        """Create from optimization array"""
        return cls(
            n_poles=int(round(arr[0] / 2) * 2),  # Must be even
            n_slots=int(round(arr[1] / 3) * 3),  # Must be multiple of 3
            rotor_radius=arr[2] / 1000,
            magnet_thickness=arr[3] / 1000,
            magnet_arc=np.clip(arr[4], 0.5, 0.95),
            air_gap=arr[5] / 1000,
            skew_angle=arr[6],
            axial_length=arr[7] / 1000,
            n_turns=int(arr[8])
        )


@dataclass
class OptimizationBounds:
    """Bounds for design parameters"""
    n_poles_range: Tuple[int, int] = (4, 24)
    n_slots_range: Tuple[int, int] = (6, 36)
    rotor_radius_range: Tuple[float, float] = (0.02, 0.10)  # m
    magnet_thickness_range: Tuple[float, float] = (0.002, 0.010)
    magnet_arc_range: Tuple[float, float] = (0.5, 0.95)
    air_gap_range: Tuple[float, float] = (0.0005, 0.003)
    skew_angle_range: Tuple[float, float] = (0, 30)
    axial_length_range: Tuple[float, float] = (0.05, 0.20)
    n_turns_range: Tuple[int, int] = (20, 200)


@dataclass
class OptimizationObjectives:
    """Optimization objectives with weights"""
    maximize_efficiency: float = 1.0
    minimize_cogging: float = 1.0
    minimize_weight: float = 0.5
    maximize_power_density: float = 0.5
    minimize_cost: float = 0.3


class GeneticOptimizer:
    """
    Genetic algorithm optimizer for generator design.
    
    Uses NSGA-II style multi-objective optimization.
    """
    
    def __init__(self, 
                 bounds: OptimizationBounds = None,
                 objectives: OptimizationObjectives = None,
                 population_size: int = 50,
                 n_generations: int = 100,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8):
        
        self.bounds = bounds or OptimizationBounds()
        self.objectives = objectives or OptimizationObjectives()
        self.pop_size = population_size
        self.n_gen = n_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        # Results storage
        self.best_solution = None
        self.pareto_front = []
        self.history = []
    
    def initialize_population(self) -> List[DesignParameters]:
        """Create initial random population"""
        population = []
        
        for _ in range(self.pop_size):
            params = DesignParameters(
                n_poles=random.choice(range(self.bounds.n_poles_range[0], 
                                           self.bounds.n_poles_range[1] + 1, 2)),
                n_slots=random.choice(range(self.bounds.n_slots_range[0], 
                                           self.bounds.n_slots_range[1] + 1, 3)),
                rotor_radius=random.uniform(*self.bounds.rotor_radius_range),
                magnet_thickness=random.uniform(*self.bounds.magnet_thickness_range),
                magnet_arc=random.uniform(*self.bounds.magnet_arc_range),
                air_gap=random.uniform(*self.bounds.air_gap_range),
                skew_angle=random.uniform(*self.bounds.skew_angle_range),
                axial_length=random.uniform(*self.bounds.axial_length_range),
                n_turns=random.randint(*self.bounds.n_turns_range)
            )
            population.append(params)
        
        return population
    
    def evaluate_fitness(self, params: DesignParameters) -> Dict[str, float]:
        """
        Evaluate all objective functions for a design.
        
        Returns dictionary of objective values.
        """
        from math import lcm
        
        # Calculate derived quantities
        pole_pairs = params.n_poles // 2
        
        # 1. Efficiency estimate (simplified)
        # Higher efficiency with:
        # - Larger magnets (more flux)
        # - Smaller air gap (less reluctance)
        # - More turns (more EMF)
        flux_factor = params.magnet_thickness * params.magnet_arc * params.rotor_radius**2
        gap_factor = 1 / (1 + params.air_gap / params.magnet_thickness)
        efficiency = 0.85 + 0.10 * flux_factor * gap_factor * 1000
        efficiency = np.clip(efficiency, 0.7, 0.98)
        
        # 2. Cogging torque (lower is better)
        # Minimized by:
        # - Higher LCM of poles and slots
        # - Larger skew angle
        # - Optimal magnet arc
        cog_order = lcm(params.n_poles, params.n_slots)
        skew_factor = 1 - params.skew_angle / 30
        arc_factor = abs(params.magnet_arc - 0.833)  # Optimal around 5/6
        cogging = (params.n_poles / cog_order) * skew_factor * (1 + arc_factor)
        
        # 3. Weight estimate
        # Based on volume of active materials
        rotor_volume = np.pi * params.rotor_radius**2 * params.axial_length
        magnet_volume = params.magnet_arc * np.pi * params.rotor_radius**2 * \
                       params.axial_length * params.magnet_thickness / params.rotor_radius
        weight = 7850 * rotor_volume + 7500 * magnet_volume  # Steel + NdFeB
        
        # 4. Power density
        # Power / weight ratio
        emf_factor = params.n_turns * flux_factor * params.axial_length
        power_est = emf_factor * 1000  # Arbitrary scaling
        power_density = power_est / weight if weight > 0 else 0
        
        # 5. Cost estimate
        # Based on magnet volume (magnets are expensive!)
        magnet_cost = magnet_volume * 1e6  # $/m³ scaling
        cost = magnet_cost + 0.1 * weight  # Add steel cost
        
        return {
            "efficiency": efficiency,
            "cogging": cogging,
            "weight": weight,
            "power_density": power_density,
            "cost": cost
        }
    
    def calculate_weighted_fitness(self, objectives: Dict[str, float]) -> float:
        """Convert multi-objective to single weighted score"""
        score = 0
        
        # Maximize efficiency (higher is better)
        score += self.objectives.maximize_efficiency * objectives["efficiency"]
        
        # Minimize cogging (lower is better, invert)
        score += self.objectives.minimize_cogging * (1 - objectives["cogging"])
        
        # Minimize weight (lower is better, invert and normalize)
        score += self.objectives.minimize_weight * (10 / (1 + objectives["weight"]))
        
        # Maximize power density
        score += self.objectives.maximize_power_density * objectives["power_density"] / 100
        
        # Minimize cost
        score += self.objectives.minimize_cost * (1 / (1 + objectives["cost"]))
        
        return score
    
    def crossover(self, parent1: DesignParameters, 
                  parent2: DesignParameters) -> DesignParameters:
        """Uniform crossover between two parents"""
        arr1 = parent1.to_array()
        arr2 = parent2.to_array()
        
        # Random mask for each gene
        mask = np.random.random(len(arr1)) < 0.5
        child_arr = np.where(mask, arr1, arr2)
        
        return DesignParameters.from_array(child_arr)
    
    def mutate(self, params: DesignParameters) -> DesignParameters:
        """Mutate parameters with small random changes"""
        arr = params.to_array()
        
        # Mutation noise
        noise_scale = [2, 3, 5, 1, 0.05, 0.2, 3, 10, 10]  # Per-parameter scale
        
        for i in range(len(arr)):
            if random.random() < self.mutation_rate:
                arr[i] += random.gauss(0, noise_scale[i])
        
        return DesignParameters.from_array(arr)
    
    def select_parents(self, population: List[DesignParameters],
                      fitnesses: List[float]) -> Tuple[DesignParameters, DesignParameters]:
        """Tournament selection"""
        def tournament():
            candidates = random.sample(list(zip(population, fitnesses)), 3)
            return max(candidates, key=lambda x: x[1])[0]
        
        return tournament(), tournament()
    
    def run(self) -> DesignParameters:
        """
        Run the genetic algorithm optimization.
        
        Returns the best design found.
        """
        print("=" * 60)
        print("GENETIC ALGORITHM OPTIMIZATION")
        print("=" * 60)
        print(f"Population: {self.pop_size}")
        print(f"Generations: {self.n_gen}")
        print(f"Mutation rate: {self.mutation_rate}")
        print()
        
        # Initialize
        population = self.initialize_population()
        
        best_fitness_ever = -np.inf
        generations_without_improvement = 0
        
        for gen in range(self.n_gen):
            # Evaluate fitness
            objectives_list = [self.evaluate_fitness(p) for p in population]
            fitnesses = [self.calculate_weighted_fitness(o) for o in objectives_list]
            
            # Track best
            best_idx = np.argmax(fitnesses)
            best_fitness = fitnesses[best_idx]
            best_params = population[best_idx]
            best_objectives = objectives_list[best_idx]
            
            if best_fitness > best_fitness_ever:
                best_fitness_ever = best_fitness
                self.best_solution = deepcopy(best_params)
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            # Log progress
            if gen % 10 == 0 or gen == self.n_gen - 1:
                print(f"Gen {gen:3d}: Best fitness = {best_fitness:.4f}")
                print(f"         Efficiency: {best_objectives['efficiency']:.3f}")
                print(f"         Cogging: {best_objectives['cogging']:.4f}")
            
            self.history.append({
                "generation": gen,
                "best_fitness": best_fitness,
                "mean_fitness": np.mean(fitnesses),
                "best_objectives": best_objectives
            })
            
            # Early stopping
            if generations_without_improvement > 20:
                print(f"\nEarly stopping at generation {gen}")
                break
            
            # Create next generation
            new_population = []
            
            # Elitism: keep best 10%
            elite_count = max(2, self.pop_size // 10)
            elite_indices = np.argsort(fitnesses)[-elite_count:]
            for idx in elite_indices:
                new_population.append(deepcopy(population[idx]))
            
            # Fill rest with crossover and mutation
            while len(new_population) < self.pop_size:
                if random.random() < self.crossover_rate:
                    parent1, parent2 = self.select_parents(population, fitnesses)
                    child = self.crossover(parent1, parent2)
                else:
                    child = deepcopy(random.choice(population))
                
                child = self.mutate(child)
                new_population.append(child)
            
            population = new_population
        
        print("\n" + "=" * 60)
        print("OPTIMIZATION COMPLETE")
        print("=" * 60)
        print(f"\nBest Design Found:")
        print(f"  Poles: {self.best_solution.n_poles}")
        print(f"  Slots: {self.best_solution.n_slots}")
        print(f"  Rotor radius: {self.best_solution.rotor_radius*1000:.1f} mm")
        print(f"  Magnet thickness: {self.best_solution.magnet_thickness*1000:.1f} mm")
        print(f"  Magnet arc: {self.best_solution.magnet_arc:.2f}")
        print(f"  Air gap: {self.best_solution.air_gap*1000:.2f} mm")
        print(f"  Skew angle: {self.best_solution.skew_angle:.1f}°")
        print(f"  Axial length: {self.best_solution.axial_length*1000:.0f} mm")
        print(f"  Turns per coil: {self.best_solution.n_turns}")
        
        return self.best_solution


def quick_optimize(target_power_watts: float = 1000,
                   target_rpm: float = 3000,
                   max_diameter_mm: float = 200) -> DesignParameters:
    """
    Quick optimization for a given power target.
    
    Uses simplified heuristics for fast results.
    """
    print(f"Quick optimization for {target_power_watts} W at {target_rpm} RPM")
    
    # Heuristic design rules
    omega = target_rpm * 2 * np.pi / 60
    
    # Power = τ × ω, so τ = P / ω
    torque_required = target_power_watts / omega
    
    # Torque ∝ B × r² × L
    # Assume B ≈ 0.8 T effective
    B_eff = 0.8
    
    # Size from torque requirement
    # τ ≈ 2 × B × r² × L for tangential stress ~ 20 kPa
    stress = 20000  # Pa
    r_L_product = torque_required / (2 * stress * 2 * np.pi)
    
    # Assume L/r ratio of 2
    rotor_radius = (r_L_product / 2) ** (1/3)
    rotor_radius = min(rotor_radius, max_diameter_mm / 2000)
    axial_length = 2 * rotor_radius
    
    # Pole count from frequency considerations
    # For 50-60 Hz output: f = p × rpm / 60
    # p = f × 60 / rpm
    target_freq = 50  # Hz
    pole_pairs = int(round(target_freq * 60 / target_rpm))
    pole_pairs = max(2, min(pole_pairs, 12))
    n_poles = 2 * pole_pairs
    
    # Slots = 1.5 × poles for 3-phase
    n_slots = int(1.5 * n_poles)
    
    # Optimal skew for this pole-slot combo
    from math import lcm
    cog_order = lcm(n_poles, n_slots)
    skew_angle = 360 / cog_order
    
    return DesignParameters(
        n_poles=n_poles,
        n_slots=n_slots,
        rotor_radius=rotor_radius,
        magnet_thickness=0.005,
        magnet_arc=0.833,  # 5/6 ratio
        air_gap=0.001,
        skew_angle=skew_angle,
        axial_length=axial_length,
        n_turns=int(100 * (0.05 / rotor_radius))  # Scale with size
    )


if __name__ == "__main__":
    # Run optimization
    optimizer = GeneticOptimizer(
        population_size=30,
        n_generations=50
    )
    
    best = optimizer.run()
    
    # Also run quick optimization for comparison
    print("\n" + "=" * 60)
    print("QUICK OPTIMIZATION RESULT")
    print("=" * 60)
    quick = quick_optimize(1000, 3000)
    print(f"Quick design: {quick.n_poles}P/{quick.n_slots}S")
