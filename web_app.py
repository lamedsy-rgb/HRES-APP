# -*- coding: utf-8 -*-
"""
HRES Optimizer v2.0 — Modern FastAPI Web Backend & Static SPA Server.

Serves the single-page engineering web interface (`web/`) and exposes REST APIs for:
  - Meteorological & community load preview (NASA POWER API + instant offline fallback)
  - Custom CSV/Excel weather & load file upload
  - Instant 8,760-hour manual what-if microgrid simulation
  - Asynchronous Genetic Algorithm (GA) optimization with live progress & convergence polling
  - 1-click bankable A4 HTML/PDF engineering report export (FR / EN / AR)

Launch:
    python web_app.py
    python web_app.py --host 127.0.0.1 --port 8000 --open
"""

import os
import sys
import io
import math
import time
import uuid
import json
import logging
import argparse
import tempfile
import threading
import webbrowser
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_handlers.weather_api import NASAWeatherDataHandler
from data_handlers.load_generator import generate_synthetic_load
from simulation.engine import run_simulation
from optimization.financials import DEFAULT_COST_PARAMS, calculate_lcoe
from optimization.ga_optimizer import GAOptimizer
from reporting.report_generator import (
    DIESEL_CO2_KG_PER_LITER,
    BASELINE_DIESEL_L_PER_KWH,
    generate_engineering_report,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hres.web")

WEB_DIR = os.path.join(PROJECT_ROOT, "web")
GUI_DIR = os.path.join(PROJECT_ROOT, "gui")

# ---------------------------------------------------------------------------
# Thread-safe bounded in-memory stores
# ---------------------------------------------------------------------------
_STORE_LOCK = threading.Lock()
_WEATHER_UPLOADS: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_LOAD_UPLOADS: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_SIMULATION_RUNS: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_OPTIMIZATION_JOBS: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_MAX_STORE_ITEMS = 30


def _put_bounded(store: OrderedDict, key: str, value: Any, max_items: int = _MAX_STORE_ITEMS) -> None:
    with _STORE_LOCK:
        store[key] = value
        store.move_to_end(key)
        while len(store) > max_items:
            store.popitem(last=False)


def _get_bounded(store: OrderedDict, key: str) -> Optional[Any]:
    with _STORE_LOCK:
        return store.get(key)


# ---------------------------------------------------------------------------
# Helpers: Sanitization, Weather/Load resolution, Simulation packaging
# ---------------------------------------------------------------------------
def _clean_json_value(val: Any) -> Any:
    """Recursively converts numpy/NaN/Inf values into strict JSON-safe Python primitives."""
    if isinstance(val, dict):
        return {str(k): _clean_json_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_clean_json_value(v) for v in val]
    if isinstance(val, (np.floating, float)):
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, np.ndarray):
        return [_clean_json_value(x) for x in val.tolist()]
    return val


def _standard_8760_index(year: int = 2023) -> pd.DatetimeIndex:
    idx = pd.date_range(start=f"{year}-01-01 00:00:00", end=f"{year}-12-31 23:00:00", freq="h")
    return idx[~((idx.month == 2) & (idx.day == 29))]


def _resolve_weather_df(
    latitude: float,
    longitude: float,
    year: int,
    weather_source: str = "synthetic",
    weather_id: Optional[str] = None,
) -> Tuple[pd.DataFrame, str, Optional[str]]:
    """Resolves an 8,760-hour weather DataFrame from upload, NASA POWER API/cache, or synthetic."""
    if weather_id:
        uploaded = _get_bounded(_WEATHER_UPLOADS, weather_id)
        if uploaded is not None:
            return uploaded["df"], "custom_upload", uploaded.get("filename")

    handler = NASAWeatherDataHandler()
    source_norm = (weather_source or "synthetic").lower().strip()

    if source_norm in ("nasa", "nasa_api", "api"):
        cache_file = os.path.join(
            handler.cache_dir, f"weather_lat_{latitude:.4f}_lon_{longitude:.4f}_year_{year}.json"
        )
        was_cached = os.path.exists(cache_file)
        df = handler.fetch_weather_data(lat=latitude, lon=longitude, year=year)
        if was_cached:
            return df, "nasa_cache", None
        if os.path.exists(cache_file):
            return df, "nasa_api", None
        return df, "synthetic_fallback", None

    # Instant offline synthetic mode (also checks if NASA cache already exists when source == "auto")
    if source_norm == "auto":
        cache_file = os.path.join(
            handler.cache_dir, f"weather_lat_{latitude:.4f}_lon_{longitude:.4f}_year_{year}.json"
        )
        if os.path.exists(cache_file):
            df = handler.fetch_weather_data(lat=latitude, lon=longitude, year=year)
            return df, "nasa_cache", None

    df = handler.generate_synthetic_weather(lat=latitude, year=year)
    return df, "synthetic", None


