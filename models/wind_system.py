import numpy as np
from typing import Union, List

def calculate_wind_power(
    wind_speed_anemometer: Union[float, np.ndarray, List[float]],
    anemometer_height: float,
    hub_height: float,
    rated_capacity: float,
    wind_shear_exponent: float = 0.14,
    cut_in_speed: float = 3.0,
    rated_speed: float = 12.0,
    cut_out_speed: float = 25.0,
    use_cubic_curve: bool = True
) -> Union[float, np.ndarray]:
    """
    Calculate the wind turbine output power based on the wind speed at anemometer height,
    adjusted to the hub height, using a piecewise power curve.

    Parameters:
        wind_speed_anemometer (float or array-like): Wind speed(s) at anemometer height (m/s).
        anemometer_height (float): Height of the anemometer measurement (m).
        hub_height (float): Hub height of the wind turbine (m).
        rated_capacity (float): Rated capacity of the wind turbine (kW).
        wind_shear_exponent (float): Power law wind shear exponent alpha (default 0.14 or 1/7).
        cut_in_speed (float): Wind speed at which turbine starts generating power (default 3.0 m/s).
        rated_speed (float): Wind speed at which turbine reaches rated capacity (default 12.0 m/s).
        cut_out_speed (float): Wind speed at which turbine shuts down for safety (default 25.0 m/s).
        use_cubic_curve (bool): If True, uses cubic interpolation in the transition zone;
                                if False, uses linear interpolation (default True).

    Returns:
        float or np.ndarray: Calculated output power in kW.
    """
    if anemometer_height <= 0:
        raise ValueError("Anemometer height must be strictly positive.")
    if hub_height <= 0:
        raise ValueError("Hub height must be strictly positive.")
    if cut_in_speed >= rated_speed or rated_speed >= cut_out_speed:
        raise ValueError("Wind speed parameters must satisfy: cut_in_speed < rated_speed < cut_out_speed")

    v_anem = np.asarray(wind_speed_anemometer, dtype=float)
    
    # Wind speed height correction: V_hub = V_anemometer * (hub_height / anemometer_height) ** alpha
    v_hub = v_anem * (hub_height / anemometer_height) ** wind_shear_exponent

    # Define conditions for piecewise power curve
    cond_zero = (v_hub < cut_in_speed) | (v_hub >= cut_out_speed)
    cond_rated = (v_hub >= rated_speed) & (v_hub < cut_out_speed)
    cond_transition = (v_hub >= cut_in_speed) & (v_hub < rated_speed)

    # Compute power in the transition region (between cut-in and rated speeds)
    if use_cubic_curve:
        transition_power = rated_capacity * ((v_hub - cut_in_speed) / (rated_speed - cut_in_speed)) ** 3
    else:
        transition_power = rated_capacity * ((v_hub - cut_in_speed) / (rated_speed - cut_in_speed))

    # Construct the piecewise output
    condlist = [cond_zero, cond_rated, cond_transition]
    choicelist = [0.0, rated_capacity, transition_power]
    
    P = np.select(condlist, choicelist, default=0.0)

    # If the input was a scalar, return a scalar float
    if np.ndim(wind_speed_anemometer) == 0:
        return float(P)
    
    return P

class WindSystem:
    """
    Class representing a Wind Turbine System.
    """
    def __init__(
        self,
        anemometer_height: float,
        hub_height: float,
        rated_capacity: float,
        wind_shear_exponent: float = 0.14,
        cut_in_speed: float = 3.0,
        rated_speed: float = 12.0,
        cut_out_speed: float = 25.0,
        use_cubic_curve: bool = True
    ):
        """
        Initialize the wind system parameters.
        """
        self.anemometer_height = anemometer_height
        self.hub_height = hub_height
        self.rated_capacity = rated_capacity
        self.wind_shear_exponent = wind_shear_exponent
        self.cut_in_speed = cut_in_speed
        self.rated_speed = rated_speed
        self.cut_out_speed = cut_out_speed
        self.use_cubic_curve = use_cubic_curve

    def calculate_power(self, wind_speed_anemometer: Union[float, np.ndarray, List[float]]) -> Union[float, np.ndarray]:
        """
        Calculate hourly output power based on the wind speed.
        """
        return calculate_wind_power(
            wind_speed_anemometer=wind_speed_anemometer,
            anemometer_height=self.anemometer_height,
            hub_height=self.hub_height,
            rated_capacity=self.rated_capacity,
            wind_shear_exponent=self.wind_shear_exponent,
            cut_in_speed=self.cut_in_speed,
            rated_speed=self.rated_speed,
            cut_out_speed=self.cut_out_speed,
            use_cubic_curve=self.use_cubic_curve
        )

