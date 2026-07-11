import os
import sys
import unittest
import numpy as np
import pandas as pd

# Add project root to sys.path to allow absolute imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports for testing
from data_handlers.weather_api import NASAWeatherDataHandler
from data_handlers.load_generator import generate_synthetic_load
from models.pv_system import calculate_pv_power, PVSystem
from models.wind_system import calculate_wind_power, WindSystem
from models.battery_system import BatterySystem
from models.diesel_system import calculate_diesel_fuel, DieselSystem
from simulation.ems import dispatch_hour, EMS
from simulation.engine import run_simulation
from optimization.financials import calculate_lcoe, calculate_npc, DEFAULT_COST_PARAMS
from optimization.ga_optimizer import GAOptimizer, CustomGA

class TestHRES(unittest.TestCase):
    
    def setUp(self):
        # We can construct miniature weather and load DataFrames for faster testing of the 8760 simulation
        # Using 8760 points so it is consistent with standard simulation size
        dates = pd.date_range(start="2023-01-01 00:00:00", end="2023-12-31 23:00:00", freq='h')
        dates = dates[~((dates.month == 2) & (dates.day == 29))] # Drop Feb 29
        self.assertEqual(len(dates), 8760)
        
        # Synthetic weather
        self.weather_df = pd.DataFrame({
            "solar_irradiance": np.sin(np.linspace(0, 2*np.pi*365, 8760)) * 0.5 + 0.5, # 0 to 1 kW/m2
            "temperature": np.sin(np.linspace(0, 2*np.pi*365, 8760)) * 10 + 20, # 10 to 30 C
            "wind_speed": np.sin(np.linspace(0, 2*np.pi*365, 8760)) * 10 + 10 # 0 to 20 m/s
        }, index=dates)
        
        # Synthetic load
        self.load_df = pd.DataFrame({
            "total_load": np.sin(np.linspace(0, 2*np.pi*365, 8760)) * 50 + 100 # 50 to 150 kW
        }, index=dates)

    def test_weather_generator(self):
        handler = NASAWeatherDataHandler()
        df = handler.generate_synthetic_weather(lat=45.0, year=2023)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 8760)
        self.assertIn("solar_irradiance", df.columns)
        self.assertIn("temperature", df.columns)
        self.assertIn("wind_speed", df.columns)

    def test_load_generator(self):
        df = generate_synthetic_load(households=50, school_preset='medium', clinic_preset='small', year=2023)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 8760)
        self.assertIn("total_load", df.columns)
        self.assertIn("household_load", df.columns)
        self.assertIn("school_load", df.columns)
        self.assertIn("clinic_load", df.columns)

    def test_physical_calculations(self):
        # 1. PV Output Power
        # G = 0.8 kW/m2, Ta = 25 C, capacity = 10 kW.
        # T_cell = 25 + (0.8 / 0.8) * (45 - 20) = 50 C
        # P = 10 * 0.8 * 0.8 * (1 - 0.004 * (50 - 25)) = 6.4 * 0.9 = 5.76 kW
        p_pv = calculate_pv_power(0.8, 25.0, 10.0)
        self.assertAlmostEqual(p_pv, 5.76)
        
        # 2. Wind speed adjustment and piecewise power curve
        # Hub height correction: V_hub = V_anem * (hub_height / anemometer_height) ** alpha
        # For anem_h=10, hub_h=50, alpha=0.14: correction factor = 5 ** 0.14 = 1.25059...
        # At V_anem = 10 m/s, V_hub = 12.5059 m/s. This is >= rated speed 12.0 and < cut-out speed 25.0.
        # So output power should be rated capacity.
        p_wind = calculate_wind_power(10.0, 10.0, 50.0, 100.0, wind_shear_exponent=0.14)
        self.assertAlmostEqual(p_wind, 100.0)
        
        # 3. Battery charge/discharge limits and capacity SOH degradation
        bat = BatterySystem(capacity=100.0, initial_soc=0.5, lifetime_cycles=100)
        self.assertEqual(bat.soc, 0.5)
        # Charge limits
        accepted = bat.charge(50.0, 1.0) # should accept some charge
        self.assertGreater(accepted, 0.0)
        self.assertLessEqual(accepted, 50.0)
        
        # Stored energy tracking and degradation
        throughput_before = bat.total_throughput
        bat.discharge(50.0, 1.0)
        self.assertGreater(bat.total_throughput, throughput_before)
        self.assertLess(bat.current_capacity, 100.0) # check degradation occurred
        
        # 4. Diesel fuel consumption and load warnings
        fuel_rated = calculate_diesel_fuel(50.0, 50.0) # capacity 50, active power 50
        # Fuel = 0.08 * 50 + 0.25 * 50 = 16.5 L/hr
        self.assertAlmostEqual(fuel_rated, 16.5)
        
        # Check low load warning
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            calculate_diesel_fuel(10.0, 50.0) # 10 kW < 15 kW (30% load)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, UserWarning))

    def test_simulation_and_energy_balance(self):
        config = {
            "pv_capacity": 50.0,
            "wind_capacity": 50.0,
            "battery_capacity": 100.0,
            "diesel_capacity": 50.0,
            "pv_derating_factor": 0.8,
            "battery_initial_soc": 0.5,
            "diesel_min_load_fraction": 0.3
        }
        hourly_df, summary = run_simulation(self.weather_df, self.load_df, config)
        
        self.assertEqual(len(hourly_df), 8760)
        self.assertIn("lolp", summary)
        self.assertIn("renewable_fraction", summary)
        
        # Energy balance check for each hour:
        # Renewables (PV + Wind) - Load - Battery Charge + Battery Discharge + Diesel Output - Dump Power + Unmet Load = 0
        renewables = hourly_df["pv_output"] + hourly_df["wind_output"]
        balance = renewables - hourly_df["load"] - hourly_df["battery_charge"] + hourly_df["battery_discharge"] + hourly_df["diesel_output"] - hourly_df["dump_power"] + hourly_df["unmet_load"]
        
        # Check that energy balance deviation is extremely close to 0
        max_deviation = np.max(np.abs(balance))
        self.assertLess(max_deviation, 1e-5)

    def test_financials(self):
        # NPC and LCOE calculation
        lcoe, details = calculate_lcoe(
            pv_capacity=50.0,
            wind_capacity=50.0,
            battery_capacity=100.0,
            diesel_capacity=50.0,
            cost_params=DEFAULT_COST_PARAMS,
            annual_diesel_operating_hours=1000.0,
            annual_fuel_consumption=5000.0,
            annual_battery_degradation_fraction=0.05,
            total_annual_load_kwh=100000.0,
            annual_unmet_load_kwh=1000.0
        )
        self.assertGreater(lcoe, 0.0)
        self.assertIn("discounted_replacement", details)
        self.assertIn("npc", details)

    def test_custom_ga(self):
        # CustomGA optimization loop
        optimizer = GAOptimizer(
            weather_df=self.weather_df,
            load_df=self.load_df,
            num_generations=2,
            sol_per_pop=4,
            use_fallback_ga=True # force fallback to CustomGA
        )
        results = optimizer.optimize()
        self.assertIn("best_configuration", results)
        self.assertIn("metrics", results)
        self.assertIn("pv_capacity", results["best_configuration"])
        self.assertIn("wind_capacity", results["best_configuration"])
        self.assertIn("battery_capacity", results["best_configuration"])
        self.assertIn("diesel_capacity", results["best_configuration"])

if __name__ == "__main__":
    unittest.main()