def _resolve_load_df(
    households: int,
    school_preset: str,
    clinic_preset: str,
    year: int,
    weather_index: pd.DatetimeIndex,
    load_id: Optional[str] = None,
) -> Tuple[pd.DataFrame, str]:
    """Resolves an 8,760-hour community load DataFrame from upload or synthetic generator."""
    if load_id:
        uploaded = _get_bounded(_LOAD_UPLOADS, load_id)
        if uploaded is not None:
            df = uploaded["df"].copy()
            if len(df) == len(weather_index):
                df.index = weather_index
            return df, "custom_upload"

    df = generate_synthetic_load(
        households=max(0, int(households)),
        school_preset=school_preset or "none",
        clinic_preset=clinic_preset or "none",
        year=year,
    )
    if len(df) == len(weather_index):
        df.index = weather_index
    return df, "synthetic"


def _build_preview_payload(
    weather_df: pd.DataFrame,
    load_df: pd.DataFrame,
    weather_source: str,
    load_source: str = "synthetic",
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds lightweight 7-day hourly and 12-month aggregated preview series for the UI."""
    load_col = "total_load" if "total_load" in load_df.columns else load_df.columns[0]
    load_series = load_df[load_col].to_numpy(dtype=np.float64)
    solar_series = weather_df["solar_irradiance"].to_numpy(dtype=np.float64)
    wind_series = weather_df["wind_speed"].to_numpy(dtype=np.float64)
    temp_series = weather_df["temperature"].to_numpy(dtype=np.float64)

    n7 = min(168, len(weather_df))
    w_idx = weather_df.index if isinstance(weather_df.index, pd.DatetimeIndex) else _standard_8760_index()

    monthly_df = pd.DataFrame(
        {
            "ghi": solar_series,
            "wind": wind_series,
            "temp": temp_series,
            "load": load_series,
        },
        index=w_idx,
    )
    m_avg = monthly_df.groupby(monthly_df.index.month).mean().reindex(range(1, 13), fill_value=0.0)
    m_sum = monthly_df.groupby(monthly_df.index.month).sum().reindex(range(1, 13), fill_value=0.0)

    hh_arr = (
        load_df["household_load"].to_numpy(dtype=np.float64)[:n7]
        if "household_load" in load_df.columns
        else load_series[:n7]
    )
    sc_arr = (
        load_df["school_load"].to_numpy(dtype=np.float64)[:n7]
        if "school_load" in load_df.columns
        else np.zeros(n7)
    )
    cl_arr = (
        load_df["clinic_load"].to_numpy(dtype=np.float64)[:n7]
        if "clinic_load" in load_df.columns
        else np.zeros(n7)
    )

    payload = {
        "weather_source": weather_source,
        "load_source": load_source,
        "filename": filename,
        "summary": {
            "hours": int(len(weather_df)),
            "annual_demand_kwh": round(float(np.sum(load_series)), 2),
            "peak_load_kw": round(float(np.max(load_series)), 2),
            "mean_load_kw": round(float(np.mean(load_series)), 2),
            "avg_ghi_kwh_m2_day": round(float(np.mean(solar_series) * 24.0), 2),
            "avg_wind_ms": round(float(np.mean(wind_series)), 2),
            "avg_temp_c": round(float(np.mean(temp_series)), 1),
        },
        "preview_7d": {
            "hours": list(range(n7)),
            "load_kw": [round(float(x), 3) for x in load_series[:n7]],
            "household_kw": [round(float(x), 3) for x in hh_arr],
            "school_kw": [round(float(x), 3) for x in sc_arr],
            "clinic_kw": [round(float(x), 3) for x in cl_arr],
            "solar_kw_m2": [round(float(x), 4) for x in solar_series[:n7]],
            "wind_ms": [round(float(x), 2) for x in wind_series[:n7]],
            "temp_c": [round(float(x), 1) for x in temp_series[:n7]],
        },
        "monthly": {
            "months": list(range(1, 13)),
            "ghi_avg_kw_m2": [round(float(x), 4) for x in m_avg["ghi"].values],
            "ghi_daily_kwh_m2": [round(float(x * 24.0), 2) for x in m_avg["ghi"].values],
            "wind_avg_ms": [round(float(x), 2) for x in m_avg["wind"].values],
            "temp_avg_c": [round(float(x), 1) for x in m_avg["temp"].values],
            "load_mwh": [round(float(x / 1000.0), 2) for x in m_sum["load"].values],
        },
    }
    return _clean_json_value(payload)


def _evaluate_and_package_simulation(
    weather_df: pd.DataFrame,
    load_df: pd.DataFrame,
    pv_capacity: float,
    wind_capacity: float,
    battery_capacity: float,
    diesel_capacity: float,
    cost_params: Dict[str, Any],
    system_config: Dict[str, Any],
    metadata: Dict[str, Any],
    optimization_method: str = "manual",
    convergence_history: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Runs a full 8,760h simulation + financial & CO2 analysis and caches run for reporting."""
    merged_cost = {**DEFAULT_COST_PARAMS, **(cost_params or {})}
    sim_config = {
        "pv_derating_factor": 0.82,
        "pv_temp_coeff": -0.004,
        "pv_noct": 45.0,
        "battery_efficiency_charge": 0.96,
        "battery_efficiency_discharge": 0.96,
        "battery_min_soc": 0.2,
        "battery_max_soc": 1.0,
        "battery_initial_soc": 0.5,
        "diesel_min_load_fraction": 0.3,
        **(system_config or {}),
        "pv_capacity": max(0.0, float(pv_capacity)),
        "wind_capacity": max(0.0, float(wind_capacity)),
        "battery_capacity": max(0.0, float(battery_capacity)),
        "diesel_capacity": max(0.0, float(diesel_capacity)),
    }

    hourly_df, summary = run_simulation(weather_df, load_df, sim_config)
    diesel_hours = float(summary.get("diesel_operating_hours", float((hourly_df["diesel_output"] > 1e-3).sum())))
    fuel_liters = float(summary["total_fuel_consumption_liters"])
    unmet_kwh = float(summary["total_unmet_load_kwh"])
    total_load_kwh = float(summary["total_load_kwh"])
    served_kwh = max(0.0, total_load_kwh - unmet_kwh)
    battery_soh = float(summary["battery_soh_pct"])
    battery_deg = max(0.0, (100.0 - battery_soh) / 100.0)

    lcoe, fin_details = calculate_lcoe(
        pv_capacity=sim_config["pv_capacity"],
        wind_capacity=sim_config["wind_capacity"],
        battery_capacity=sim_config["battery_capacity"],
        diesel_capacity=sim_config["diesel_capacity"],
        cost_params=merged_cost,
        annual_diesel_operating_hours=diesel_hours,
        annual_fuel_consumption=fuel_liters,
        annual_battery_degradation_fraction=battery_deg,
        total_annual_load_kwh=total_load_kwh,
        annual_unmet_load_kwh=unmet_kwh,
    )

    project_lifetime = int(fin_details.get("project_lifetime", merged_cost["project_lifetime"]))
    annual_co2_hybrid_tons = (fuel_liters * DIESEL_CO2_KG_PER_LITER) / 1000.0
    baseline_diesel_liters = served_kwh * BASELINE_DIESEL_L_PER_KWH
    annual_co2_baseline_tons = (baseline_diesel_liters * DIESEL_CO2_KG_PER_LITER) / 1000.0
    annual_co2_avoided_tons = max(0.0, annual_co2_baseline_tons - annual_co2_hybrid_tons)
    lifetime_co2_avoided_tons = annual_co2_avoided_tons * project_lifetime

    # Build canonical results dict compatible with reporting/report_generator.py
    canonical_results = {
        "best_configuration": {
            "pv_capacity": sim_config["pv_capacity"],
            "wind_capacity": sim_config["wind_capacity"],
            "battery_capacity": sim_config["battery_capacity"],
            "diesel_capacity": sim_config["diesel_capacity"],
        },
        "metrics": {
            "lcoe": lcoe,
            "npc": fin_details["npc"],
            "capital_cost": fin_details["capital_cost"],
            "annual_om_cost": fin_details["annual_om_cost"],
            "annual_fixed_om_cost": fin_details["annual_fixed_om_cost"],
            "annual_fuel_cost": fin_details["annual_fuel_cost"],
            "total_load_kwh": total_load_kwh,
            "served_load_kwh": served_kwh,
            "total_pv_generation_kwh": float(summary["total_pv_generation_kwh"]),
            "total_wind_generation_kwh": float(summary["total_wind_generation_kwh"]),
            "total_diesel_generation_kwh": float(summary["total_diesel_generation_kwh"]),
            "total_dump_power_kwh": float(summary["total_dump_power_kwh"]),
            "unmet_load_kwh": unmet_kwh,
            "lolp": float(summary["lolp"]),
            "reliability_pct": max(0.0, min(100.0, (1.0 - float(summary["lolp"])) * 100.0)),
            "capacity_shortage_hours": int(summary["capacity_shortage_hours"]),
            "renewable_fraction": float(summary["renewable_fraction"]),
            "diesel_operating_hours": diesel_hours,
            "fuel_consumption_liters": fuel_liters,
            "battery_soh_pct": battery_soh,
            "battery_total_throughput_kwh": float(summary["battery_total_throughput_kwh"]),
            "annual_co2_hybrid_tons": annual_co2_hybrid_tons,
            "annual_co2_avoided_tons": annual_co2_avoided_tons,
            "lifetime_co2_avoided_tons": lifetime_co2_avoided_tons,
        },
        "financial_details": fin_details,
        "optimization_method": optimization_method,
        "convergence_history": convergence_history or [],
    }

    run_id = uuid.uuid4().hex[:12]
    _put_bounded(
        _SIMULATION_RUNS,
        run_id,
        {
            "hourly_df": hourly_df,
            "results": canonical_results,
            "metadata": metadata,
            "cost_params": merged_cost,
            "created_at": datetime.utcnow().isoformat() + "Z",
        },
    )

    # Monthly energy balance (MWh)
    idx = hourly_df.index if isinstance(hourly_df.index, pd.DatetimeIndex) else _standard_8760_index()
    m_df = pd.DataFrame(
        {
            "pv": hourly_df["pv_output"].to_numpy(dtype=np.float64),
            "wind": hourly_df["wind_output"].to_numpy(dtype=np.float64),
            "diesel": hourly_df["diesel_output"].to_numpy(dtype=np.float64),
            "load": hourly_df["load"].to_numpy(dtype=np.float64),
            "dump": hourly_df["dump_power"].to_numpy(dtype=np.float64),
            "unmet": hourly_df["unmet_load"].to_numpy(dtype=np.float64),
        },
        index=idx,
    )
    m_mwh = m_df.groupby(m_df.index.month).sum().reindex(range(1, 13), fill_value=0.0) / 1000.0

    # Compact rounded 8,760h arrays for instant client-side Week 1..52 interactive dispatch slider
    hourly_compact = {
        "load": np.round(hourly_df["load"].to_numpy(dtype=np.float64), 2).tolist(),
        "pv": np.round(hourly_df["pv_output"].to_numpy(dtype=np.float64), 2).tolist(),
        "wind": np.round(hourly_df["wind_output"].to_numpy(dtype=np.float64), 2).tolist(),
        "diesel": np.round(hourly_df["diesel_output"].to_numpy(dtype=np.float64), 2).tolist(),
        "soc_pct": np.round(np.clip(hourly_df["battery_soc"].to_numpy(dtype=np.float64) * 100.0, 0.0, 100.0), 1).tolist(),
        "unmet": np.round(hourly_df["unmet_load"].to_numpy(dtype=np.float64), 2).tolist(),
    }

    response_payload = {
        "run_id": run_id,
        "best_configuration": canonical_results["best_configuration"],
        "metrics": canonical_results["metrics"],
        "financial_details": fin_details,
        "optimization_method": optimization_method,
        "convergence_history": convergence_history or [],
        "metadata": metadata,
        "monthly_balance": {
            "months": list(range(1, 13)),
            "pv_mwh": [round(float(x), 3) for x in m_mwh["pv"].values],
            "wind_mwh": [round(float(x), 3) for x in m_mwh["wind"].values],
            "diesel_mwh": [round(float(x), 3) for x in m_mwh["diesel"].values],
            "load_mwh": [round(float(x), 3) for x in m_mwh["load"].values],
            "curtailed_mwh": [round(float(x), 3) for x in m_mwh["dump"].values],
            "unmet_mwh": [round(float(x), 3) for x in m_mwh["unmet"].values],
        },
        "hourly_dispatch": hourly_compact,
    }
    return _clean_json_value(response_payload)


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class SiteAndLoadConfig(BaseModel):
    latitude: float = Field(18.0735, ge=-90.0, le=90.0)
    longitude: float = Field(-15.9582, ge=-180.0, le=180.0)
    site_name: str = "Nouakchott, Mauritania"
    project_name: str = "HRES Rural Microgrid Study"
    year: int = Field(2023, ge=2000, le=2030)
    weather_source: str = "synthetic"  # "synthetic" | "nasa" | "auto"
    weather_id: Optional[str] = None
    load_id: Optional[str] = None
    households: int = Field(60, ge=0, le=5000)
    school_preset: str = "medium"
    clinic_preset: str = "small"


class ManualSimRequest(SiteAndLoadConfig):
    pv_capacity: float = Field(80.0, ge=0.0, le=50000.0)
    wind_capacity: float = Field(15.0, ge=0.0, le=50000.0)
    battery_capacity: float = Field(200.0, ge=0.0, le=200000.0)
    diesel_capacity: float = Field(20.0, ge=0.0, le=50000.0)
    cost_params: Dict[str, Any] = Field(default_factory=dict)
    system_config: Dict[str, Any] = Field(default_factory=dict)


class OptimizeRequest(SiteAndLoadConfig):
    enable_pv: bool = True
    enable_wind: bool = True
    enable_battery: bool = True
    enable_diesel: bool = True
    pv_min: float = Field(0.0, ge=0.0)
    pv_max: float = Field(250.0, ge=0.0)
    wind_min: float = Field(0.0, ge=0.0)
    wind_max: float = Field(100.0, ge=0.0)
    battery_min: float = Field(0.0, ge=0.0)
    battery_max: float = Field(600.0, ge=0.0)
    diesel_min: float = Field(0.0, ge=0.0)
    diesel_max: float = Field(60.0, ge=0.0)
    lolp_max: float = Field(0.01, ge=0.0, le=1.0)
    mode: str = "balanced"  # "quick" | "balanced" | "precision" | "custom"
    num_generations: Optional[int] = Field(None, ge=1, le=200)
    sol_per_pop: Optional[int] = Field(None, ge=2, le=100)
    use_fallback_ga: bool = False
    cost_params: Dict[str, Any] = Field(default_factory=dict)
    system_config: Dict[str, Any] = Field(default_factory=dict)


class ReportRequest(BaseModel):
    run_id: Optional[str] = None
    language: str = "fr"
    sample_week_start_day: Optional[int] = Field(None, ge=1, le=358)
    download: bool = False
    project_name: Optional[str] = None
    site_name: Optional[str] = None
    # Optional fallback payload if run_id is not cached (e.g., server restarted)
    fallback_sim: Optional[ManualSimRequest] = None


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="HRES Optimizer Web API",
    description="8,760-hour Hybrid Renewable Energy System simulation, GA optimization & bankable reporting API.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = os.path.join(WEB_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend web/index.html not found.")
    return FileResponse(index_path, media_type="text/html; charset=utf-8")


