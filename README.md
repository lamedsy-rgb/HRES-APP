# HRES Optimizer - rural microgrid sizing tool

A modern, interactive desktop application built in CustomTkinter (Python) to design and size Hybrid Renewable Energy Systems (HRES) for remote, off-grid rural communities.

The software balances electricity demand with combinations of Solar PV, Wind turbines, Battery storage (BESS), and backup Diesel generators. It uses state-of-the-art physics models and a genetic algorithm to determine the optimal system architecture that minimizes both Net Present Cost (NPC) and Levelized Cost of Energy (LCOE) while satisfying reliability constraints.

---

## Key Features

- **Interactive Map Picker & NASA API**: Click anywhere on the map of Senegal/West Africa to automatically pull hourly historical solar and weather data for a full year (8760 hours) via the NASA POWER API.
- **Synthetic Load Profile Generator**: Generates realistic diurnal village load curves based on households count, school size (daytime load), and health clinic size (continuous 24/7 cold-chain load).
- **Advanced State Simulation**: Simulates the system operation hour-by-hour for a full year (8760 hours) to balance renewable supply, charge/discharge batteries, operate the diesel generator, and track battery State of Health (SOH) degradation.
- **Genetic Algorithm Optimization**: Finds the absolute cheapest sizing configuration using `pygad` (with a custom pure-NumPy genetic optimizer fallback for maximum portability).
- **Interactive Graphs**: View interactive Matplotlib curves of generation, load, battery SOC, and fuel consumption for any selected week of the year.
- **Scenario Management**: Save multiple sizing runs (e.g., Solar-only vs. Wind-only vs. Hybrid) and compare their financial and technical performance side-by-side.
- **Multi-language**: Fully localized in French, English, and Arabic.
- **Interactive Step-by-Step Tutorial**: Walkthrough tour upon first launch to guide new users through the application features and key technical terms (LOLP, LCOE, NPC, SOH).

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Pip (Python Package Manager)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Application in Development Mode
```bash
python main.py
```

### Run Unit Tests
```bash
python -m unittest discover -s tests
```

---

## Building Standalone Executable

If you want to package the application into a standalone Windows executable (which will be generated in `dist/HRES_Optimizer/HRES_Optimizer.exe`), run:
```bash
python build.py
```

---

## Physics & Equations

The technical center under the **Aide & Doc** tab details all mathematical models utilized in this software, including:
- Cell temperature and power output calculations for Solar PV.
- Exponent hub height wind speed shear law and piecewise cubic wind power curves.
- Battery state of charge (SOC) dynamics and throughput capacity fade aging.
- Diesel generator fuel consumption curves and minimum load constraints.
