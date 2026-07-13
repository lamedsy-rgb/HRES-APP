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

    # 1. Instantiate the physical component models
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
    
    bat_capacity = config.get("battery_capacity", 0.0)
    battery_system = None
    if bat_capacity > 0:
        battery_system = BatterySystem(
            capacity=bat_capacity,
            nominal_voltage=config.get("battery_nominal_voltage", 48.0),
            min_soc=config.get("battery_min_soc", 0.2),
            max_soc=config.get("battery_max_soc", 1.0),
            initial_soc=config.get("battery_initial_soc", 0.5),
            efficiency_charge=config.get("battery_efficiency_charge", 0.95),
            efficiency_discharge=config.get("battery_efficiency_discharge", 0.95),
            max_charge_rate=config.get("battery_max_charge_rate", 0.5),
            max_discharge_rate=config.get("battery_max_discharge_rate", 0.5),
            self_discharge_rate=config.get("battery_self_discharge_rate", 0.0001),
            lifetime_cycles=config.get("battery_lifetime_cycles", 3000.0)
        )
        
    diesel_capacity = config.get("diesel_capacity", 0.0)
    diesel_system = None
    if diesel_capacity > 0:
        diesel_system = DieselSystem(
            capacity=diesel_capacity,
            f0=config.get("diesel_f0", 0.08),
            f1=config.get("diesel_f1", 0.25),
            min_load_fraction=config.get("diesel_min_load_fraction", 0.3)
        )

    # 2. Extract load values (with fallback)
    if "total_load" in load_df.columns:
        loads = load_df["total_load"].values
    elif "load" in load_df.columns:
        loads = load_df["load"].values
    else:
        loads = load_df.iloc[:, 0].values

    # 3. Vectorized pre-calculation of PV and Wind power outputs (highly optimized)
    solar_irradiances = weather_df["solar_irradiance"].values
    temperatures = weather_df["temperature"].values
    wind_speeds = weather_df["wind_speed"].values
    
    pv_powers = pv_system.calculate_power(solar_irradiances, temperatures)
    wind_powers = wind_system.calculate_power(wind_speeds)

    # 4. Pre-allocate arrays for simulation outputs (for execution speed)
    battery_charge_arr = np.zeros(N)
    battery_discharge_arr = np.zeros(N)
    battery_soc_arr = np.zeros(N)
    diesel_power_arr = np.zeros(N)
    diesel_fuel_arr = np.zeros(N)
    dump_power_arr = np.zeros(N)
    unmet_load_arr = np.zeros(N)

    # 5. Chronological EMS Simulation Loop
    for t in range(N):
        dispatch = dispatch_hour(
            pv_power=pv_powers[t],
            wind_power=wind_powers[t],
            load=loads[t],
            battery=battery_system,
            diesel=diesel_system,
            duration_hr=1.0
        )
        
        battery_charge_arr[t] = dispatch["battery_charge"]
        battery_discharge_arr[t] = dispatch["battery_discharge"]
        battery_soc_arr[t] = dispatch["battery_soc"]
        diesel_power_arr[t] = dispatch["diesel_power"]
        diesel_fuel_arr[t] = dispatch["diesel_fuel"]
        dump_power_arr[t] = dispatch["dump_power"]
        unmet_load_arr[t] = dispatch["unmet_load"]

    # 6. Construct hourly metrics DataFrame
    hourly_df = pd.DataFrame({
        "solar_irradiance": solar_irradiances,
        "wind_speed": wind_speeds,
        "temperature": temperatures,
        "load": loads,
        "pv_output": pv_powers,
        "wind_output": wind_powers,
        "battery_charge": battery_charge_arr,
        "battery_discharge": battery_discharge_arr,
        "battery_soc": battery_soc_arr,
        "diesel_output": diesel_power_arr,
        "diesel_fuel": diesel_fuel_arr,
        "dump_power": dump_power_arr,
        "unmet_load": unmet_load_arr
    }, index=weather_df.index)

    # 7. Calculate Summary Statistics
    total_load = float(np.sum(loads))
    total_pv_gen = float(np.sum(pv_powers))
    total_wind_gen = float(np.sum(wind_powers))
    total_diesel_gen = float(np.sum(diesel_power_arr))
    total_fuel = float(np.sum(diesel_fuel_arr))
    total_unmet = float(np.sum(unmet_load_arr))
    
    lolp = total_unmet / total_load if total_load > 0 else 0.0
    
    # Renewable Fraction (RF) = 1.0 - (Total Diesel Generation / Total Load Served)
    total_load_served = total_load - total_unmet
    if total_load_served > 0:
        rf = 1.0 - (total_diesel_gen / total_load_served)
    else:
        rf = 1.0
    # Keep RF physically bound between 0 and 1
    rf = max(0.0, min(1.0, rf))
    
    capacity_shortage_hours = int(np.sum(unmet_load_arr > 1e-3))
    
    # Battery health metrics
    battery_soh = 100.0
    battery_remaining_capacity = 0.0
    battery_throughput = 0.0
    if battery_system is not None:
        status = battery_system.get_status()
        battery_soh = status["current_capacity_kwh"] / status["capacity_nominal_kwh"] * 100.0 if status["capacity_nominal_kwh"] > 0 else 0.0
        battery_remaining_capacity = status["current_capacity_kwh"]
        battery_throughput = status["total_throughput_kwh"]

    summary_stats = {
        "total_pv_generation_kwh": total_pv_gen,
        "total_wind_generation_kwh": total_wind_gen,
        "total_diesel_generation_kwh": total_diesel_gen,
        "total_fuel_consumption_liters": total_fuel,
        "total_unmet_load_kwh": total_unmet,
        "lolp": lolp,
        "renewable_fraction": rf,
        "capacity_shortage_hours": capacity_shortage_hours,
        "battery_soh_pct": battery_soh,
        "battery_remaining_capacity_kwh": battery_remaining_capacity,
        "battery_total_throughput_kwh": battery_throughput
    }

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