@app.get("/favicon.png")
def serve_favicon():
    logo_path = os.path.join(GUI_DIR, "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/manifest.json")
def serve_manifest():
    manifest_path = os.path.join(WEB_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="Manifest not found")


@app.get("/icon.svg")
def serve_icon_svg():
    icon_path = os.path.join(WEB_DIR, "icon.svg")
    if os.path.exists(icon_path):
        return FileResponse(icon_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Icon not found")


@app.get("/api/health")
def api_health():
    pygad_ok = False
    try:
        import pygad  # noqa: F401
        pygad_ok = True
    except ImportError:
        pygad_ok = False

    return {
        "status": "ok",
        "service": "HRES Optimizer Web API",
        "version": "2.0.0",
        "engine": "FastNumPy-EMS-8760h",
        "pygad_available": pygad_ok,
        "default_cost_params": DEFAULT_COST_PARAMS,
    }


@app.post("/api/preview")
def api_preview(req: SiteAndLoadConfig):
    try:
        weather_df, w_source, filename = _resolve_weather_df(
            latitude=req.latitude,
            longitude=req.longitude,
            year=req.year,
            weather_source=req.weather_source,
            weather_id=req.weather_id,
        )
        load_df, l_source = _resolve_load_df(
            households=req.households,
            school_preset=req.school_preset,
            clinic_preset=req.clinic_preset,
            year=req.year,
            weather_index=weather_df.index,
            load_id=req.load_id,
        )
        return _build_preview_payload(
            weather_df=weather_df,
            load_df=load_df,
            weather_source=w_source,
            load_source=l_source,
            filename=filename,
        )
    except Exception as e:
        logger.exception("Error in /api/preview")
        raise HTTPException(status_code=400, detail=str(e))


def _parse_uploaded_tabular(contents: bytes, filename: str) -> pd.DataFrame:
    name_low = (filename or "").lower()
    buf = io.BytesIO(contents)
    if name_low.endswith(".csv") or name_low.endswith(".txt"):
        # Support both comma and semicolon CSV delimiters seamlessly
        try:
            df = pd.read_csv(buf)
            if df.shape[1] == 1:
                buf.seek(0)
                df = pd.read_csv(buf, sep=";")
        except Exception:
            buf.seek(0)
            df = pd.read_csv(buf, sep=None, engine="python")
    elif name_low.endswith(".xlsx") or name_low.endswith(".xls"):
        df = pd.read_excel(buf)
    else:
        raise ValueError("Unsupported file format. Please upload a .csv, .xlsx, or .xls file.")
    if df.empty:
        raise ValueError("Uploaded file is empty.")
    return df


@app.post("/api/upload-weather")
async def api_upload_weather(
    file: UploadFile = File(...),
    year: int = Query(2023, ge=2000, le=2030),
    households: int = Query(60, ge=0, le=5000),
    school_preset: str = Query("medium"),
    clinic_preset: str = Query("small"),
):
    try:
        contents = await file.read()
        if not contents:
            raise ValueError("Uploaded weather file is empty.")

        df = _parse_uploaded_tabular(contents, file.filename or "weather.csv")

        solar_col, temp_col, wind_col = None, None, None
        for col in df.columns:
            c_low = str(col).lower().strip()
            if solar_col is None and any(k in c_low for k in ("solar", "irrad", "ghi", "ray", "allsky", "sw_dwn")):
                solar_col = col
            elif temp_col is None and any(k in c_low for k in ("temp", "t2m", "celsius", "tamb")):
                temp_col = col
            elif wind_col is None and any(k in c_low for k in ("wind", "speed", "vent", "ws10", "ws50")):
                wind_col = col

        missing = []
        if solar_col is None:
            missing.append("solar_irradiance / GHI")
        if temp_col is None:
            missing.append("temperature / T2M")
        if wind_col is None:
            missing.append("wind_speed / WS10M")
        if missing:
            raise ValueError(
                f"Could not detect required columns: {', '.join(missing)}. "
                f"Found columns: {', '.join(str(c) for c in df.columns)}"
            )

        solar_vals = pd.to_numeric(df[solar_col], errors="coerce").ffill().bfill().fillna(0.0).to_numpy(dtype=np.float64)
        temp_vals = pd.to_numeric(df[temp_col], errors="coerce").ffill().bfill().fillna(25.0).to_numpy(dtype=np.float64)
        wind_vals = pd.to_numeric(df[wind_col], errors="coerce").ffill().bfill().fillna(4.0).to_numpy(dtype=np.float64)

        # Auto-convert Wh/m2 (or W/m2) to kW/m2 if clearly in W/m2 scale
        converted_units = False
        if float(np.max(solar_vals)) > 5.0:
            solar_vals = solar_vals / 1000.0
            converted_units = True

        solar_vals = np.clip(solar_vals, 0.0, None)
        wind_vals = np.clip(wind_vals, 0.0, None)

        # Normalize to exact 8,760 hourly rows
        n_rows = len(solar_vals)
        note = "Exact 8,760 hourly rows parsed."
        if n_rows == 8784:  # Leap year -> drop Feb 29 (hours 1416..1439)
            keep = np.ones(8784, dtype=bool)
            keep[1416:1440] = False
            solar_vals = solar_vals[keep]
            temp_vals = temp_vals[keep]
            wind_vals = wind_vals[keep]
            note = "Leap-year file (8,784 rows): Feb 29 removed to match 8,760h standard."
        elif n_rows != 8760:
            if n_rows < 24:
                raise ValueError(f"Weather file must contain 8,760 hourly rows (found only {n_rows} rows).")
            # Tile or truncate cleanly to 8760 if partial year / multi-day sample uploaded
            if n_rows > 8760:
                solar_vals = solar_vals[:8760]
                temp_vals = temp_vals[:8760]
                wind_vals = wind_vals[:8760]
                note = f"File had {n_rows} rows; truncated to first 8,760 hours."
            else:
                reps = int(math.ceil(8760 / n_rows))
                solar_vals = np.tile(solar_vals, reps)[:8760]
                temp_vals = np.tile(temp_vals, reps)[:8760]
                wind_vals = np.tile(wind_vals, reps)[:8760]
                note = f"File had {n_rows} rows; tiled cyclically to 8,760 hours."

        if converted_units:
            note += " Irradiance auto-converted from W/m² to kW/m²."

        std_idx = _standard_8760_index(year)
        weather_df = pd.DataFrame(
            {
                "solar_irradiance": solar_vals,
                "temperature": temp_vals,
                "wind_speed": wind_vals,
            },
            index=std_idx,
        )

        weather_id = uuid.uuid4().hex[:12]
        _put_bounded(
            _WEATHER_UPLOADS,
            weather_id,
            {"df": weather_df, "filename": file.filename or "custom_weather.csv"},
        )

        load_df, l_source = _resolve_load_df(
            households=households,
            school_preset=school_preset,
            clinic_preset=clinic_preset,
            year=year,
            weather_index=std_idx,
        )
        preview = _build_preview_payload(
            weather_df=weather_df,
            load_df=load_df,
            weather_source="custom_upload",
            load_source=l_source,
            filename=file.filename,
        )
        preview["weather_id"] = weather_id
        preview["parse_note"] = note
        preview["detected_columns"] = {
            "solar_irradiance": str(solar_col),
            "temperature": str(temp_col),
            "wind_speed": str(wind_col),
        }
        return preview
    except Exception as e:
        logger.warning(f"Weather upload error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/upload-load")
async def api_upload_load(
    file: UploadFile = File(...),
    year: int = Query(2023, ge=2000, le=2030),
):
    try:
        contents = await file.read()
        if not contents:
            raise ValueError("Uploaded load file is empty.")
        df = _parse_uploaded_tabular(contents, file.filename or "load.csv")
        load_col = None
        for col in df.columns:
            c_low = str(col).lower().strip()
            if any(k in c_low for k in ("total_load", "load", "charge", "demand", "cons", "kw")):
                load_col = col
                break
        if load_col is None:
            load_col = df.columns[0]

        vals = pd.to_numeric(df[load_col], errors="coerce").ffill().bfill().fillna(0.0).to_numpy(dtype=np.float64)
        vals = np.clip(vals, 0.0, None)
        if len(vals) == 8784:
            keep = np.ones(8784, dtype=bool)
            keep[1416:1440] = False
            vals = vals[keep]
        elif len(vals) > 8760:
            vals = vals[:8760]
        elif len(vals) < 8760:
            if len(vals) < 24:
                raise ValueError(f"Load file must contain 8,760 hourly rows (found {len(vals)}).")
            vals = np.tile(vals, int(math.ceil(8760 / len(vals))))[:8760]

        std_idx = _standard_8760_index(year)
        load_df = pd.DataFrame({"total_load": vals}, index=std_idx)
        load_id = uuid.uuid4().hex[:12]
        _put_bounded(_LOAD_UPLOADS, load_id, {"df": load_df, "filename": file.filename or "custom_load.csv"})
        return {
            "load_id": load_id,
            "filename": file.filename,
            "detected_column": str(load_col),
            "annual_demand_kwh": round(float(np.sum(vals)), 2),
            "peak_load_kw": round(float(np.max(vals)), 2),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/simulate-manual")
def api_simulate_manual(req: ManualSimRequest):
    try:
        weather_df, w_source, filename = _resolve_weather_df(
            latitude=req.latitude,
            longitude=req.longitude,
            year=req.year,
            weather_source=req.weather_source,
            weather_id=req.weather_id,
        )
        load_df, l_source = _resolve_load_df(
            households=req.households,
            school_preset=req.school_preset,
            clinic_preset=req.clinic_preset,
            year=req.year,
            weather_index=weather_df.index,
            load_id=req.load_id,
        )
        metadata = {
            "project_name": req.project_name,
            "site_name": req.site_name,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "year": req.year,
            "households": req.households,
            "school_preset": req.school_preset,
            "clinic_preset": req.clinic_preset,
            "weather_source": w_source,
            "load_source": l_source,
            "weather_filename": filename,
        }
        return _evaluate_and_package_simulation(
            weather_df=weather_df,
            load_df=load_df,
            pv_capacity=req.pv_capacity,
            wind_capacity=req.wind_capacity,
            battery_capacity=req.battery_capacity,
            diesel_capacity=req.diesel_capacity,
            cost_params=req.cost_params,
            system_config=req.system_config,
            metadata=metadata,
            optimization_method="Manual Simulation",
        )
    except Exception as e:
        logger.exception("Error in /api/simulate-manual")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/optimize")
def api_optimize(req: OptimizeRequest):
    if not (req.enable_pv or req.enable_wind or req.enable_battery or req.enable_diesel):
        raise HTTPException(status_code=400, detail="Enable at least one system component.")

    mode_presets = {
        "quick": (10, 12),
        "balanced": (25, 16),
        "precision": (45, 22),
    }
    default_gens, default_pop = mode_presets.get((req.mode or "balanced").lower(), (25, 16))
    num_gens = req.num_generations if req.num_generations is not None else default_gens
    sol_pop = req.sol_per_pop if req.sol_per_pop is not None else default_pop

    pv_bounds = (min(req.pv_min, req.pv_max), max(req.pv_min, req.pv_max)) if req.enable_pv else (0.0, 0.0)
    wind_bounds = (min(req.wind_min, req.wind_max), max(req.wind_min, req.wind_max)) if req.enable_wind else (0.0, 0.0)
    bat_bounds = (min(req.battery_min, req.battery_max), max(req.battery_min, req.battery_max)) if req.enable_battery else (0.0, 0.0)
    diesel_bounds = (min(req.diesel_min, req.diesel_max), max(req.diesel_min, req.diesel_max)) if req.enable_diesel else (0.0, 0.0)

    job_id = uuid.uuid4().hex[:12]
    job_state: Dict[str, Any] = {
        "job_id": job_id,
        "status": "queued",
        "progress_pct": 0.0,
        "current_generation": 0,
        "total_generations": int(num_gens),
        "sol_per_pop": int(sol_pop),
        "best_lcoe": None,
        "convergence_history": [],
        "logs": [f"Job {job_id} queued ({num_gens} generations × {sol_pop} population)..."],
        "started_at": time.perf_counter(),
        "elapsed_sec": 0.0,
        "result": None,
        "error": None,
    }
    _put_bounded(_OPTIMIZATION_JOBS, job_id, job_state)

    def _run_job():
        t0 = time.perf_counter()
        try:
            with _STORE_LOCK:
                job_state["status"] = "running"
                job_state["logs"].append("Loading meteorological & community load profiles (8,760h)...")

            weather_df, w_source, filename = _resolve_weather_df(
                latitude=req.latitude,
                longitude=req.longitude,
                year=req.year,
                weather_source=req.weather_source,
                weather_id=req.weather_id,
            )
            load_df, l_source = _resolve_load_df(
                households=req.households,
                school_preset=req.school_preset,
                clinic_preset=req.clinic_preset,
                year=req.year,
                weather_index=weather_df.index,
                load_id=req.load_id,
            )

            with _STORE_LOCK:
                job_state["progress_pct"] = 5.0
                job_state["logs"].append(
                    f"Profiles ready (weather={w_source}, annual demand={load_df.iloc[:, -1].sum():,.0f} kWh). Starting GA..."
                )

            sys_cfg_base = {
                "pv_derating_factor": 0.82,
                "pv_temp_coeff": -0.004,
                "pv_noct": 45.0,
                "battery_efficiency_charge": 0.96,
                "battery_efficiency_discharge": 0.96,
                "battery_min_soc": 0.2,
                "battery_max_soc": 1.0,
                "battery_initial_soc": 0.5,
                "diesel_min_load_fraction": 0.3,
                **(req.system_config or {}),
            }

            optimizer = GAOptimizer(
                weather_df=weather_df,
                load_df=load_df,
                cost_params={**DEFAULT_COST_PARAMS, **(req.cost_params or {})},
                system_config_base=sys_cfg_base,
                lolp_max=req.lolp_max,
                pv_bounds=pv_bounds,
                wind_bounds=wind_bounds,
                battery_bounds=bat_bounds,
                diesel_bounds=diesel_bounds,
                num_generations=int(num_gens),
                sol_per_pop=int(sol_pop),
                use_fallback_ga=req.use_fallback_ga,
            )

            def _on_progress(gen: int, total: int, best_fit: float, best_lcoe_val: float):
                pct = 5.0 + 90.0 * (gen / max(1, total))
                lcoe_clean = None if (math.isnan(best_lcoe_val) or math.isinf(best_lcoe_val)) else round(best_lcoe_val, 4)
                with _STORE_LOCK:
                    job_state["current_generation"] = gen
                    job_state["progress_pct"] = round(min(95.0, pct), 1)
                    job_state["best_lcoe"] = lcoe_clean
                    job_state["convergence_history"].append(round(best_fit, 6))
                    job_state["elapsed_sec"] = round(time.perf_counter() - t0, 2)
                    lcoe_str = f"${lcoe_clean:.4f}/kWh" if lcoe_clean is not None else "penalized"
                    job_state["logs"].append(
                        f"Gen {gen:02d}/{total:02d} — Best Fitness: {best_fit:.4f} (Est. LCOE: {lcoe_str})"
                    )
                    if len(job_state["logs"]) > 80:
                        job_state["logs"] = job_state["logs"][-80:]

            opt_res = optimizer.optimize(progress_callback=_on_progress)
            best = opt_res["best_configuration"]

            metadata = {
                "project_name": req.project_name,
                "site_name": req.site_name,
                "latitude": req.latitude,
                "longitude": req.longitude,
                "year": req.year,
                "households": req.households,
                "school_preset": req.school_preset,
                "clinic_preset": req.clinic_preset,
                "weather_source": w_source,
                "load_source": l_source,
                "weather_filename": filename,
                "lolp_max": req.lolp_max,
            }

            packaged = _evaluate_and_package_simulation(
                weather_df=weather_df,
                load_df=load_df,
                pv_capacity=best["pv_capacity"],
                wind_capacity=best["wind_capacity"],
                battery_capacity=best["battery_capacity"],
                diesel_capacity=best["diesel_capacity"],
                cost_params=req.cost_params,
                system_config=sys_cfg_base,
                metadata=metadata,
                optimization_method=f"GA ({opt_res.get('optimization_method', 'ga')})",
                convergence_history=[float(x) for x in opt_res.get("convergence_history", [])],
            )

            elapsed = round(time.perf_counter() - t0, 2)
            with _STORE_LOCK:
                job_state["status"] = "completed"
                job_state["progress_pct"] = 100.0
                job_state["current_generation"] = int(num_gens)
                job_state["best_lcoe"] = round(float(packaged["metrics"]["lcoe"]), 4)
                job_state["elapsed_sec"] = elapsed
                job_state["result"] = packaged
                job_state["logs"].append(
                    f"Completed in {elapsed:.2f}s — Optimal LCOE: ${packaged['metrics']['lcoe']:.4f}/kWh | "
                    f"RF: {packaged['metrics']['renewable_fraction']*100:.1f}% | LOLP: {packaged['metrics']['lolp']*100:.2f}%"
                )
        except Exception as e:
            logger.exception(f"Optimization job {job_id} failed")
            with _STORE_LOCK:
                job_state["status"] = "failed"
                job_state["error"] = str(e)
                job_state["elapsed_sec"] = round(time.perf_counter() - t0, 2)
                job_state["logs"].append(f"ERROR: {e}")

    thread = threading.Thread(target=_run_job, daemon=True)
    thread.start()
    return {"job_id": job_id, "status": "queued", "total_generations": int(num_gens)}


@app.get("/api/jobs/{job_id}")
def api_job_status(job_id: str):
    job = _get_bounded(_OPTIMIZATION_JOBS, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    with _STORE_LOCK:
        snap = {
            "job_id": job["job_id"],
            "status": job["status"],
            "progress_pct": job["progress_pct"],
            "current_generation": job["current_generation"],
            "total_generations": job["total_generations"],
            "sol_per_pop": job["sol_per_pop"],
            "best_lcoe": job["best_lcoe"],
            "convergence_history": list(job["convergence_history"]),
            "logs": list(job["logs"]),
            "elapsed_sec": job["elapsed_sec"] if job["status"] in ("completed", "failed") else round(time.perf_counter() - job["started_at"], 2),
            "result": job["result"],
            "error": job["error"],
        }
    return _clean_json_value(snap)


@app.post("/api/report")
def api_report(req: ReportRequest):
    run_entry = _get_bounded(_SIMULATION_RUNS, req.run_id) if req.run_id else None

    if run_entry is None and req.fallback_sim is not None:
        # Re-run simulation transparently if caller passed fallback_sim (e.g. after server restart)
        packaged = api_simulate_manual(req.fallback_sim)
        run_entry = _get_bounded(_SIMULATION_RUNS, packaged["run_id"])

    if run_entry is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation run not found. Please run a simulation or optimization first.",
        )

    lang = (req.language or "fr").lower().strip()
    if lang not in ("fr", "en", "ar"):
        lang = "fr"

    meta = dict(run_entry["metadata"])
    if req.project_name:
        meta["project_name"] = req.project_name
    if req.site_name:
        meta["site_name"] = req.site_name

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, f"HRES_Report_{lang.upper()}.html")
            generate_engineering_report(
                hourly_df=run_entry["hourly_df"],
                results=run_entry["results"],
                output_path=out_path,
                metadata=meta,
                cost_params=run_entry["cost_params"],
                language=lang,
                sample_week_start_day=req.sample_week_start_day,
            )
            with open(out_path, "r", encoding="utf-8") as f:
                html_content = f.read()

        headers = {}
        if req.download:
            stamp = datetime.now().strftime("%Y%m%d_%H%M")
            headers["Content-Disposition"] = f'attachment; filename="HRES_Report_{lang.upper()}_{stamp}.html"'
        return HTMLResponse(content=html_content, headers=headers)
    except Exception as e:
        logger.exception("Failed to generate engineering report")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Launch the HRES Optimizer Web Application.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"), help="Bind host (default: HOST env or 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")), help="Bind port (default: PORT env or 8000)")
    parser.add_argument("--open", action="store_true", help="Open default browser automatically")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    logger.info(f"Starting HRES Optimizer Web Application at {url}")

    if args.open:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
