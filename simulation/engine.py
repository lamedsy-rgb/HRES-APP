import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

# Add project root to sys.path to allow absolute imports when running directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.pv_system import PVSystem
from models.wind_system import WindSystem
from models.battery_system import BatterySystem
from models.diesel_system import DieselSystem
from simulation.ems import dispatch_hour

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _simulate_ems_arrays(
    pv_powers: np.ndarray,
    wind_powers: np.ndarray,
    loads: np.ndarray,
    config: Dict[str, Any],
    return_hourly_arrays: bool = True
):
    """
    High-performance chronological 8,760h EMS kernel mathematically equivalent to
    iterating simulation.ems.dispatch_hour with BatterySystem and DieselSystem.
    Eliminates per-hour Python dict allocations and scalar NumPy wrapper overhead.
    """
    N = len(loads)
    bat_capacity = float(config.get("battery_capacity", 0.0))
    has_bat = bat_capacity > 0.0
    if has_bat:
        min_soc = float(config.get("battery_min_soc", 0.2))
        max_soc = float(config.get("battery_max_soc", 1.0))
        initial_soc = float(config.get("battery_initial_soc", 0.5))
        if not (0.0 <= min_soc < max_soc <= 1.0):
            raise ValueError("SoC limits must satisfy 0.0 <= min_soc < max_soc <= 1.0")
        if not (0.0 <= initial_soc <= 1.0):
            raise ValueError("Initial SoC must be between 0.0 and 1.0")
        eff_charge = float(config.get("battery_efficiency_charge", 0.95))
        eff_discharge = float(config.get("battery_efficiency_discharge", 0.95))
        inv_eff_charge = 1.0 / eff_charge
        inv_eff_discharge = 1.0 / eff_discharge
        max_charge_rate = float(config.get("battery_max_charge_rate", 0.5))
        max_discharge_rate = float(config.get("battery_max_discharge_rate", 0.5))
        self_discharge_rate = float(config.get("battery_self_discharge_rate", 0.0001))
        lifetime_cycles = float(config.get("battery_lifetime_cycles", 3000.0))
        lifetime_throughput_limit = lifetime_cycles * bat_capacity
        inv_lifetime_limit = (1.0 / lifetime_throughput_limit) if lifetime_throughput_limit > 0.0 else 0.0
        current_capacity = bat_capacity
        stored_energy = initial_soc * bat_capacity
        total_throughput = 0.0
    else:
        min_soc = max_soc = eff_charge = eff_discharge = 0.0
        inv_eff_charge = inv_eff_discharge = 0.0
        max_charge_rate = max_discharge_rate = self_discharge_rate = 0.0
        lifetime_throughput_limit = inv_lifetime_limit = 0.0
        current_capacity = stored_energy = total_throughput = 0.0

    diesel_capacity = float(config.get("diesel_capacity", 0.0))
    has_diesel = diesel_capacity > 0.0
    if has_diesel:
        diesel_f0 = float(config.get("diesel_f0", 0.08))
        diesel_f1 = float(config.get("diesel_f1", 0.25))
        diesel_min_load = float(config.get("diesel_min_load_fraction", 0.3)) * diesel_capacity
        diesel_f0_cap = diesel_f0 * diesel_capacity
    else:
        diesel_f0 = diesel_f1 = diesel_min_load = diesel_f0_cap = 0.0

    # Pre-compute net load in C via NumPy and convert to Python list for fastest CPython iteration
    net_loads = (loads - (pv_powers + wind_powers)).tolist()

    total_diesel_gen = 0.0
    total_fuel = 0.0
    total_unmet = 0.0
    total_dump = 0.0
    capacity_shortage_hours = 0
    diesel_operating_hours = 0

    if return_hourly_arrays:
        battery_charge_list = [0.0] * N
        battery_discharge_list = [0.0] * N
        battery_soc_list = [0.0] * N
        diesel_power_list = [0.0] * N
        diesel_fuel_list = [0.0] * N
        dump_power_list = [0.0] * N
        unmet_load_list = [0.0] * N

    for t in range(N):
        net_load = net_loads[t]
        bat_charge = 0.0
        bat_discharge = 0.0
        diesel_p = 0.0
        diesel_f = 0.0
        dump = 0.0
        unmet = 0.0

        if net_load <= 0.0:
            surplus = -net_load
            if has_bat:
                # Apply hourly self-discharge
                loss = self_discharge_rate * current_capacity
                if loss > stored_energy:
                    stored_energy = 0.0
                else:
                    stored_energy -= loss

                max_e_c = max_charge_rate * current_capacity
                headroom = max_soc * current_capacity - stored_energy
                max_e_soc = (headroom * inv_eff_charge) if headroom > 0.0 else 0.0

                actual_charge = surplus
                if max_e_c < actual_charge:
                    actual_charge = max_e_c
                if max_e_soc < actual_charge:
                    actual_charge = max_e_soc
                if actual_charge < 0.0:
                    actual_charge = 0.0

                added = actual_charge * eff_charge
                stored_energy += added
                max_allowed = max_soc * current_capacity
                if stored_energy > max_allowed:
                    stored_energy = max_allowed

                total_throughput += added
                if inv_lifetime_limit > 0.0:
                    decay = 1.0 - total_throughput * inv_lifetime_limit
                    current_capacity = (bat_capacity * decay) if decay > 0.0 else 0.0
                    max_allowed = max_soc * current_capacity
                    if stored_energy > max_allowed:
                        stored_energy = max_allowed

                bat_charge = actual_charge
                dump = surplus - bat_charge
            else:
                dump = surplus
        else:
            deficit = net_load
            if has_bat:
                # Apply hourly self-discharge
                loss = self_discharge_rate * current_capacity
                if loss > stored_energy:
                    stored_energy = 0.0
                else:
                    stored_energy -= loss

                max_e_c = max_discharge_rate * current_capacity
                avail = stored_energy - min_soc * current_capacity
                max_e_soc = (avail * eff_discharge) if avail > 0.0 else 0.0

                actual_discharge = deficit
                if max_e_c < actual_discharge:
                    actual_discharge = max_e_c
                if max_e_soc < actual_discharge:
                    actual_discharge = max_e_soc
                if actual_discharge < 0.0:
                    actual_discharge = 0.0

                stored_energy -= actual_discharge * inv_eff_discharge
                if stored_energy < 0.0:
                    stored_energy = 0.0

                total_throughput += actual_discharge
                if inv_lifetime_limit > 0.0:
                    decay = 1.0 - total_throughput * inv_lifetime_limit
                    current_capacity = (bat_capacity * decay) if decay > 0.0 else 0.0
                    max_allowed = max_soc * current_capacity
                    if stored_energy > max_allowed:
                        stored_energy = max_allowed

                bat_discharge = actual_discharge
                remaining_deficit = deficit - bat_discharge
            else:
                remaining_deficit = deficit

            if remaining_deficit > 0.0:
                if has_diesel:
                    if remaining_deficit < diesel_min_load:
                        diesel_p = diesel_min_load
                        excess_gen = diesel_min_load - remaining_deficit
                        if has_bat:
                            # Charge battery with excess min-load output (without double self-discharge)
                            max_e_c = max_charge_rate * current_capacity
                            headroom = max_soc * current_capacity - stored_energy
                            max_e_soc = (headroom * inv_eff_charge) if headroom > 0.0 else 0.0

                            actual_charge = excess_gen
                            if max_e_c < actual_charge:
                                actual_charge = max_e_c
                            if max_e_soc < actual_charge:
                                actual_charge = max_e_soc
                            if actual_charge < 0.0:
                                actual_charge = 0.0

                            added = actual_charge * eff_charge
                            stored_energy += added
                            max_allowed = max_soc * current_capacity
                            if stored_energy > max_allowed:
                                stored_energy = max_allowed

                            total_throughput += added
                            if inv_lifetime_limit > 0.0:
                                decay = 1.0 - total_throughput * inv_lifetime_limit
                                current_capacity = (bat_capacity * decay) if decay > 0.0 else 0.0
                                max_allowed = max_soc * current_capacity
                                if stored_energy > max_allowed:
                                    stored_energy = max_allowed

                            bat_charge = actual_charge
                            dump = excess_gen - bat_charge
                        else:
                            dump = excess_gen
                    elif remaining_deficit <= diesel_capacity:
                        diesel_p = remaining_deficit
                    else:
                        diesel_p = diesel_capacity
                        unmet = remaining_deficit - diesel_capacity

                    if diesel_p > 0.0:
                        diesel_f = diesel_f0_cap + diesel_f1 * diesel_p
                else:
                    unmet = remaining_deficit

        total_diesel_gen += diesel_p
        total_fuel += diesel_f
        total_dump += dump
        total_unmet += unmet
        if unmet > 1e-3:
            capacity_shortage_hours += 1
        if diesel_p > 1e-3:
            diesel_operating_hours += 1

        if return_hourly_arrays:
            battery_charge_list[t] = bat_charge
            battery_discharge_list[t] = bat_discharge
            battery_soc_list[t] = (stored_energy / current_capacity) if (has_bat and current_capacity > 0.0) else 0.0
            diesel_power_list[t] = diesel_p
            diesel_fuel_list[t] = diesel_f
            dump_power_list[t] = dump
            unmet_load_list[t] = unmet

    total_load = float(np.sum(loads))
    total_pv_gen = float(np.sum(pv_powers))
    total_wind_gen = float(np.sum(wind_powers))

    lolp = total_unmet / total_load if total_load > 0.0 else 0.0
    total_load_served = total_load - total_unmet
    if total_load_served > 0.0:
        rf = 1.0 - (total_diesel_gen / total_load_served)
    else:
        rf = 1.0
    rf = max(0.0, min(1.0, rf))

    if has_bat:
        battery_soh = (current_capacity / bat_capacity) * 100.0 if bat_capacity > 0.0 else 0.0
        battery_remaining_capacity = current_capacity
        battery_throughput = total_throughput
    else:
        battery_soh = 100.0
        battery_remaining_capacity = 0.0
        battery_throughput = 0.0

    summary_stats = {
        "total_load_kwh": total_load,
        "total_pv_generation_kwh": total_pv_gen,
        "total_wind_generation_kwh": total_wind_gen,
        "total_diesel_generation_kwh": total_diesel_gen,
        "total_fuel_consumption_liters": total_fuel,
        "total_dump_power_kwh": total_dump,
        "total_unmet_load_kwh": total_unmet,
        "lolp": lolp,
        "renewable_fraction": rf,
        "capacity_shortage_hours": capacity_shortage_hours,
        "diesel_operating_hours": float(diesel_operating_hours),
        "battery_soh_pct": battery_soh,
        "battery_remaining_capacity_kwh": battery_remaining_capacity,
        "battery_total_throughput_kwh": battery_throughput,
    }

    if not return_hourly_arrays:
        return None, summary_stats

    hourly_arrays = {
        "battery_charge": np.array(battery_charge_list, dtype=np.float64),
        "battery_discharge": np.array(battery_discharge_list, dtype=np.float64),
        "battery_soc": np.array(battery_soc_list, dtype=np.float64),
        "diesel_output": np.array(diesel_power_list, dtype=np.float64),
        "diesel_fuel": np.array(diesel_fuel_list, dtype=np.float64),
        "dump_power": np.array(dump_power_list, dtype=np.float64),
        "unmet_load": np.array(unmet_load_list, dtype=np.float64),
    }
    return hourly_arrays, summary_stats