if __name__ == "__main__":
    print("Testing wind_system.py...")
    # Test parameters
    anem_h = 10.0
    hub_h = 50.0
    cap = 100.0  # 100 kW rated
    alpha = 0.14
    
    # Wind speed height correction calculation:
    # V_hub = V_anem * (50 / 10) ** 0.14 = V_anem * 5 ** 0.14 = V_anem * 1.25059...
    
    # Test case 1: Cut-out speed test
    # If V_anem = 20 m/s, V_hub = 20 * 1.25059 = 25.0118 m/s (which is >= cut-out speed 25 m/s)
    # Output power should be 0.0 kW
    p_high = calculate_wind_power(20.0, anem_h, hub_h, cap, wind_shear_exponent=alpha)
    print(f"High wind test: V_anem=20.0 m/s -> V_hub=25.01 m/s -> Output Power = {p_high:.4f} kW (Expected: 0.0000 kW)")
    assert p_high == 0.0, "Test Case 1 failed"

    # Test case 2: Rated speed test
    # If V_anem = 10 m/s, V_hub = 10 * 1.25268 = 12.5268 m/s (which is between rated 12.0 and cut-out 25.0)
    # Output power should be 100.0 kW (rated capacity)
    p_rated = calculate_wind_power(10.0, anem_h, hub_h, cap, wind_shear_exponent=alpha)
    print(f"Rated wind test: V_anem=10.0 m/s -> V_hub=12.53 m/s -> Output Power = {p_rated:.4f} kW (Expected: 100.0000 kW)")
    assert abs(p_rated - cap) < 1e-6, "Test Case 2 failed"

    # Test case 3: Cut-in speed test (V_hub < cut_in)
    # If V_anem = 1.0 m/s, V_hub = 1.25268 m/s (which is < 3.0 m/s)
    # Output power should be 0.0 kW
    p_low = calculate_wind_power(1.0, anem_h, hub_h, cap, wind_shear_exponent=alpha)
    print(f"Low wind test: V_anem=1.0 m/s -> V_hub=1.25 m/s -> Output Power = {p_low:.4f} kW (Expected: 0.0000 kW)")
    assert p_low == 0.0, "Test Case 3 failed"

    # Test case 4: Transition speed test (cubic power curve)
    # If V_anem = 5.0 m/s, V_hub = 5 * 1.25268 = 6.26363 m/s
    # Output Power = 100 * ((6.26363 - 3) / (12 - 3)) ** 3 = 100 * (3.26363 / 9) ** 3 = 100 * 0.36262 ** 3 = 100 * 0.047684 = 4.7684 kW
    p_transition = calculate_wind_power(5.0, anem_h, hub_h, cap, wind_shear_exponent=alpha)
    print(f"Transition wind test (cubic): V_anem=5.0 m/s -> V_hub=6.26 m/s -> Output Power = {p_transition:.4f} kW (Expected: ~4.7684 kW)")
    assert abs(p_transition - 4.76841) < 1e-4, "Test Case 4 failed"

    # Test case 5: Array inputs using class
    wind_sys = WindSystem(anemometer_height=anem_h, hub_height=hub_h, rated_capacity=cap, wind_shear_exponent=alpha)
    speeds = [0.0, 2.0, 5.0, 10.0, 22.0, 30.0]
    powers = wind_sys.calculate_power(speeds)
    print("Array input calculations using WindSystem:")
    for v, p in zip(speeds, powers):
        print(f"  V_anem={v:.1f} m/s -> Power={p:.4f} kW")

    print("All Wind system tests passed successfully!")
