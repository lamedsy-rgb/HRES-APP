# -*- coding: utf-8 -*-
"""
Nouakchott, Mauritania — Rural Microgrid Case Study Generator.

Runs the 8,760-hour HRES physics simulation and Genetic Algorithm optimizer
for a 60-household coastal Sahelian community near Nouakchott (18.0735° N, -15.9582° W)
and exports:
  - examples/sample_report_nouakchott.html (self-contained print-ready A4 report)
  - examples/monthly_energy_balance.png
  - examples/weekly_dispatch_soc.png
  - examples/lifecycle_cost_breakdown.png
"""

import os
import sys
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_handlers.weather_api import NASAWeatherDataHandler
from data_handlers.load_generator import generate_synthetic_load
from simulation.engine import run_simulation
from optimization.ga_optimizer import GAOptimizer
from reporting.report_generator import generate_engineering_report


def main():
    examples_dir = os.path.dirname(os.path.abspath(__file__))
    lat, lon, year = 18.0735, -15.9582, 2023

    # Reproducible GA seed
    np.random.seed(2024)

    # 1. Generate 8,760-hour meteorological data (100% offline deterministic)
    weather_handler = NASAWeatherDataHandler()
    weather_df = weather_handler.generate_synthetic_weather(lat=lat, year=year)

    # 2. Generate 8,760-hour community electrical demand profile
    #    60 households + medium school + small 24/7 health clinic
    load_df = generate_synthetic_load(
        households=60,
        school_preset="medium",
        clinic_preset="small",
        year=year,
    )

    # 3. Financial & technical assumptions (Sahel / Mauritania off-grid benchmark)
    cost_params = {
        "pv_capex": 950.0,
        "wind_capex": 1550.0,
        "battery_capex": 290.0,
        "diesel_capex": 400.0,
        "diesel_fuel_price": 1.30,
        "discount_rate": 0.08,
        "project_lifetime": 25,
    }

    system_config_base = {
        "pv_derating_factor": 0.82,
        "pv_temp_coeff": -0.004,
        "battery_efficiency_charge": 0.96,
        "battery_efficiency_discharge": 0.96,
        "battery_min_soc": 0.20,
        "battery_max_soc": 1.00,
        "diesel_min_load_fraction": 0.30,
    }

    # 4. Run Genetic Algorithm optimization (target LOLP <= 1.0%)
    optimizer = GAOptimizer(
        weather_df=weather_df,
        load_df=load_df,
        cost_params=cost_params,
        system_config_base=system_config_base,
        lolp_max=0.01,
        pv_bounds=(10.0, 180.0),
        wind_bounds=(0.0, 60.0),
        battery_bounds=(20.0, 400.0),
        diesel_bounds=(0.0, 40.0),
        num_generations=20,
        sol_per_pop=16,
        use_fallback_ga=True,
    )
    results = optimizer.optimize()

    # 5. Re-run hourly simulation at the optimal sizing for full 8,760-hour traces
    optimal_config = {**system_config_base, **results["best_configuration"]}
    hourly_df, summary = run_simulation(weather_df, load_df, optimal_config)

    # 6. Export standalone A4 HTML engineering report + showcase PNG charts
    report_path = os.path.join(examples_dir, "sample_report_nouakchott.html")
    metadata = {
        "project_name": "Nouakchott Rural Microgrid — Techno-Economic Sizing Report",
        "site_name": "Nouakchott Peri-Urban Village, Mauritania (60 HH + School + Clinic)",
        "latitude": lat,
        "longitude": lon,
        "year": year,
    }

    generated = generate_engineering_report(
        hourly_df=hourly_df,
        results=results,
        output_path=report_path,
        metadata=metadata,
        cost_params=cost_params,
        language="en",
        save_charts_dir=examples_dir,
    )

    cfg = results["best_configuration"]
    m = results["metrics"]
    print("\n=== Nouakchott Case Study Summary ===")
    print(f"PV Capacity       : {cfg['pv_capacity']:.2f} kWp")
    print(f"Wind Capacity     : {cfg['wind_capacity']:.2f} kW")
    print(f"Battery Capacity  : {cfg['battery_capacity']:.2f} kWh")
    print(f"Diesel Capacity   : {cfg['diesel_capacity']:.2f} kW")
    print(f"LCOE              : ${m['lcoe']:.4f}/kWh")
    print(f"NPC               : ${m['npc']:,.2f}")
    print(f"Initial CAPEX     : ${m['capital_cost']:,.2f}")
    print(f"Renewable Fraction: {m['renewable_fraction']*100:.2f}%")
    print(f"LOLP              : {m['lolp']*100:.3f}%")
    print(f"Annual Fuel       : {m['fuel_consumption_liters']:,.1f} L/yr")
    print(f"Battery Year-1 SOH: {m['battery_soh_pct']:.2f}%")
    print(f"Report saved to   : {generated}")


if __name__ == "__main__":
    main()
