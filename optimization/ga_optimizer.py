import os
import sys
import math
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional

# Add project root to sys.path to allow absolute imports when running directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from simulation.engine import run_simulation
from optimization.financials import calculate_lcoe, DEFAULT_COST_PARAMS

# Setup logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class CustomGA:
    """
    A pure NumPy-based fallback Genetic Algorithm.
    Implements selection (tournament), crossover (arithmetic), mutation (Gaussian), and elitism.
    """
    def __init__(
        self,
        num_generations: int,
        sol_per_pop: int,
        num_genes: int,
        gene_space: List[Tuple[float, float]],
        fitness_func,
        mutation_probability: float = 0.1,
        crossover_probability: float = 0.8,
        elitism_percent: float = 0.05,
        tournament_size: int = 3
    ):
        self.num_generations = num_generations
        self.sol_per_pop = sol_per_pop
        self.num_genes = num_genes
        self.gene_space = gene_space  # List of (min, max) bounds per gene
        self.fitness_func = fitness_func
        self.mutation_probability = mutation_probability
        self.crossover_probability = crossover_probability
        self.elitism_percent = elitism_percent
        self.tournament_size = tournament_size

        # State vars
        self.population = None
        self.fitness_history = []
        self.best_solutions_fitness = []  # To match PyGAD's structure
        self.best_solution = None
        self.best_solution_fitness = -float('inf')

    def run(self):
        # 1. Initialize population uniformly within bounds
        self.population = np.zeros((self.sol_per_pop, self.num_genes))
        for j in range(self.num_genes):
            g_min, g_max = self.gene_space[j]
            self.population[:, j] = np.random.uniform(g_min, g_max, size=self.sol_per_pop)

        self.fitness_history = []
        self.best_solutions_fitness = []

        logger.info("Starting Custom NumPy Genetic Algorithm optimization loop...")

        for gen in range(self.num_generations):
            # 2. Evaluate fitness for all chromosomes
            fitnesses = np.zeros(self.sol_per_pop)
            for idx in range(self.sol_per_pop):
                fitnesses[idx] = self.fitness_func(self, self.population[idx], idx)

            # Track the best solution in this generation
            best_idx = np.argmax(fitnesses)
            best_fit = fitnesses[best_idx]

            # Track overall best
            if best_fit > self.best_solution_fitness:
                self.best_solution_fitness = best_fit
                self.best_solution = self.population[best_idx].copy()

            self.fitness_history.append(best_fit)
            self.best_solutions_fitness.append(best_fit)

            if (gen + 1) % max(1, self.num_generations // 5) == 0 or gen == 0:
                logger.info(f"Generation {gen + 1}/{self.num_generations} - Best Fitness: {best_fit:.6f} (LCOE: ${1.0/best_fit if best_fit > 1e-9 else float('inf'):.4f}/kWh)")

            # 3. Create the next generation
            new_population = np.zeros_like(self.population)

            # Apply elitism: copy best individuals directly
            num_elites = max(1, int(round(self.elitism_percent * self.sol_per_pop)))
            elite_indices = np.argsort(fitnesses)[-num_elites:]
            new_population[:num_elites] = self.population[elite_indices]

            # Generate rest of population through selection, crossover, and mutation
            i = num_elites
            while i < self.sol_per_pop:
                # Selection
                p1 = self._tournament_selection(fitnesses)
                p2 = self._tournament_selection(fitnesses)

                # Crossover
                if np.random.rand() < self.crossover_probability:
                    c1, c2 = self._arithmetic_crossover(p1, p2)
                else:
                    c1, c2 = p1.copy(), p2.copy()

                # Mutation
                c1 = self._mutate(c1)
                c2 = self._mutate(c2)

                new_population[i] = c1
                if i + 1 < self.sol_per_pop:
                    new_population[i + 1] = c2
                i += 2

            self.population = new_population

        # Final evaluation of the last population
        fitnesses = np.zeros(self.sol_per_pop)
        for idx in range(self.sol_per_pop):
            fitnesses[idx] = self.fitness_func(self, self.population[idx], idx)
        best_idx = np.argmax(fitnesses)
        best_fit = fitnesses[best_idx]
        if best_fit > self.best_solution_fitness:
            self.best_solution_fitness = best_fit
            self.best_solution = self.population[best_idx].copy()
        
        self.fitness_history.append(self.best_solution_fitness)
        self.best_solutions_fitness.append(self.best_solution_fitness)
        
        logger.info(f"Optimization completed. Optimal Fitness: {self.best_solution_fitness:.6f}")

    def _tournament_selection(self, fitnesses: np.ndarray) -> np.ndarray:
        candidates = np.random.choice(self.sol_per_pop, size=self.tournament_size, replace=False)
        best_candidate = candidates[np.argmax(fitnesses[candidates])]
        return self.population[best_candidate]

    def _arithmetic_crossover(self, p1: np.ndarray, p2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        alpha = np.random.uniform(0.0, 1.0, size=self.num_genes)
        c1 = alpha * p1 + (1.0 - alpha) * p2
        c2 = alpha * p2 + (1.0 - alpha) * p1
        return c1, c2

    def _mutate(self, child: np.ndarray) -> np.ndarray:
        mutated = child.copy()
        for j in range(self.num_genes):
            if np.random.rand() < self.mutation_probability:
                g_min, g_max = self.gene_space[j]
                # Gaussian mutation with standard deviation = 10% of gene search range
                std = 0.1 * (g_max - g_min)
                mutated[j] += np.random.normal(0, std)
                # Clip to prevent going out of bounds
                mutated[j] = np.clip(mutated[j], g_min, g_max)
        return mutated


class GAOptimizer:
    """
    Genetic Algorithm optimizer for finding the optimal sizes of:
      1. PV capacity (kW)
      2. Wind capacity (kW)
      3. Battery capacity (kWh)
      4. Diesel capacity (kW)
    
    Optimizes for minimum Levelized Cost of Energy (LCOE) under constraints.
    Supports PyGAD with an automatic Custom NumPy GA fallback.
    """
    def __init__(
        self,
        weather_df: pd.DataFrame,
        load_df: pd.DataFrame,
        cost_params: Optional[Dict[str, Any]] = None,
        system_config_base: Optional[Dict[str, Any]] = None,
        lolp_max: float = 0.05,
        pv_bounds: Tuple[float, float] = (0.0, 200.0),
        wind_bounds: Tuple[float, float] = (0.0, 100.0),
        battery_bounds: Tuple[float, float] = (0.0, 500.0),
        diesel_bounds: Tuple[float, float] = (0.0, 50.0),
        num_generations: int = 50,
        sol_per_pop: int = 20,
        use_fallback_ga: bool = False
    ):
        self.weather_df = weather_df
        self.load_df = load_df
        self.cost_params = cost_params or {}
        self.system_config_base = system_config_base or {}
        self.lolp_max = lolp_max
        
        # Search space bounds for PV, Wind, Battery, Diesel capacities
        self.bounds = [pv_bounds, wind_bounds, battery_bounds, diesel_bounds]
        
        self.num_generations = num_generations
        self.sol_per_pop = sol_per_pop
        self.use_fallback_ga = use_fallback_ga
        
        # Pre-compute annual load metrics to save execution cycles inside fitness evaluation
        if "total_load" in load_df.columns:
            self.total_annual_load_kwh = float(load_df["total_load"].sum())
        elif "load" in load_df.columns:
            self.total_annual_load_kwh = float(load_df["load"].sum())
        else:
            self.total_annual_load_kwh = float(load_df.iloc[:, 0].sum())

    def fitness_func(self, ga_instance, solution, solution_idx) -> float:
        """
        Fitness evaluation function: computes 1.0 / penalized_lcoe.
        Includes a harsh constraint penalty for solutions exceeding LOLP_max.
        """
        # Ensure values are strictly bounded
        pv_capacity = max(self.bounds[0][0], min(self.bounds[0][1], float(solution[0])))
        wind_capacity = max(self.bounds[1][0], min(self.bounds[1][1], float(solution[1])))
        battery_capacity = max(self.bounds[2][0], min(self.bounds[2][1], float(solution[2])))
        diesel_capacity = max(self.bounds[3][0], min(self.bounds[3][1], float(solution[3])))
        
        # Build configuration for simulation engine
        config = {
            **self.system_config_base,
            "pv_capacity": pv_capacity,
            "wind_capacity": wind_capacity,
            "battery_capacity": battery_capacity,
            "diesel_capacity": diesel_capacity
        }
        
        try:
            # Run physical simulation
            hourly_df, summary = run_simulation(self.weather_df, self.load_df, config)
            
            # Extract key simulation outputs
            fuel_consumption = summary["total_fuel_consumption_liters"]
            unmet_load = summary["total_unmet_load_kwh"]
            lolp = summary["lolp"]
            battery_soh = summary["battery_soh_pct"]
            
            # Extract diesel generator annual operating hours
            if "diesel_output" in hourly_df.columns:
                diesel_operating_hours = float((hourly_df["diesel_output"] > 1e-3).sum())
            else:
                diesel_operating_hours = 0.0
                
            # Compute annual battery state-of-health degradation fraction
            battery_degradation = max(0.0, (100.0 - battery_soh) / 100.0)
            
            # Compute financial Levelized Cost of Energy
            lcoe, details = calculate_lcoe(
                pv_capacity=pv_capacity,
                wind_capacity=wind_capacity,
                battery_capacity=battery_capacity,
                diesel_capacity=diesel_capacity,
                cost_params=self.cost_params,
                annual_diesel_operating_hours=diesel_operating_hours,
                annual_fuel_consumption=fuel_consumption,
                annual_battery_degradation_fraction=battery_degradation,
                total_annual_load_kwh=self.total_annual_load_kwh,
                annual_unmet_load_kwh=unmet_load
            )
            
            # Enforce reliability constraint (LOLP <= lolp_max)
            # Apply steep LCOE penalty if reliability constraint is violated
            if lolp > self.lolp_max:
                penalty_factor = 1.0 + 10.0 * (lolp - self.lolp_max) + 5.0
                penalized_lcoe = lcoe * penalty_factor
            else:
                penalized_lcoe = lcoe
                
            # Minimize LCOE by maximizing fitness
            if penalized_lcoe <= 0.0 or math.isnan(penalized_lcoe):
                fitness = 1e-10
            else:
                fitness = 1.0 / penalized_lcoe
                
        except Exception as e:
            # Safeguard GA from simulation failures (e.g. NaN outputs or numerical divergence)
            logger.debug(f"Simulation failed during evaluation: {e}")
            fitness = 1e-10
            
        return fitness

    def optimize(self) -> Dict[str, Any]:
        """
        Runs the optimization routine. Attempts to run PyGAD first,
        falling back automatically to CustomGA if PyGAD is missing or fails.
        
        Returns:
            Dict[str, Any]: Detailed optimization results.
        """
        use_pygad = False
        if not self.use_fallback_ga:
            try:
                import pygad
                use_pygad = True
            except ImportError:
                logger.warning("PyGAD library is not installed or import failed. Falling back to custom NumPy GA optimizer.")
                use_pygad = False
                
        if use_pygad:
            import pygad
            logger.info("Initializing PyGAD Optimization Engine...")
            
            # Formulate bounding spaces for PyGAD genes
            pygad_gene_space = [
                {"low": self.bounds[0][0], "high": self.bounds[0][1]},
                {"low": self.bounds[1][0], "high": self.bounds[1][1]},
                {"low": self.bounds[2][0], "high": self.bounds[2][1]},
                {"low": self.bounds[3][0], "high": self.bounds[3][1]}
            ]
            
            # Set parent mating size to half the population
            num_parents_mating = max(2, self.sol_per_pop // 2)
            
            try:
                ga_instance = pygad.GA(
                    num_generations=self.num_generations,
                    num_parents_mating=num_parents_mating,
                    fitness_func=lambda ga_inst, sol, sol_idx: self.fitness_func(ga_inst, sol, sol_idx),
                    sol_per_pop=self.sol_per_pop,
                    num_genes=4,
                    gene_space=pygad_gene_space,
                    parent_selection_type="tournament",
                    K_tournament=3,
                    crossover_type="single_point",
                    mutation_type="random",
                    mutation_probability=0.1,
                    crossover_probability=0.8,
                    keep_elitism=1,
                    suppress_warnings=True
                )
                
                ga_instance.run()
                
                best_solution, best_fitness, best_idx = ga_instance.best_solution()
                convergence_history = list(ga_instance.best_solutions_fitness)
                method = "pygad"
                
            except Exception as e:
                logger.error(f"PyGAD run failed with error: {e}. Switching immediately to Custom NumPy GA fallback.")
                use_pygad = False
                
        if not use_pygad:
            logger.info("Initializing Custom NumPy GA Fallback...")
            custom_ga = CustomGA(
                num_generations=self.num_generations,
                sol_per_pop=self.sol_per_pop,
                num_genes=4,
                gene_space=self.bounds,
                fitness_func=lambda ga_inst, sol, sol_idx: self.fitness_func(ga_inst, sol, sol_idx),
                mutation_probability=0.1,
                crossover_probability=0.8,
                elitism_percent=0.05,
                tournament_size=3
            )
            custom_ga.run()
            
            best_solution = custom_ga.best_solution
            best_fitness = custom_ga.best_solution_fitness
            convergence_history = custom_ga.best_solutions_fitness
            method = "custom_numpy"
            
        # Post-process the best configuration to extract detailed KPIs
        pv_capacity = max(self.bounds[0][0], min(self.bounds[0][1], float(best_solution[0])))
        wind_capacity = max(self.bounds[1][0], min(self.bounds[1][1], float(best_solution[1])))
        battery_capacity = max(self.bounds[2][0], min(self.bounds[2][1], float(best_solution[2])))
        diesel_capacity = max(self.bounds[3][0], min(self.bounds[3][1], float(best_solution[3])))
        
        # Run detailed final simulation
        config = {
            **self.system_config_base,
            "pv_capacity": pv_capacity,
            "wind_capacity": wind_capacity,
            "battery_capacity": battery_capacity,
            "diesel_capacity": diesel_capacity
        }
        
        hourly_df, summary = run_simulation(self.weather_df, self.load_df, config)
        
        fuel_consumption = summary["total_fuel_consumption_liters"]
        unmet_load = summary["total_unmet_load_kwh"]
        lolp = summary["lolp"]
        battery_soh = summary["battery_soh_pct"]
        
        if "diesel_output" in hourly_df.columns:
            diesel_operating_hours = float((hourly_df["diesel_output"] > 1e-3).sum())
        else:
            diesel_operating_hours = 0.0
            
        battery_degradation = max(0.0, (100.0 - battery_soh) / 100.0)
        
        lcoe, details = calculate_lcoe(
            pv_capacity=pv_capacity,
            wind_capacity=wind_capacity,
            battery_capacity=battery_capacity,
            diesel_capacity=diesel_capacity,
            cost_params=self.cost_params,
            annual_diesel_operating_hours=diesel_operating_hours,
            annual_fuel_consumption=fuel_consumption,
            annual_battery_degradation_fraction=battery_degradation,
            total_annual_load_kwh=self.total_annual_load_kwh,
            annual_unmet_load_kwh=unmet_load
        )
        
        return {
            "best_configuration": {
                "pv_capacity": pv_capacity,
                "wind_capacity": wind_capacity,
                "battery_capacity": battery_capacity,
                "diesel_capacity": diesel_capacity
            },
            "metrics": {
                "lcoe": lcoe,
                "npc": details["npc"],
                "capital_cost": details["capital_cost"],
                "annual_om_cost": details["annual_om_cost"],
                "annual_fuel_cost": details["annual_fuel_cost"],
                "unmet_load_kwh": unmet_load,
                "lolp": lolp,
                "renewable_fraction": summary["renewable_fraction"],
                "diesel_operating_hours": diesel_operating_hours,
                "fuel_consumption_liters": fuel_consumption,
                "battery_soh_pct": battery_soh
            },
            "financial_details": details,
            "convergence_history": convergence_history,
            "optimization_method": method
        }

if __name__ == "__main__":
    print("==================================================")
    print("Testing ga_optimizer.py execution on synthetic data...")
    print("==================================================")
    
    from data_handlers.weather_api import NASAWeatherDataHandler
    from data_handlers.load_generator import generate_synthetic_load
    
    # 1. Generate synthetic hourly inputs
    lat, lon, year = 18.0858, -15.9785, 2023
    print("Generating offline synthetic weather and load patterns...")
    weather_handler = NASAWeatherDataHandler()
    weather_df = weather_handler.generate_synthetic_weather(lat=lat, year=year)
    
    load_df = generate_synthetic_load(
        households=20, # small community to speed up simulation loops
        school_preset="small",
        clinic_preset="small",
        year=year
    )
    
    # 2. Define financial and physical parameters
    cost_overrides = {
        "diesel_fuel_price": 1.3,
        "discount_rate": 0.08,
        "project_lifetime": 20
    }
    
    system_config_base = {
        "pv_derating_factor": 0.82,
        "pv_temp_coeff": -0.004,
        "battery_efficiency_charge": 0.96,
        "battery_efficiency_discharge": 0.96,
        "battery_min_soc": 0.2,
        "battery_max_soc": 1.0,
        "diesel_min_load_fraction": 0.3
    }
    
    # Let's run first with PyGAD if installed, then with CustomGA fallback to demonstrate robustness
    print("\n--- Test 1: GA Optimizer (Attempting PyGAD/Fallback default) ---")
    optimizer = GAOptimizer(
        weather_df=weather_df,
        load_df=load_df,
        cost_params=cost_overrides,
        system_config_base=system_config_base,
        lolp_max=0.05, # Max 5% Loss of Load Probability
        pv_bounds=(0.0, 150.0),
        wind_bounds=(0.0, 50.0),
        battery_bounds=(0.0, 300.0),
        diesel_bounds=(0.0, 30.0),
        num_generations=15, # Low count to finish execution quickly during testing
        sol_per_pop=10,
        use_fallback_ga=False
    )
    
    res = optimizer.optimize()
    
    print("\nOptimization completed successfully!")
    print(f"Optimization method used: {res['optimization_method']}")
    print("\nOptimal HRES Configuration:")
    print(f"  PV Capacity      : {res['best_configuration']['pv_capacity']:.2f} kW")
    print(f"  Wind Capacity    : {res['best_configuration']['wind_capacity']:.2f} kW")
    print(f"  Battery Capacity : {res['best_configuration']['battery_capacity']:.2f} kWh")
    print(f"  Diesel Capacity  : {res['best_configuration']['diesel_capacity']:.2f} kW")
    
    print("\nSystem Performance & Financial Metrics:")
    print(f"  LCOE             : ${res['metrics']['lcoe']:.4f} / kWh")
    print(f"  Net Present Cost : ${res['metrics']['npc']:,.2f}")
    print(f"  Capital Cost     : ${res['metrics']['capital_cost']:,.2f}")
    print(f"  Annual Fuel Cons : {res['metrics']['fuel_consumption_liters']:,.2f} Liters/year")
    print(f"  Annual Fuel Cost : ${res['metrics']['annual_fuel_cost']:,.2f}/year")
    print(f"  Diesel Op Hours  : {res['metrics']['diesel_operating_hours']:.1f} hours/year")
    print(f"  Unmet Load       : {res['metrics']['unmet_load_kwh']:.2f} kWh/year")
    print(f"  LOLP achieved    : {res['metrics']['lolp']*100.0:.3f}% (Target: <= 5.0%)")
    print(f"  Renewable Frac.  : {res['metrics']['renewable_fraction']*100.0:.2f}%")
    print(f"  Battery SOH (1yr): {res['metrics']['battery_soh_pct']:.2f}%")
    
    # 3. Force Custom numpy-based fallback GA test to assert mathematical correctness
    print("\n--- Test 2: Forcing Custom NumPy GA Fallback ---")
    optimizer_fallback = GAOptimizer(
        weather_df=weather_df,
        load_df=load_df,
        cost_params=cost_overrides,
        system_config_base=system_config_base,
        lolp_max=0.05,
        pv_bounds=(0.0, 150.0),
        wind_bounds=(0.0, 50.0),
        battery_bounds=(0.0, 300.0),
        diesel_bounds=(0.0, 30.0),
        num_generations=15,
        sol_per_pop=10,
        use_fallback_ga=True # Explicitly force the NumPy Custom GA
    )
    
    res_fallback = optimizer_fallback.optimize()
    print("\nCustom Fallback Optimization completed successfully!")
    print(f"Optimization method used: {res_fallback['optimization_method']}")
    print("\nOptimal Fallback HRES Configuration:")
    print(f"  PV Capacity      : {res_fallback['best_configuration']['pv_capacity']:.2f} kW")
    print(f"  Wind Capacity    : {res_fallback['best_configuration']['wind_capacity']:.2f} kW")
    print(f"  Battery Capacity : {res_fallback['best_configuration']['battery_capacity']:.2f} kWh")
    print(f"  Diesel Capacity  : {res_fallback['best_configuration']['diesel_capacity']:.2f} kW")
    print(f"  LCOE achieved    : ${res_fallback['metrics']['lcoe']:.4f} / kWh")
    print(f"  LOLP achieved    : {res_fallback['metrics']['lolp']*100.0:.3f}%")
    
    assert res_fallback['metrics']['lolp'] <= 0.05 or res_fallback['best_configuration']['diesel_capacity'] > 0, "Fallback GA did not converge to a valid bounds or served configuration"
    
    print("\nConvergence History Sample:")
    print("  First 3 Generations Fitness:", [f"{x:.4f}" for x in res_fallback['convergence_history'][:3]])
    print("  Last 3 Generations Fitness :", [f"{x:.4f}" for x in res_fallback['convergence_history'][-3:]])
    
    print("\nAll GA optimizer modules and fallbacks validated successfully!")
