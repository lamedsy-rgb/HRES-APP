import os
import sys
import tempfile
import unittest
import numpy as np
import pandas as pd

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data_handlers.weather_api import NASAWeatherDataHandler
from data_handlers.load_generator import generate_synthetic_load
from simulation.engine import run_simulation
from optimization.financials import calculate_lcoe, calculate_npc, DEFAULT_COST_PARAMS
from optimization.ga_optimizer import GAOptimizer
from reporting.report_generator import generate_engineering_report


class TestReportingAndAuditFixes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        handler = NASAWeatherDataHandler()
        cls.weather_df = handler.generate_synthetic_weather(lat=18.0735, year=2023)
        cls.load_df = generate_synthetic_load(
            households=40,
            school_preset="small",
            clinic_preset="small",
            year=2023,
        )
        cls.config = {
            "pv_capacity": 55.0,
            "wind_capacity": 12.0,
            "battery_capacity": 140.0,
            "diesel_capacity": 20.0,
            "pv_derating_factor": 0.82,
            "battery_initial_soc": 0.5,
            "diesel_min_load_fraction": 0.3,
        }
        cls.hourly_df, cls.summary = run_simulation(cls.weather_df, cls.load_df, cls.config)
        diesel_hrs = float((cls.hourly_df["diesel_output"] > 1e-3).sum())
        bat_deg = max(0.0, (100.0 - cls.summary["battery_soh_pct"]) / 100.0)
        lcoe, fin_details = calculate_lcoe(
            pv_capacity=cls.config["pv_capacity"],
            wind_capacity=cls.config["wind_capacity"],
            battery_capacity=cls.config["battery_capacity"],
            diesel_capacity=cls.config["diesel_capacity"],
            cost_params=DEFAULT_COST_PARAMS,
            annual_diesel_operating_hours=diesel_hrs,
            annual_fuel_consumption=cls.summary["total_fuel_consumption_liters"],
            annual_battery_degradation_fraction=bat_deg,
            total_annual_load_kwh=float(cls.load_df["total_load"].sum()),
            annual_unmet_load_kwh=cls.summary["total_unmet_load_kwh"],
        )
        cls.results = {
            "best_configuration": {
                "pv_capacity": cls.config["pv_capacity"],
                "wind_capacity": cls.config["wind_capacity"],
                "battery_capacity": cls.config["battery_capacity"],
                "diesel_capacity": cls.config["diesel_capacity"],
            },
            "metrics": {
                "lcoe": lcoe,
                "npc": fin_details["npc"],
                "capital_cost": fin_details["capital_cost"],
                "annual_om_cost": fin_details["annual_om_cost"],
                "annual_fuel_cost": fin_details["annual_fuel_cost"],
                "unmet_load_kwh": cls.summary["total_unmet_load_kwh"],
                "lolp": cls.summary["lolp"],
                "renewable_fraction": cls.summary["renewable_fraction"],
                "diesel_operating_hours": diesel_hrs,
                "fuel_consumption_liters": cls.summary["total_fuel_consumption_liters"],
                "battery_soh_pct": cls.summary["battery_soh_pct"],
            },
            "financial_details": fin_details,
            "optimization_method": "custom_numpy",
        }

    def test_generate_report_en_and_pngs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_html = os.path.join(tmpdir, "report_en.html")
            charts_dir = os.path.join(tmpdir, "charts")
            generated = generate_engineering_report(
                hourly_df=self.hourly_df,
                results=self.results,
                output_path=out_html,
                metadata={
                    "project_name": "Nouakchott Test Microgrid",
                    "site_name": "Nouakchott, Mauritania",
                    "latitude": 18.0735,
                    "longitude": -15.9582,
                    "year": 2023,
                },
                language="en",
                save_charts_dir=charts_dir,
            )
            self.assertTrue(os.path.exists(generated))
            self.assertGreater(os.path.getsize(generated), 50_000)

            with open(generated, "r", encoding="utf-8") as f:
                content = f.read()

            # Self-contained base64 images (3 charts) and valid structure
            self.assertIn("<!DOCTYPE html>", content)
            self.assertEqual(content.count("data:image/png;base64,"), 3)
            self.assertIn("Nouakchott Test Microgrid", content)
            self.assertIn("18.0735", content)
            self.assertNotIn(">nan<", content.lower())
            self.assertNotIn("$nan", content.lower())

            # Standalone PNGs saved
            for fname in [
                "monthly_energy_balance.png",
                "weekly_dispatch_soc.png",
                "lifecycle_cost_breakdown.png",
            ]:
                p = os.path.join(charts_dir, fname)
                self.assertTrue(os.path.exists(p), f"Missing PNG: {fname}")
                self.assertGreater(os.path.getsize(p), 5_000)

    def test_generate_report_fr_and_ar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for lang, expected_phrase in [
                ("fr", "Synthèse Exécutive"),
                ("ar", "الملخص التنفيذي"),
            ]:
                out_html = os.path.join(tmpdir, f"report_{lang}.html")
                generate_engineering_report(
                    hourly_df=self.hourly_df,
                    results=self.results,
                    output_path=out_html,
                    language=lang,
                )
                with open(out_html, "r", encoding="utf-8") as f:
                    content = f.read()
                self.assertIn(expected_phrase, content)
                self.assertEqual(content.count("data:image/png;base64,"), 3)

    def test_weather_api_fill_value_before_unit_conversion(self):
        """Regression test: NASA -999.0 fill values in irradiance must be ffilled before /1000."""
        handler = NASAWeatherDataHandler()
        timestamps = pd.date_range("2023-01-01 00:00:00", periods=4, freq="h").strftime("%Y%m%d%H")
        mock_json = {
            "header": {"fill_value": -999.0},
            "properties": {
                "parameter": {
                    "ALLSKY_SFC_SW_DWN": {
                        timestamps[0]: 500.0,
                        timestamps[1]: -999.0,  # Missing hour should ffill to 500.0 -> 0.5 kW/m2
                        timestamps[2]: 600.0,
                        timestamps[3]: 400.0,
                    },
                    "T2M": {t: 25.0 for t in timestamps},
                    "WS10M": {t: 5.0 for t in timestamps},
                }
            },
        }
        parsed = handler._parse_api_json(mock_json, year=2023)
        self.assertAlmostEqual(parsed["solar_irradiance"].iloc[0], 0.5, places=4)
        self.assertAlmostEqual(parsed["solar_irradiance"].iloc[1], 0.5, places=4)

    def test_financials_breakdown_consistency(self):
        """Verify discounted_fixed_om + discounted_fuel == discounted_om."""
        npc = calculate_npc(
            pv_capacity=50.0,
            wind_capacity=10.0,
            battery_capacity=100.0,
            diesel_capacity=20.0,
            cost_params=DEFAULT_COST_PARAMS,
            annual_diesel_operating_hours=800.0,
            annual_fuel_consumption=3000.0,
            annual_battery_degradation_fraction=0.04,
        )
        self.assertAlmostEqual(
            npc["discounted_fixed_om"] + npc["discounted_fuel"],
            npc["discounted_om"],
            places=6,
        )
        self.assertAlmostEqual(
            npc["capital_cost"] + npc["discounted_om"] + npc["discounted_replacement"] - npc["discounted_salvage"],
            npc["npc"],
            places=6,
        )

    def test_custom_ga_small_population_no_crash(self):
        """Regression test: sol_per_pop < tournament_size must not raise ValueError."""
        optimizer = GAOptimizer(
            weather_df=self.weather_df.iloc[:168],
            load_df=self.load_df.iloc[:168],
            num_generations=1,
            sol_per_pop=2,
            use_fallback_ga=True,
        )
        res = optimizer.optimize()
        self.assertIn("best_configuration", res)


if __name__ == "__main__":
    unittest.main()
