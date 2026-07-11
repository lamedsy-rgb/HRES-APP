import numpy as np
from typing import Union, List

def calculate_pv_power(
    irradiance: Union[float, np.ndarray, List[float]],
    ambient_temp: Union[float, np.ndarray, List[float]],
    capacity: float,
    derating_factor: float = 0.8,
    temp_coeff: float = -0.004,
    noct: float = 45.0
) -> Union[float, np.ndarray]:
    """
    Calculate the PV output power based on solar irradiance and ambient temperature.

    Parameters:
        irradiance (float or array-like): Solar Irradiance in kW/m^2.
        ambient_temp (float or array-like): Ambient Temperature in degrees Celsius.
        capacity (float): Rated capacity of PV system in kW.
        derating_factor (float): Derating factor (default 0.8).
        temp_coeff (float): Temperature coefficient of power in /C (default -0.004).
        noct (float): Nominal Operating Cell Temperature in degrees Celsius (default 45.0).

    Returns:
        float or np.ndarray: PV output power in kW.
    """
    # Ensure inputs are numpy arrays for element-wise mathematical operations
    G = np.asarray(irradiance, dtype=float)
    Ta = np.asarray(ambient_temp, dtype=float)

    # Compute cell temperature: T_cell = T_ambient + (G / 0.8) * (NOCT - 20)
    T_cell = Ta + (G / 0.8) * (noct - 20.0)

    # Compute power: P = capacity * derating_factor * G * (1 + temp_coeff * (T_cell - 25))
    P = capacity * derating_factor * G * (1.0 + temp_coeff * (T_cell - 25.0))

    # Output power cannot be negative; force negative values to 0.0
    P = np.maximum(0.0, P)

    # If both inputs were scalars (int or float), return a scalar float
    if np.ndim(irradiance) == 0 and np.ndim(ambient_temp) == 0:
        return float(P)
    
    return P

class PVSystem:
    """
    Class representing a Photo-Voltaic (PV) system.
    """
    def __init__(
        self,
        capacity: float,
        derating_factor: float = 0.8,
        temp_coeff: float = -0.004,
        noct: float = 45.0
    ):
        """
        Initialize the PV system parameters.

        Parameters:
            capacity (float): Rated capacity of PV system in kW.
            derating_factor (float): Derating factor (default 0.8).
            temp_coeff (float): Temperature coefficient of power in /C (default -0.004).
            noct (float): Nominal Operating Cell Temperature in degrees Celsius (default 45.0).
        """
        self.capacity = capacity
        self.derating_factor = derating_factor
        self.temp_coeff = temp_coeff
        self.noct = noct

    def calculate_power(
        self,
        irradiance: Union[float, np.ndarray, List[float]],
        ambient_temp: Union[float, np.ndarray, List[float]]
    ) -> Union[float, np.ndarray]:
        """
        Calculate hourly output power.

        Parameters:
            irradiance (float or array-like): Solar Irradiance in kW/m^2.
            ambient_temp (float or array-like): Ambient Temperature in degrees Celsius.

        Returns:
            float or np.ndarray: PV output power in kW.
        """
        return calculate_pv_power(
            irradiance=irradiance,
            ambient_temp=ambient_temp,
            capacity=self.capacity,
            derating_factor=self.derating_factor,
            temp_coeff=self.temp_coeff,
            noct=self.noct
        )

if __name__ == "__main__":
    print("Testing pv_system.py...")
    # Test case 1: Standard test with scalar inputs
    # G = 0.8 kW/m2, Ta = 25 C, capacity = 10 kW.
    # T_cell = 25 + (0.8 / 0.8) * (45 - 20) = 25 + 25 = 50 C
    # P = 10 * 0.8 * 0.8 * (1 + -0.004 * (50 - 25)) = 6.4 * (1 - 0.004 * 25) = 6.4 * 0.9 = 5.76 kW
    p_out = calculate_pv_power(0.8, 25.0, 10.0)
    print(f"Scalar calculation: G=0.8 kW/m2, Ta=25C, capacity=10kW -> Output Power = {p_out:.4f} kW (Expected: 5.7600 kW)")
    assert abs(p_out - 5.76) < 1e-6, "Test Case 1 failed"

    # Test case 2: Nighttime (G = 0)
    p_night = calculate_pv_power(0.0, 15.0, 10.0)
    print(f"Night calculation: G=0.0 -> Output Power = {p_night:.4f} kW (Expected: 0.0000 kW)")
    assert p_night == 0.0, "Test Case 2 failed"

    # Test case 3: Array inputs
    irradiances = [0.0, 0.2, 0.5, 0.8, 1.0]
    temps = [15.0, 20.0, 25.0, 30.0, 35.0]
    pv_sys = PVSystem(capacity=15.0)
    powers = pv_sys.calculate_power(irradiances, temps)
    print("Array input calculations:")
    for g, t, p in zip(irradiances, temps, powers):
        print(f"  G={g:.1f} kW/m2, Ta={t:.1f}C -> Power={p:.4f} kW")

    print("All PV system tests passed successfully!")
