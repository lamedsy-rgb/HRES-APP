import io
import os
import sys
import time
import unittest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from web_app import app


class TestHRESWebAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_serves_spa_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("HRES Optimizer", resp.text)
        self.assertIn("/static/app.js", resp.text)

    def test_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("default_cost_params", data)
        self.assertIn("engine", data)

    def test_preview_endpoint(self):
        payload = {
            "latitude": 18.0735,
            "longitude": -15.9582,
            "site_name": "Nouakchott, Mauritania",
            "year": 2023,
            "weather_source": "synthetic",
            "households": 60,
            "school_preset": "medium",
            "clinic_preset": "small",
        }
        resp = self.client.post("/api/preview", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["weather_source"], "synthetic")
        self.assertEqual(data["summary"]["hours"], 8760)
        self.assertGreater(data["summary"]["annual_demand_kwh"], 10000.0)
        self.assertEqual(len(data["preview_7d"]["load_kw"]), 168)
        self.assertEqual(len(data["monthly"]["ghi_daily_kwh_m2"]), 12)
        self.assertEqual(len(data["monthly"]["wind_avg_ms"]), 12)

    def test_upload_weather_csv_and_use_in_simulation(self):
        # Build a valid 8760-row CSV in W/m2 to also verify automatic W/m2 -> kW/m2 unit conversion
        n = 8760
        hours = np.arange(n)
        df = pd.DataFrame({
            "solar_irradiance": np.maximum(0.0, np.sin(np.pi * ((hours % 24) - 6) / 12)) * 850.0,  # W/m2
            "temperature": 26.0 + 5.0 * np.cos(2 * np.pi * ((hours % 24) - 15) / 24),
            "wind_speed": 5.5 + 1.5 * np.sin(2 * np.pi * hours / 24),
        })
        csv_bytes = df.to_csv(index=False).encode("utf-8")

        resp = self.client.post(
            "/api/upload-weather?year=2023&households=50&school_preset=small&clinic_preset=small",
            files={"file": ("custom_site_weather.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["weather_source"], "custom_upload")
        self.assertIn("weather_id", data)
        self.assertIn("kW/m²", data["parse_note"])
        self.assertLessEqual(max(data["preview_7d"]["solar_kw_m2"]), 1.0)

        # Verify uploaded weather_id works in manual simulation
        sim_resp = self.client.post(
            "/api/simulate-manual",
            json={
                "latitude": 18.0735,
                "longitude": -15.9582,
                "weather_id": data["weather_id"],
                "households": 50,
                "school_preset": "small",
                "clinic_preset": "small",
                "pv_capacity": 80.0,
                "wind_capacity": 10.0,
                "battery_capacity": 180.0,
                "diesel_capacity": 15.0,
            },
        )
        self.assertEqual(sim_resp.status_code, 200)
        sim_data = sim_resp.json()
        self.assertEqual(sim_data["metadata"]["weather_source"], "custom_upload")
        self.assertGreater(sim_data["metrics"]["total_pv_generation_kwh"], 0.0)

    def test_simulate_manual_and_report_export(self):
        sim_payload = {
            "latitude": 18.0735,
            "longitude": -15.9582,
            "site_name": "Nouakchott, Mauritania",
            "year": 2023,
            "weather_source": "synthetic",
            "households": 60,
            "school_preset": "medium",
            "clinic_preset": "small",
            "pv_capacity": 120.0,
            "wind_capacity": 5.0,
            "battery_capacity": 300.0,
            "diesel_capacity": 15.0,
            "cost_params": {"diesel_fuel_price": 1.30, "discount_rate": 0.08, "project_lifetime": 25},
        }
        resp = self.client.post("/api/simulate-manual", json=sim_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("run_id", data)
        self.assertGreater(data["metrics"]["lcoe"], 0.0)
        self.assertGreater(data["metrics"]["npc"], 0.0)
        self.assertGreaterEqual(data["metrics"]["renewable_fraction"], 0.0)
        self.assertLessEqual(data["metrics"]["renewable_fraction"], 1.0)
        self.assertEqual(len(data["monthly_balance"]["pv_mwh"]), 12)
        self.assertEqual(len(data["hourly_dispatch"]["load"]), 8760)
        self.assertEqual(len(data["hourly_dispatch"]["soc_pct"]), 8760)

        # Test bankable HTML/PDF report export in FR and EN
        for lang, expected_phrase in [("fr", "Synthèse Exécutive"), ("en", "Executive Summary")]:
            rep = self.client.post(
                "/api/report",
                json={
                    "run_id": data["run_id"],
                    "language": lang,
                    "sample_week_start_day": 150,
                },
            )
            self.assertEqual(rep.status_code, 200)
            self.assertIn("text/html", rep.headers.get("content-type", ""))
            self.assertIn("<!DOCTYPE html>", rep.text)
            self.assertIn(expected_phrase, rep.text)
            self.assertEqual(rep.text.count("data:image/png;base64,"), 3)

    def test_optimize_job_lifecycle(self):
        opt_payload = {
            "latitude": 18.0735,
            "longitude": -15.9582,
            "site_name": "Nouakchott, Mauritania",
            "year": 2023,
            "weather_source": "synthetic",
            "households": 40,
            "school_preset": "small",
            "clinic_preset": "small",
            "enable_pv": True,
            "enable_wind": True,
            "enable_battery": True,
            "enable_diesel": True,
            "lolp_max": 0.05,
            "num_generations": 3,
            "sol_per_pop": 6,
            "use_fallback_ga": True,
        }
        start_resp = self.client.post("/api/optimize", json=opt_payload)
        self.assertEqual(start_resp.status_code, 200)
        job_id = start_resp.json()["job_id"]

        # Poll until completion (typically < 0.5s with FastNumPy engine)
        final_job = None
        for _ in range(60):
            poll = self.client.get(f"/api/jobs/{job_id}")
            self.assertEqual(poll.status_code, 200)
            final_job = poll.json()
            if final_job["status"] in ("completed", "failed"):
                break
            time.sleep(0.1)

        self.assertIsNotNone(final_job)
        self.assertEqual(final_job["status"], "completed", f"Job failed: {final_job.get('error')}")
        self.assertEqual(final_job["progress_pct"], 100.0)
        self.assertGreater(len(final_job["logs"]), 0)
        self.assertIsNotNone(final_job["result"])
        self.assertIn("run_id", final_job["result"])
        self.assertGreater(final_job["result"]["metrics"]["lcoe"], 0.0)


if __name__ == "__main__":
    unittest.main()
