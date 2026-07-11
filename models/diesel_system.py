import warnings
import numpy as np
from typing import Union, List

def calculate_diesel_fuel(
    active_power: Union[float, np.ndarray, List[float]],
    capacity: float,
    f0: float = 0.08,
    f1: float = 0.25,
    min_load_fraction: float = 0.3
) -> Union[float, np.ndarray]:
    """
    Calculate the diesel generator's hourly fuel consumption.

    Parameters:
        active_power (float or array-like): Active power output of the generator in kW.
        capacity (float): Rated capacity of the generator in kW.
        f0 (float): Fuel curve intercept coefficient in L/hr/kW_rated (default 0.08).
        f1 (float): Fuel curve slope coefficient in L/hr/kW_output (default 0.25).
        min_load_fraction (float): Minimum allowable operating load fraction (default 0.3 or 30%).

    Returns:
        float or np.ndarray: Fuel consumption in Liters per hour (L/hr).
    """
    if capacity <= 0:
        raise ValueError("Rated capacity of diesel generator must be strictly positive.")

    P_out = np.asarray(active_power, dtype=float)
    min_load = min_load_fraction * capacity

    # Check for minimum load constraint violations
    violations = (P_out > 0.0) & (P_out < min_load)
    if np.any(violations):
        warnings.warn(
            f"Diesel generator is operating below its minimum load constraint of {min_load:.2f} kW "
            f"({min_load_fraction * 100:.1f}% of capacity). This may cause engine wet stacking.",
            UserWarning
        )

    # Fuel consumption (L/hr) = F0 * capacity + F1 * active_power if active_power > 0 else 0
    fuel = np.where(P_out > 0.0, (f0 * capacity) + (f1 * P_out), 0.0)

    # Return scalar float if input was a scalar
    if np.ndim(active_power) == 0:
        return float(fuel)

    return fuel

class DieselSystem:
    """
    Class representing a Diesel Generator system.
    """
    def __init__(
        self,
        capacity: float,
        f0: float = 0.08,
        f1: float = 0.25,
        min_load_fraction: float = 0.3
    ):
        """
        Initialize the diesel system parameters.

        Parameters:
            capacity (float): Rated capacity of the generator in kW.
            f0 (float): Fuel curve intercept coefficient in L/hr/kW_rated (default 0.08).
            f1 (float): Fuel curve slope coefficient in L/hr/kW_output (default 0.25).
            min_load_fraction (float): Minimum operating load fraction (default 0.3).
        """
        self.capacity = capacity
        self.f0 = f0
        self.f1 = f1
        self.min_load_fraction = min_load_fraction

    def calculate_fuel(self, active_power: Union[float, np.ndarray, List[float]]) -> Union[float, np.ndarray]:
        """
        Calculate hourly fuel consumption for the diesel generator.
        """
        return calculate_diesel_fuel(
            active_power=active_power,
            capacity=self.capacity,
            f0=self.f0,
            f1=self.f1,
            min_load_fraction=self.min_load_fraction
        )

    def check_min_load_violation(self, active_power: Union[float, np.ndarray, List[float]]) -> Union[bool, np.ndarray]:
        """
        Check if power output is positive but below the minimum load constraint.
        """
        P_out = np.asarray(active_power, dtype=float)
        min_load = self.min_load_fraction * self.capacity
        violations = (P_out > 0.0) & (P_out < min_load)
        if np.ndim(active_power) == 0:
            return bool(violations)
        return violations

if __name__ == "__main__":
    print("Testing diesel_system.py...")
    
    # Test parameters: 50 kW capacity generator
    cap = 50.0
    
    # Test case 1: Generator is OFF (power = 0)
    # Fuel consumption should be 0.0 L/hr, no warnings.
    fuel_off = calculate_diesel_fuel(0.0, cap)
    print(f"Generator OFF: Fuel = {fuel_off:.4f} L/hr (Expected: 0.0000 L/hr)")
    assert fuel_off == 0.0, "Test Case 1 failed"

    # Test case 2: Generator is running at rated load (50 kW)
    # Fuel = 0.08 * 50 + 0.25 * 50 = 4.0 + 12.5 = 16.5 L/hr
    fuel_rated = calculate_diesel_fuel(50.0, cap)
    print(f"Generator Rated: Fuel = {fuel_rated:.4f} L/hr (Expected: 16.5000 L/hr)")
    assert abs(fuel_rated - 16.5) < 1e-6, "Test Case 2 failed"

    # Test case 3: Generator operating below minimum load constraint (e.g. 10 kW, which is < 15 kW)
    # This should trigger a UserWarning, fuel = 0.08 * 50 + 0.25 * 10 = 4.0 + 2.5 = 6.5 L/hr
    print("Testing below-min-load warning (should print a warning message):")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fuel_low = calculate_diesel_fuel(10.0, cap)
        print(f"Generator Low Load: Fuel = {fuel_low:.4f} L/hr (Expected: 6.5000 L/hr)")
        assert abs(fuel_low - 6.5) < 1e-6, "Fuel calculation failed for low load"
        assert len(w) == 1, "Min load warning was not raised"
        assert issubclass(w[0].category, UserWarning), "Warning category mismatch"
        print(f"Captured Warning: {w[0].message}")

    # Test case 4: Array inputs using class
    diesel_sys = DieselSystem(capacity=100.0)
    power_profile = [0.0, 20.0, 50.0, 80.0, 100.0]
    
    print("\nArray inputs calculation:")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fuels = diesel_sys.calculate_fuel(power_profile)
        violations = diesel_sys.check_min_load_violation(power_profile)
        for p, f, v in zip(power_profile, fuels, violations):
            print(f"  Power={p:.1f} kW -> Fuel={f:.2f} L/hr (Min Load Violation: {v})")
            
    print("All Diesel generator tests passed successfully!")