def run_simulation_fast(
    pv_powers: np.ndarray,
    wind_powers: np.ndarray,
    loads: np.ndarray,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fast summary-only simulation using pre-extracted NumPy arrays.
    Ideal for Genetic Algorithm fitness evaluation (skips pandas DataFrame construction).
    """
    _, summary_stats = _simulate_ems_arrays(
        pv_powers=pv_powers,
        wind_powers=wind_powers,
        loads=loads,
        config=config,
        return_hourly_arrays=False
    )
    return summary_stats


def run_simulation(
    weather_df: pd.DataFrame,
    load_df: pd.DataFrame,
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes the 8760-hour simulation loop for the HRES.
    
    Parameters:
        weather_df (pd.DataFrame): Hourly weather data containing:
            - 'solar_irradiance' (kW/m^2)
            - 'temperature' (degrees C)
            - 'wind_speed' (m/s)
        load_df (pd.DataFrame): Hourly load demand containing:
            - 'total_load' (kW) (or fallback to first column)
        config (Dict[str, Any]): System configuration parameters:
            - pv_capacity (kW)
            - wind_capacity (kW)
            - battery_capacity (kWh)
            - diesel_capacity (kW)
            - PV System parameters (optional): pv_derating_factor, pv_temp_coeff, pv_noct
            - Wind System parameters (optional): wind_anemometer_height, wind_hub_height,
                                                 wind_shear_exponent, wind_cut_in_speed,
                                                 wind_rated_speed, wind_cut_out_speed,
                                                 wind_use_cubic_curve
            - Battery System parameters (optional): battery_nominal_voltage, battery_min_soc,
                                                    battery_max_soc, battery_initial_soc,
                                                    battery_efficiency_charge, battery_efficiency_discharge,
                                                    battery_max_charge_rate, battery_max_discharge_rate,
                                                    battery_self_discharge_rate, battery_lifetime_cycles
            - Diesel System parameters (optional): diesel_f0, diesel_f1, diesel_min_load_fraction
            
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]:
            - hourly_df: DataFrame containing all hourly simulation metrics
            - summary_stats: Dictionary containing annual system metrics and KPIs
    """
    N = len(weather_df)
    if len(load_df) != N:
        raise ValueError(f"Length mismatch: weather_df has {N} rows, but load_df has {len(load_df)} rows.")

    # 1. Instantiate PV and Wind physical models for vectorized hourly output
    pv_system = PVSystem(
        capacity=config.get("pv_capacity", 0.0),
        derating_factor=config.get("pv_derating_factor", 0.8),
        temp_coeff=config.get("pv_temp_coeff", -0.004),
        noct=config.get("pv_noct", 45.0)
    )
    
    wind_system = WindSystem(
        anemometer_height=config.get("wind_anemometer_height", 10.0),
        hub_height=config.get("wind_hub_height", 50.0),
        rated_capacity=config.get("wind_capacity", 0.0),
        wind_shear_exponent=config.get("wind_shear_exponent", 0.14),
        cut_in_speed=config.get("wind_cut_in_speed", 3.0),
        rated_speed=config.get("wind_rated_speed", 12.0),
        cut_out_speed=config.get("wind_cut_out_speed", 25.0),
        use_cubic_curve=config.get("wind_use_cubic_curve", True)
    )

    # 2. Extract load & weather NumPy arrays
    if "total_load" in load_df.columns:
        loads = load_df["total_load"].to_numpy(dtype=np.float64, copy=False)
    elif "load" in load_df.columns:
        loads = load_df["load"].to_numpy(dtype=np.float64, copy=False)
    else:
        loads = load_df.iloc[:, 0].to_numpy(dtype=np.float64, copy=False)

    solar_irradiances = weather_df["solar_irradiance"].to_numpy(dtype=np.float64, copy=False)
    temperatures = weather_df["temperature"].to_numpy(dtype=np.float64, copy=False)
    wind_speeds = weather_df["wind_speed"].to_numpy(dtype=np.float64, copy=False)
    
    pv_powers = pv_system.calculate_power(solar_irradiances, temperatures)
    wind_powers = wind_system.calculate_power(wind_speeds)

    # 3. Execute optimized chronological EMS loop
    hourly_arrays, summary_stats = _simulate_ems_arrays(
        pv_powers=pv_powers,
        wind_powers=wind_powers,
        loads=loads,
        config=config,
        return_hourly_arrays=True
    )

    # 4. Construct hourly metrics DataFrame
    hourly_df = pd.DataFrame({
        "solar_irradiance": solar_irradiances,
        "wind_speed": wind_speeds,
        "temperature": temperatures,
        "load": loads,
        "pv_output": pv_powers,
        "wind_output": wind_powers,
        "battery_charge": hourly_arrays["battery_charge"],
        "battery_discharge": hourly_arrays["battery_discharge"],
        "battery_soc": hourly_arrays["battery_soc"],
        "diesel_output": hourly_arrays["diesel_output"],
        "diesel_fuel": hourly_arrays["diesel_fuel"],
        "dump_power": hourly_arrays["dump_power"],
        "unmet_load": hourly_arrays["unmet_load"]
    }, index=weather_df.index)

    return hourly_df, summary_stats

if __name__ == "__main__":
    print("==================================================")
    print("Testing simulation/engine.py loop execution...")
    print("==================================================")
    
    from data_handlers.weather_api import NASAWeatherDataHandler
    from data_handlers.load_generator import generate_synthetic_load
    
    # Generate weather and load data
    lat, lon, year = 18.0858, -15.9785, 2023
    weather_handler = NASAWeatherDataHandler()
    weather_df = weather_handler.generate_synthetic_weather(lat=lat, year=year)
    
    load_df = generate_synthetic_load(
        households=50,
        school_preset="medium",
        clinic_preset="small",
        year=year
    )
    
    # Define test configuration
    config = {
        # Capacities
        "pv_capacity": 60.0,       # kW
        "wind_capacity": 30.0,     # kW
        "battery_capacity": 100.0, # kWh
        "diesel_capacity": 25.0,   # kW
        
        # PV params
        "pv_derating_factor": 0.8,
        "pv_temp_coeff": -0.004,
        "pv_noct": 45.0,
        
        # Wind params
        "wind_anemometer_height": 10.0,
        "wind_hub_height": 50.0,
        "wind_shear_exponent": 0.14,
        "wind_cut_in_speed": 3.0,
        "wind_rated_speed": 12.0,
        "wind_cut_out_speed": 25.0,
        "wind_use_cubic_curve": True,
        
        # Battery params
        "battery_nominal_voltage": 48.0,
        "battery_min_soc": 0.2,
        "battery_max_soc": 1.0,
        "battery_initial_soc": 0.6,
        "battery_efficiency_charge": 0.95,
        "battery_efficiency_discharge": 0.95,
        "battery_max_charge_rate": 0.5,
        "battery_max_discharge_rate": 0.5,
        "battery_self_discharge_rate": 0.0001,
        "battery_lifetime_cycles": 1500.0, # lower cycles to check degradation
        
        # Diesel params
        "diesel_f0": 0.08,
        "diesel_f1": 0.25,
        "diesel_min_load_fraction": 0.3
    }
    
    # Run the 8760-hour simulation
    hourly_res, summary = run_simulation(weather_df, load_df, config)
    
    # Output results
    print("\nSimulation completed successfully!")
    print("\n--- Summary Statistics ---")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"{k:35s}: {v:12.4f}")
        else:
            print(f"{k:35s}: {v:12d}")
            
    print("\n--- Sample Hourly Outputs (First 5 Hours) ---")
    columns_to_show = [
        "load", "pv_output", "wind_output", 
        "battery_charge", "battery_discharge", "battery_soc",
        "diesel_output", "diesel_fuel", "dump_power", "unmet_load"
    ]
    print(hourly_res[columns_to_show].head())
    
    # Perform basic sanity assertions
    assert len(hourly_res) == 8760, "Hourly outputs should contain exactly 8760 hours."
    assert summary["total_pv_generation_kwh"] > 0, "PV generation should be positive."
    assert summary["lolp"] >= 0.0 and summary["lolp"] <= 1.0, "LOLP must be between 0.0 and 1.0."
    assert summary["renewable_fraction"] >= 0.0 and summary["renewable_fraction"] <= 1.0, "Renewable fraction must be between 0.0 and 1.0."
    assert summary["battery_soh_pct"] <= 100.0, "Battery State of Health cannot exceed 100%."
    
    print("\nAll engine checks passed!")
