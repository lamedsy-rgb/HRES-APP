import os
import sys
import json
import time
import math
import logging
import threading
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import messagebox as mb
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import customtkinter as ctk

# Add project root to sys.path to allow absolute imports when running directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui.components import PlotCanvas, LabeledSlider, LabeledEntry
from data_handlers.weather_api import NASAWeatherDataHandler
from data_handlers.load_generator import generate_synthetic_load
from simulation.engine import run_simulation
from optimization.ga_optimizer import GAOptimizer
from optimization.financials import DEFAULT_COST_PARAMS, calculate_lcoe
from tkintermapview import TkinterMapView
from gui.translations import TRANSLATIONS

# Configure logging to write to standard streams and also intercept it for GUI console
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TextboxHandler(logging.Handler):
    """Custom logging handler to redirect logs to a CTkTextbox in real-time."""
    def __init__(self, textbox):
        super().__init__()
        self.textbox = textbox

    def emit(self, record):
        msg = self.format(record)
        def append():
            try:
                self.textbox.configure(state="normal")
                self.textbox.insert(tk.END, msg + "\n")
                self.textbox.see(tk.END)
                self.textbox.configure(state="disabled")
            except Exception:
                pass
        self.textbox.after(0, append)


class Application(ctk.CTk):
    """
    Main HRES Optimization desktop application.
    Features modern dark/light styling, background thread execution, NASA API queries,
    real-time optimization updates, interactive plots, and persistent scenario comparison.
    """
    def __init__(self):
        super().__init__()
        
        # Localization state (default French)
        self.current_language = "fr"
        self.current_tab_name = "Données d'Entrée"
        
        # Window configuration
        self.title(self.get_text("title"))
        self.geometry("1300x850")
        self.minimum_size = (1100, 750)
        

        # Color theme and appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Resizable paned windows registry
        self._paned_windows = []
        
        # Data and state variables
        self.weather_df = None
        self.load_df = None
        self.hourly_df = None
        self.results = None
        self.saved_scenarios = []
        self.scenarios_file = os.path.join(project_root, "saved_scenarios.json")
        
        # Load saved scenarios
        self.load_scenarios()
        
        # Generate initial synthetic data and default run on startup so the app is instantly interactive
        self.initialize_default_data()
        
        # Setup GUI Grid Layout (Row 0 for Top Bar, Row 1 for Tab Content)
        self.grid_rowconfigure(0, weight=0) # Top Bar
        self.grid_rowconfigure(1, weight=1) # Main Content
        self.grid_columnconfigure(0, weight=1)
        
        # Build components
        self.create_top_bar()
        self.create_main_container()
        
        # Intercept root logger to direct logs to the optimization console
        self.setup_logging_interceptor()
        
        # Select first tab by default
        self.select_tab(self.current_tab_name)
        
        # Initial call to pre-vis plot
        self.update_previs_plot()
        
        # Check first time tutorial launch
        self.after(500, self.prompt_first_time_tutorial)
        
    def load_scenarios(self):
        """Loads saved scenarios from a local JSON file."""
        if os.path.exists(self.scenarios_file):
            try:
                with open(self.scenarios_file, "r", encoding="utf-8") as f:
                    self.saved_scenarios = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load saved scenarios: {e}")
                self.saved_scenarios = []
                
    def save_scenarios_to_file(self):
        """Saves current scenarios to a local JSON file."""
        try:
            with open(self.scenarios_file, "w", encoding="utf-8") as f:
                json.dump(self.saved_scenarios, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save scenarios: {e}")

    def initialize_default_data(self):
        """Initializes weather, load, and simulation results with offline synthetic defaults."""
        try:
            logger.info("Génération de données par défaut au démarrage...")
            # Default location: Senegal (14.5° N, -16.2° W)
            weather_handler = NASAWeatherDataHandler()
            self.weather_df = weather_handler.generate_synthetic_weather(lat=14.5, year=2023)
            
            # Default village: 50 households, medium school, medium clinic
            self.load_df = generate_synthetic_load(
                households=50,
                school_preset="medium",
                clinic_preset="medium",
                year=2023
            )
            
            # Run default simulation with realistic sizes to immediately populate graphs
            default_config = {
                "pv_capacity": 45.0,
                "wind_capacity": 15.0,
                "battery_capacity": 120.0,
                "diesel_capacity": 25.0,
                "pv_derating_factor": 0.82,
                "pv_temp_coeff": -0.004,
                "battery_efficiency_charge": 0.96,
                "battery_efficiency_discharge": 0.96,
                "battery_min_soc": 0.2,
                "battery_max_soc": 1.0,
                "diesel_min_load_fraction": 0.3
            }
            
            self.hourly_df, summary = run_simulation(self.weather_df, self.load_df, default_config)
            
            # Extract default financials
            lcoe, details = calculate_lcoe(
                pv_capacity=45.0,
                wind_capacity=15.0,
                battery_capacity=120.0,
                diesel_capacity=25.0,
                cost_params=DEFAULT_COST_PARAMS,
                annual_diesel_operating_hours=float((self.hourly_df["diesel_output"] > 1e-3).sum()) if "diesel_output" in self.hourly_df.columns else 0.0,
                annual_fuel_consumption=summary["total_fuel_consumption_liters"],
                annual_battery_degradation_fraction=max(0.0, (100.0 - summary["battery_soh_pct"]) / 100.0),
                total_annual_load_kwh=float(self.load_df["total_load"].sum()),
                annual_unmet_load_kwh=summary["total_unmet_load_kwh"]
            )
            
            self.results = {
                "best_configuration": {
                    "pv_capacity": 45.0,
                    "wind_capacity": 15.0,
                    "battery_capacity": 120.0,
                    "diesel_capacity": 25.0
                },
                "metrics": {
                    "lcoe": lcoe,
                    "npc": details["npc"],
                    "capital_cost": details["capital_cost"],
                    "annual_om_cost": details["annual_om_cost"],
                    "annual_fuel_cost": details["annual_fuel_cost"],
                    "unmet_load_kwh": summary["total_unmet_load_kwh"],
                    "lolp": summary["lolp"],
                    "renewable_fraction": summary["renewable_fraction"],
                    "diesel_operating_hours": float((self.hourly_df["diesel_output"] > 1e-3).sum()) if "diesel_output" in self.hourly_df.columns else 0.0,
                    "fuel_consumption_liters": summary["total_fuel_consumption_liters"],
                    "battery_soh_pct": summary["battery_soh_pct"]
                },
                "financial_details": details,
                "optimization_method": "Initialisation"
            }
            logger.info("Données par défaut générées avec succès.")
        except Exception as e:
            logger.critical(f"Erreur lors de l'initialisation par défaut: {e}")

    def create_top_bar(self):
        """Creates the horizontal top navigation and action bar (handles RTL layout)."""
        is_rtl = (getattr(self, "current_language", "fr") == "ar")
        logo_col = 2 if is_rtl else 0
        ctrl_col = 0 if is_rtl else 2
        
        self.top_bar_frame = ctk.CTkFrame(self, height=65, corner_radius=0)
        self.top_bar_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.top_bar_frame.grid_rowconfigure(0, weight=1)
        self.top_bar_frame.grid_columnconfigure(0, weight=0)
        self.top_bar_frame.grid_columnconfigure(1, weight=1) # Expands to center navigation
        self.top_bar_frame.grid_columnconfigure(2, weight=0)
        
        # 1. Logo & Subtitle
        logo_frame = ctk.CTkFrame(self.top_bar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=logo_col, padx=20, pady=5, sticky="ew" if is_rtl else "w")
        
        logo_label = ctk.CTkLabel(
            logo_frame, 
            text=self.get_text("sidebar_logo"), 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#1f538d"
        )
        logo_label.grid(row=0, column=0, sticky="w" if not is_rtl else "e")
        
        subtitle_label = ctk.CTkLabel(
            logo_frame, 
            text=self.get_text("sidebar_subtitle"), 
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#888888"
        )
        subtitle_label.grid(row=1, column=0, sticky="w" if not is_rtl else "e")
        
        # 2. Navigation Tab Segmented Button
        nav_values = [
            self.get_text("tab_inputs"),
            self.get_text("tab_opt"),
            self.get_text("tab_results"),
            self.get_text("tab_scenarios"),
            self.get_text("tab_help")
        ]
        
        self.tab_key_map = {
            "Données d'Entrée": "tab_inputs",
            "Simulation & Optimisation": "tab_opt",
            "Résultats & Graphiques": "tab_results",
            "Comparatif de Scénarios": "tab_scenarios",
            "Aide & Doc": "tab_help",
            "Aide & Documentation": "tab_help"
        }
        
        self.nav_segmented_btn = ctk.CTkSegmentedButton(
            self.top_bar_frame,
            values=nav_values,
            command=self.on_nav_tab_changed,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.nav_segmented_btn.grid(row=0, column=1, padx=20, pady=10, sticky="")
        
        # Set active selection
        active_label = self.get_text(self.tab_key_map.get(self.current_tab_name, "tab_inputs"))
        self.nav_segmented_btn.set(active_label)
        
        # 3. Control Panel (Theme, Language, Sessions)
        ctrl_frame = ctk.CTkFrame(self.top_bar_frame, fg_color="transparent")
        ctrl_frame.grid(row=0, column=ctrl_col, padx=20, pady=5, sticky="ew" if not is_rtl else "e")
        
        # Grid indices inside ctrl_frame (RTL swaps horizontal ordering)
        save_col = 3 if is_rtl else 0
        load_col = 2 if is_rtl else 1
        lang_col = 1 if is_rtl else 2
        theme_col = 0 if is_rtl else 3
        
        self.save_session_btn = ctk.CTkButton(
            ctrl_frame,
            text=self.get_text("save_session"),
            height=30,
            width=100,
            fg_color="#333333",
            hover_color="#444444",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.save_session
        )
        self.save_session_btn.grid(row=0, column=save_col, padx=4, pady=5)
        
        self.load_session_btn = ctk.CTkButton(
            ctrl_frame,
            text=self.get_text("load_session"),
            height=30,
            width=100,
            fg_color="#333333",
            hover_color="#444444",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.load_session
        )
        self.load_session_btn.grid(row=0, column=load_col, padx=4, pady=5)
        
        lang_values = ["Français", "English", "العربية"]
        self.language_optionmenu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=lang_values,
            width=90,
            height=30,
            font=ctk.CTkFont(size=11),
            command=self.change_language
        )
        self.language_optionmenu.grid(row=0, column=lang_col, padx=4, pady=5)
        current_lang_map = {"fr": "Français", "en": "English", "ar": "العربية"}
        self.language_optionmenu.set(current_lang_map.get(getattr(self, "current_language", "fr"), "Français"))
        
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=["Dark", "Light"],
            width=80,
            height=30,
            font=ctk.CTkFont(size=11),
            command=self.change_appearance_mode
        )
        self.appearance_mode_optionemenu.grid(row=0, column=theme_col, padx=4, pady=5)
        self.appearance_mode_optionemenu.set(ctk.get_appearance_mode().capitalize())

    def on_nav_tab_changed(self, value):
        """Callback triggered when the segmented navigation button value changes."""
        target_name = "Données d'Entrée"
        for name, key in self.tab_key_map.items():
            if value == self.get_text(key):
                target_name = name
                break
        self.select_tab(target_name)

    def change_language(self, language_str: str):
        """Callback triggered when the language OptionMenu is modified."""
        lang_map = {"Français": "fr", "English": "en", "العربية": "ar"}
        target_lang = lang_map.get(language_str, "fr")
        if target_lang != getattr(self, "current_language", "fr"):
            self.current_language = target_lang
            self.title(self.get_text("title"))
            self.rebuild_ui()
        
    def change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)
        self.after(100, self.update_pane_colors)
        self.after(200, self.refresh_all_plots)

    def get_text(self, key):
        """Helper to fetch translated text for current language."""
        lang = getattr(self, "current_language", "fr")
        return TRANSLATIONS[lang].get(key, key)

    def get_anchor(self):
        """Dynamic text anchor helper: returns 'e' for Arabic, 'w' for others."""
        return "e" if getattr(self, "current_language", "fr") == "ar" else "w"

    def get_sticky(self):
        """Dynamic layout sticky helper: returns 'ne' for Arabic, 'nw' for others."""
        return "ne" if getattr(self, "current_language", "fr") == "ar" else "nw"

    def rebuild_ui(self):
        """Rebuilds top bar and tabs, preserving variables and state inputs."""
        # 1. Fetch current UI state
        saved_inputs = self.get_current_inputs_state()
        
        # 2. Destroy current widgets
        if hasattr(self, "top_bar_frame"):
            self.top_bar_frame.destroy()
        if hasattr(self, "tab_frames"):
            for frame in self.tab_frames.values():
                frame.destroy()
        
        # Reset paned windows registry
        self._paned_windows = []
        
        # 3. Setup horizontal Grid Layout
        self.grid_rowconfigure(0, weight=0) # Top Bar
        self.grid_rowconfigure(1, weight=1) # Main Content
        self.grid_columnconfigure(0, weight=1)
        
        # 4. Re-create components
        self.create_top_bar()
        self.create_main_container()
        
        # 5. Restore inputs
        self.restore_inputs_state(saved_inputs)
        
        # 6. Re-select current tab and reload plots
        self.select_tab(self.current_tab_name)
        self.refresh_all_plots()

    def get_current_inputs_state(self):
        """Collects all UI input widget values to restore on language changes or session loading."""
        state = {}
        # Tab 1
        try: state["input_segment"] = self.input_segmented_btn.get()
        except: pass
        try: state["previs_segment"] = self.previs_segmented_btn.get()
        except: pass
        try: state["households"] = self.households_slider.get()
        except: pass
        try: state["school"] = self.school_preset.get()
        except: pass
        try: state["clinic"] = self.clinic_preset.get()
        except: pass
        try: state["pv_capex"] = self.pv_capex_entry.get()
        except: pass
        try: state["wind_capex"] = self.wind_capex_entry.get()
        except: pass
        try: state["battery_capex"] = self.battery_capex_entry.get()
        except: pass
        try: state["diesel_capex"] = self.diesel_capex_entry.get()
        except: pass
        try: state["fuel_price"] = self.fuel_price_entry.get()
        except: pass
        try: state["lat"] = self.lat_entry.get()
        except: pass
        try: state["lon"] = self.lon_entry.get()
        except: pass
        try: state["year"] = self.year_entry.get()
        except: pass
        # Tab 2
        try: state["lolp_max"] = self.lolp_max_slider.get()
        except: pass
        try: state["generations"] = self.generations_slider.get()
        except: pass
        try: state["pop_size"] = self.pop_size_slider.get()
        except: pass
        try: state["force_numpy"] = self.force_numpy_checkbox.get()
        except: pass
        try: state["enable_pv"] = self.enable_pv_cb.get()
        except: pass
        try: state["enable_wind"] = self.enable_wind_cb.get()
        except: pass
        try: state["enable_bat"] = self.enable_bat_cb.get()
        except: pass
        try: state["enable_diesel"] = self.enable_diesel_cb.get()
        except: pass
        # Tab 3
        try: state["show_pv"] = self.show_curve_pv.get()
        except: pass
        try: state["show_wind"] = self.show_curve_wind.get()
        except: pass
        try: state["show_diesel"] = self.show_curve_diesel.get()
        except: pass
        try: state["show_load"] = self.show_curve_load.get()
        except: pass
        try: state["show_soc"] = self.show_curve_soc.get()
        except: pass
        try: state["start_day"] = self.start_day_slider.get()
        except: pass
        try: state["duration"] = self.duration_slider.get()
        except: pass
        # Tab 4
        try: state["scenario_name"] = self.scenario_name_entry.get()
        except: pass
        return state

    def restore_inputs_state(self, state):
        """Restores collected UI values back to the recreated widget instances."""
        # Tab 1 segment and parameters
        try:
            if "input_segment" in state:
                self.input_segmented_btn.set(state["input_segment"])
                self.on_input_segment_changed(state["input_segment"])
        except: pass
        try:
            if "previs_segment" in state:
                self.previs_segmented_btn.set(state["previs_segment"])
        except: pass
        try:
            if "households" in state: self.households_slider.set(state["households"])
        except: pass
        try:
            if "school" in state: self.school_preset.set(state["school"])
        except: pass
        try:
            if "clinic" in state: self.clinic_preset.set(state["clinic"])
        except: pass
        # Tab 1 financial entries
        try:
            if "pv_capex" in state: self.pv_capex_entry.set(state["pv_capex"])
        except: pass
        try:
            if "wind_capex" in state: self.wind_capex_entry.set(state["wind_capex"])
        except: pass
        try:
            if "battery_capex" in state: self.battery_capex_entry.set(state["battery_capex"])
        except: pass
        try:
            if "diesel_capex" in state: self.diesel_capex_entry.set(state["diesel_capex"])
        except: pass
        try:
            if "fuel_price" in state: self.fuel_price_entry.set(state["fuel_price"])
        except: pass
        # Geolocation
        try:
            if "lat" in state: self.lat_entry.set(state["lat"])
        except: pass
        try:
            if "lon" in state: self.lon_entry.set(state["lon"])
        except: pass
        try:
            if "year" in state: self.year_entry.set(state["year"])
        except: pass
        # Tab 2 parameters
        try:
            if "lolp_max" in state: self.lolp_max_slider.set(state["lolp_max"])
        except: pass
        try:
            if "generations" in state: self.generations_slider.set(state["generations"])
        except: pass
        try:
            if "pop_size" in state: self.pop_size_slider.set(state["pop_size"])
        except: pass
        try:
            if "force_numpy" in state:
                if state["force_numpy"]: self.force_numpy_checkbox.select()
                else: self.force_numpy_checkbox.deselect()
        except: pass
        try:
            if "enable_pv" in state:
                self.enable_pv_cb.select() if state["enable_pv"] else self.enable_pv_cb.deselect()
        except: pass
        try:
            if "enable_wind" in state:
                self.enable_wind_cb.select() if state["enable_wind"] else self.enable_wind_cb.deselect()
        except: pass
        try:
            if "enable_bat" in state:
                self.enable_bat_cb.select() if state["enable_bat"] else self.enable_bat_cb.deselect()
        except: pass
        try:
            if "enable_diesel" in state:
                self.enable_diesel_cb.select() if state["enable_diesel"] else self.enable_diesel_cb.deselect()
        except: pass
        # Tab 3 curves
        try:
            if "show_pv" in state: self.show_curve_pv.set(state["show_pv"])
        except: pass
        try:
            if "show_wind" in state: self.show_curve_wind.set(state["show_wind"])
        except: pass
        try:
            if "show_diesel" in state: self.show_curve_diesel.set(state["show_diesel"])
        except: pass
        try:
            if "show_load" in state: self.show_curve_load.set(state["show_load"])
        except: pass
        try:
            if "show_soc" in state: self.show_curve_soc.set(state["show_soc"])
        except: pass
        try:
            if "start_day" in state: self.start_day_slider.set(state["start_day"])
        except: pass
        try:
            if "duration" in state: self.duration_slider.set(state["duration"])
        except: pass
        # Tab 4
        try:
            if "scenario_name" in state: self.scenario_name_entry.set(state["scenario_name"])
        except: pass

    def serialize_df(self, df):
        """Converts a pandas DataFrame with DatetimeIndex into a JSON-serializable split format dict."""
        if df is None:
            return None
        d = df.to_dict(orient="split")
        # Convert Timestamps to ISO format strings to make them JSON-serializable
        d["index"] = [t.isoformat() if hasattr(t, "isoformat") else str(t) for t in d["index"]]
        return d

    def deserialize_df(self, d):
        """Reconstructs a pandas DataFrame from a split format dict and restores DatetimeIndex."""
        if d is None:
            return None
        df = pd.DataFrame(d["data"], index=d["index"], columns=d["columns"])
        df.index = pd.to_datetime(df.index)
        return df

    def save_session(self):
        """Serializes and saves the active weather data, inputs, scenarios, and results to an external file."""
        file_path = fd.asksaveasfilename(
            defaultextension=".hres",
            filetypes=[("HRES Session Files", "*.hres"), ("All Files", "*.*")],
            title=self.get_text("save_session_title")
        )
        if not file_path:
            return
            
        try:
            session_data = {
                "language": self.current_language,
                "inputs": self.get_current_inputs_state(),
                "results": self.results,
                "saved_scenarios": self.saved_scenarios,
                "weather_df": self.serialize_df(self.weather_df),
                "load_df": self.serialize_df(self.load_df),
                "hourly_df": self.serialize_df(self.hourly_df),
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
            mb.showinfo(self.get_text("success"), self.get_text("session_saved_msg"))
            logger.info(f"Session saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            mb.showerror(self.get_text("error"), f"{self.get_text('session_save_error')}\n{e}")

    def load_session(self):
        """Deserializes and restores meteorological data, inputs, scenarios, and results from a file."""
        file_path = fd.askopenfilename(
            filetypes=[("HRES Session Files", "*.hres"), ("All Files", "*.*")],
            title=self.get_text("load_session_title")
        )
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                
            # Reconstruct DataFrames using helper
            self.weather_df = self.deserialize_df(session_data.get("weather_df"))
            self.load_df = self.deserialize_df(session_data.get("load_df"))
            self.hourly_df = self.deserialize_df(session_data.get("hourly_df"))
            
            # Sync index align
            if self.load_df is not None and self.weather_df is not None:
                self.load_df.index = self.weather_df.index
                
            # Restore state variables
            self.results = session_data.get("results")
            self.saved_scenarios = session_data.get("saved_scenarios", [])
            self.current_language = session_data.get("language", self.current_language)
            self.title(self.get_text("title"))
            
            # Sync persistent local json scenarios file
            self.save_scenarios_to_file()
            
            # Restore inputs configuration
            inputs = session_data.get("inputs", {})
            
            # Rebuild and reload the interface
            self.rebuild_ui()
            self.restore_inputs_state(inputs)
            
            # Update plots
            self.refresh_all_plots()
            
            mb.showinfo(self.get_text("success"), self.get_text("session_loaded_msg"))
            logger.info(f"Session loaded from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            mb.showerror(self.get_text("error"), f"{self.get_text('session_load_error')}\n{e}")
        
    def get_pane_bg(self):
        mode = ctk.get_appearance_mode().lower()
        return "#242424" if mode == "dark" else "#ebebeb"

    def update_pane_colors(self):
        bg = self.get_pane_bg()
        for pane in getattr(self, "_paned_windows", []):
            try:
                pane.configure(bg=bg)
            except Exception:
                pass

    def create_paned_window(self, parent, orient, **kwargs):
        bg = self.get_pane_bg()
        sash_cur = "size_we" if orient == tk.HORIZONTAL else "size_ns"
        pane = tk.PanedWindow(
            parent, 
            orient=orient, 
            bd=0, 
            sashwidth=6, 
            sashpad=2, 
            bg=bg, 
            sashcursor=sash_cur,
            opaqueresize=False,
            **kwargs
        )
        pane.bind("<Motion>", self.on_pane_motion)
        pane.bind("<Leave>", self.on_pane_leave)
        if not hasattr(self, "_paned_windows"):
            self._paned_windows = []
        self._paned_windows.append(pane)
        return pane

    def on_pane_motion(self, event):
        pane = event.widget
        try:
            identity = pane.identify(event.x, event.y)
            if identity and "sash" in identity:
                mode = ctk.get_appearance_mode().lower()
                active_bg = "#444444" if mode == "dark" else "#cccccc"
                pane.configure(bg=active_bg)
            else:
                mode = ctk.get_appearance_mode().lower()
                normal_bg = "#242424" if mode == "dark" else "#ebebeb"
                pane.configure(bg=normal_bg)
        except Exception:
            pass

    def on_pane_leave(self, event):
        pane = event.widget
        try:
            mode = ctk.get_appearance_mode().lower()
            normal_bg = "#242424" if mode == "dark" else "#ebebeb"
            pane.configure(bg=normal_bg)
        except Exception:
            pass
        
    def select_tab(self, tab_name: str):
        """Raises selected tab frame and updates top bar navigation highlight state."""
        self.current_tab_name = tab_name
        
        # Sync the segmented button selection if it doesn't match
        if hasattr(self, "nav_segmented_btn") and hasattr(self, "tab_key_map"):
            active_label = self.get_text(self.tab_key_map.get(tab_name, "tab_inputs"))
            if self.nav_segmented_btn.get() != active_label:
                self.nav_segmented_btn.set(active_label)
                
        # Switch frames (always spans row 1, full width)
        for name, frame in self.tab_frames.items():
            if name == tab_name:
                frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
                if hasattr(frame, "on_show"):
                    frame.on_show()
            else:
                frame.grid_forget()

    def create_main_container(self):
        """Creates the container frames for all navigation tabs."""
        self.tab_frames = {
            "Données d'Entrée": self.build_tab_inputs(),
            "Simulation & Optimisation": self.build_tab_optimization(),
            "Résultats & Graphiques": self.build_tab_results(),
            "Comparatif de Scénarios": self.build_tab_scenario_comparison(),
            "Aide & Doc": self.build_tab_help()
        }

    # =========================================================================
    # TAB 1: DONNÉES D'ENTRÉE (Input Ingestion)
    # =========================================================================
    def build_tab_inputs(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=0) # Title
        frame.grid_rowconfigure(1, weight=1) # Content Split Area
        frame.grid_columnconfigure(0, weight=1)
        
        # Tab title
        title = ctk.CTkLabel(
            frame, 
            text=self.get_text("tab1_title"), 
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor=self.get_anchor()
        )
        title.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        
        # Horizontal Split Container using tk.PanedWindow
        split_container = self.create_paned_window(frame, tk.HORIZONTAL)
        split_container.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")
        
        # === LEFT COLUMN ===
        left_col = ctk.CTkFrame(split_container, fg_color="transparent")
        left_col.grid_rowconfigure(0, weight=0) # Segmented control
        left_col.grid_rowconfigure(1, weight=1) # Input Container
        left_col.grid_columnconfigure(0, weight=1)
        
        # Segmented Control at the top
        seg_values = [
            self.get_text("seg_manual"),
            self.get_text("seg_file"),
            self.get_text("seg_geoloc")
        ]
        self.input_segmented_btn = ctk.CTkSegmentedButton(
            left_col,
            values=seg_values,
            command=self.on_input_segment_changed,
            height=35
        )
        self.input_segmented_btn.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="ew")
        self.input_segmented_btn.set(self.get_text("seg_manual"))
        
        # Input container CTkFrame
        self.input_container = ctk.CTkFrame(left_col)
        self.input_container.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.input_container.grid_rowconfigure(0, weight=1)
        self.input_container.grid_columnconfigure(0, weight=1)
        
        # Sub-frames for each ingestion method (parent is now self.input_container)
        self.input_sub_frames = {}
        self.input_sub_frames["manual"] = self.build_manual_input_frame(self.input_container)
        self.input_sub_frames["file"] = self.build_file_import_frame(self.input_container)
        self.input_sub_frames["geoloc"] = self.build_geoloc_frame(self.input_container)
        
        # Display default sub-frame inside the container
        self.input_sub_frames["manual"].grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        
        # === RIGHT COLUMN ===
        # Right column is a vertical PanedWindow
        right_col = self.create_paned_window(split_container, tk.VERTICAL)
        
        # Add columns to horizontal split (RTL swaps horizontal ordering)
        is_rtl = (getattr(self, "current_language", "fr") == "ar")
        if is_rtl:
            split_container.add(right_col)
            split_container.add(left_col, width=420)
        else:
            split_container.add(left_col, width=420)
            split_container.add(right_col)
        
        # Map widget card container
        map_card = ctk.CTkFrame(right_col, corner_radius=12)
        right_col.add(map_card, height=280)
        map_card.grid_rowconfigure(0, weight=1)
        map_card.grid_columnconfigure(0, weight=1)
        
        # Map widget
        self.map_widget = TkinterMapView(map_card, corner_radius=12)
        self.map_widget.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.map_widget.set_position(14.5, -16.2) # Center on Senegal
        self.map_widget.set_zoom(6)
        self.map_marker = self.map_widget.set_marker(14.5, -16.2, text="Position sélectionnée")
        self.map_widget.add_left_click_map_command(self.on_map_click)
        
        # Pre-vis widget container
        previs_frame = ctk.CTkFrame(right_col, corner_radius=12)
        right_col.add(previs_frame, height=350)
        previs_frame.grid_rowconfigure(0, weight=0) # Segmented control
        previs_frame.grid_rowconfigure(1, weight=1) # PlotCanvas
        previs_frame.grid_columnconfigure(0, weight=1)
        
        # Pre-vis segmented control
        previs_seg_values = [
            self.get_text("previs_load"),
            self.get_text("previs_solar"),
            self.get_text("previs_wind")
        ]
        self.previs_segmented_btn = ctk.CTkSegmentedButton(
            previs_frame,
            values=previs_seg_values,
            command=self.update_previs_plot,
            height=30
        )
        self.previs_segmented_btn.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        self.previs_segmented_btn.set(self.get_text("previs_load"))
        
        # previs PlotCanvas widget
        self.previs_canvas = PlotCanvas(previs_frame, dpi=80)
        self.previs_canvas.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        return frame
    
    def on_input_segment_changed(self, value):
        for f in self.input_sub_frames.values():
            f.grid_forget()
            
        if value == self.get_text("seg_manual"):
            self.input_sub_frames["manual"].grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        elif value == self.get_text("seg_file"):
            self.input_sub_frames["file"].grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        elif value == self.get_text("seg_geoloc"):
            self.input_sub_frames["geoloc"].grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

    def on_map_click(self, coords):
        # Ignore clicks on the map's default zoom in/out buttons to prevent resetting marker position
        if hasattr(self, "map_widget") and hasattr(self.map_widget, "last_mouse_down_position"):
            mx, my = self.map_widget.last_mouse_down_position
            if 10 <= mx <= 60 and 10 <= my <= 100:
                logger.info(f"Map click ignored on zoom controls: x={mx}, y={my}")
                return
                
        lat, lon = coords
        if hasattr(self, "map_marker") and self.map_marker is not None:
            try:
                self.map_marker.delete()
            except Exception:
                pass
        self.map_marker = self.map_widget.set_marker(lat, lon, text="Position sélectionnée")
        self.lat_entry.set(round(lat, 4))
        self.lon_entry.set(round(lon, 4))
        self.update_previs_plot()

    def get_preset_value(self, val_str):
        """Maps localized optionmenu options to standard internal keys."""
        for lang in ["fr", "en", "ar"]:
            for key in ["none", "small", "medium", "large"]:
                if val_str == TRANSLATIONS[lang][key]:
                    return key
        return "none"

    def get_community_preset_value(self, val_str):
        """Maps localized community options to standard preset keys."""
        for lang in ["fr", "en", "ar"]:
            for key in ["preset_custom", "preset_hamlet", "preset_village", "preset_center"]:
                if val_str == TRANSLATIONS[lang][key]:
                    return key
        return "preset_custom"

    def apply_community_preset(self, value):
        preset_key = self.get_community_preset_value(value)
        if preset_key == "preset_custom":
            return
        self._updating_preset = True
        try:
            if preset_key == "preset_hamlet":
                self.households_slider.set(15)
                self.school_preset.set(self.get_text("none"))
                self.clinic_preset.set(self.get_text("none"))
            elif preset_key == "preset_village":
                self.households_slider.set(60)
                self.school_preset.set(self.get_text("medium"))
                self.clinic_preset.set(self.get_text("small"))
            elif preset_key == "preset_center":
                self.households_slider.set(250)
                self.school_preset.set(self.get_text("large"))
                self.clinic_preset.set(self.get_text("large"))
        finally:
            self._updating_preset = False
        self.update_previs_plot()

    def on_manual_input_change(self, _=None):
        if hasattr(self, "community_preset"):
            if not getattr(self, "_updating_preset", False):
                self.community_preset.set(self.get_text("preset_custom"))
        self.update_previs_plot()

    def update_previs_plot(self, _=None):
        tab = self.previs_segmented_btn.get()
        fig = self.previs_canvas.fig
        fig.clear()
        ax = fig.add_subplot(111)
        
        # Check matching translated tabs
        if tab == self.get_text("previs_load"):
            is_manual_tab = (self.input_segmented_btn.get() == self.get_text("seg_manual"))
            if self.load_df is not None and not is_manual_tab:
                y_values = self.load_df["total_load"].iloc[:168].values
            else:
                households = int(self.households_slider.get())
                school_pr = self.get_preset_value(self.school_preset.get())
                clinic_pr = self.get_preset_value(self.clinic_preset.get())
                
                temp_load_df = generate_synthetic_load(
                    households=households,
                    school_preset=school_pr,
                    clinic_preset=clinic_pr,
                    year=2023
                )
                y_values = temp_load_df["total_load"].iloc[:168].values
                
            x_values = np.arange(168)
            
            ax.plot(x_values, y_values, color="#00e5ff", linewidth=1.5)
            ax.fill_between(x_values, y_values, color="#00e5ff", alpha=0.15)
            ax.set_title(self.get_text("previs_load_title"), fontsize=11, fontweight="bold")
            ax.set_xlabel(self.get_text("hours_of_week"))
            ax.set_ylabel(self.get_text("power_kw"))
            ax.grid(True, linestyle=":", alpha=0.6)
            
        elif tab == self.get_text("previs_solar"):
            df = self.weather_df
            if df is None:
                weather_handler = NASAWeatherDataHandler()
                df = weather_handler.generate_synthetic_weather(lat=14.5, year=2023)
            
            monthly_avg = df.groupby(df.index.month)["solar_irradiance"].mean()
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            ax.bar(months, monthly_avg, color="#ff9800", edgecolor="#e68a00")
            ax.set_title(self.get_text("previs_solar_title"), fontsize=11, fontweight="bold")
            ax.set_ylabel("GHI (kW/m²)")
            ax.set_xlabel(self.get_text("month"))
            ax.grid(True, linestyle=":", alpha=0.6)
            
        elif tab == self.get_text("previs_wind"):
            df = self.weather_df
            if df is None:
                weather_handler = NASAWeatherDataHandler()
                df = weather_handler.generate_synthetic_weather(lat=14.5, year=2023)
            
            monthly_avg = df.groupby(df.index.month)["wind_speed"].mean()
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            ax.bar(months, monthly_avg, color="#00bcd4", edgecolor="#00838f")
            ax.set_title(self.get_text("previs_wind_title"), fontsize=11, fontweight="bold")
            ax.set_ylabel("Wind (m/s)")
            ax.set_xlabel(self.get_text("month"))
            ax.grid(True, linestyle=":", alpha=0.6)
            
        self.previs_canvas.draw()

    def build_manual_input_frame(self, parent):
        frame = ctk.CTkScrollableFrame(parent)
        frame.grid_columnconfigure(0, weight=1)
        
        # LEFT: Village parameters
        village_card = ctk.CTkFrame(frame, corner_radius=12)
        village_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        village_card.grid_columnconfigure(0, weight=1)
        
        v_title = ctk.CTkLabel(village_card, text=self.get_text("community_title"), font=ctk.CTkFont(size=16, weight="bold"), anchor=self.get_anchor())
        v_title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        
        # Preset community selector
        preset_lbl = ctk.CTkLabel(village_card, text=self.get_text("preset_lbl"), anchor=self.get_anchor())
        preset_lbl.grid(row=1, column=0, padx=15, pady=(10, 0), sticky="ew")
        self.community_preset = ctk.CTkOptionMenu(
            village_card,
            values=[
                self.get_text("preset_custom"),
                self.get_text("preset_hamlet"),
                self.get_text("preset_village"),
                self.get_text("preset_center")
            ],
            command=self.apply_community_preset
        )
        self.community_preset.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.community_preset.set(self.get_text("preset_custom"))
        
        # Slider for Households
        self.households_slider = LabeledSlider(
            village_card, 
            self.get_text("households_lbl"), 
            from_=5, 
            to=500, 
            default_value=50, 
            resolution=5, 
            value_suffix="",
            command=self.on_manual_input_change
        )
        self.households_slider.grid(row=3, column=0, padx=15, pady=10, sticky="ew")
        
        school_lbl = ctk.CTkLabel(village_card, text=self.get_text("school_lbl"), anchor=self.get_anchor())
        school_lbl.grid(row=4, column=0, padx=15, pady=(10, 0), sticky="ew")
        
        opt_values = [self.get_text("none"), self.get_text("small"), self.get_text("medium"), self.get_text("large")]
        self.school_preset = ctk.CTkOptionMenu(
            village_card, 
            values=opt_values,
            command=self.on_manual_input_change
        )
        self.school_preset.grid(row=5, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.school_preset.set(self.get_text("medium"))
        
        clinic_lbl = ctk.CTkLabel(village_card, text=self.get_text("clinic_lbl"), anchor=self.get_anchor())
        clinic_lbl.grid(row=6, column=0, padx=15, pady=(10, 0), sticky="ew")
        self.clinic_preset = ctk.CTkOptionMenu(
            village_card, 
            values=opt_values,
            command=self.on_manual_input_change
        )
        self.clinic_preset.grid(row=7, column=0, padx=15, pady=(0, 20), sticky="ew")
        self.clinic_preset.set(self.get_text("medium"))
        
        # RIGHT: Cost parameters
        cost_card = ctk.CTkFrame(frame, corner_radius=12)
        cost_card.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        cost_card.grid_columnconfigure(0, weight=1)
        
        c_title = ctk.CTkLabel(cost_card, text=self.get_text("financial_title"), font=ctk.CTkFont(size=16, weight="bold"), anchor=self.get_anchor())
        c_title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        
        self.pv_capex_entry = LabeledEntry(cost_card, self.get_text("pv_capex"), 1000.0)
        self.pv_capex_entry.grid(row=1, column=0, padx=15, pady=6, sticky="ew")
        
        self.wind_capex_entry = LabeledEntry(cost_card, self.get_text("wind_capex"), 1600.0)
        self.wind_capex_entry.grid(row=2, column=0, padx=15, pady=6, sticky="ew")
        
        self.battery_capex_entry = LabeledEntry(cost_card, self.get_text("bat_capex"), 300.0)
        self.battery_capex_entry.grid(row=3, column=0, padx=15, pady=6, sticky="ew")
        
        self.diesel_capex_entry = LabeledEntry(cost_card, self.get_text("diesel_capex"), 400.0)
        self.diesel_capex_entry.grid(row=4, column=0, padx=15, pady=6, sticky="ew")
        
        self.fuel_price_entry = LabeledEntry(cost_card, self.get_text("fuel_price"), 1.20)
        self.fuel_price_entry.grid(row=5, column=0, padx=15, pady=(6, 15), sticky="ew")
        
        # Bottom Actions
        action_card = ctk.CTkFrame(frame, fg_color="transparent")
        action_card.grid(row=2, column=0, padx=10, pady=20, sticky="ew")
        action_card.grid_columnconfigure(0, weight=1)
        
        self.generate_btn = ctk.CTkButton(
            action_card,
            text=self.get_text("apply_config"),
            height=45,
            font=ctk.CTkFont(weight="bold"),
            command=self.generate_manual_profiles
        )
        self.generate_btn.grid(row=0, column=0, sticky="ew")
        
        self.manual_status_lbl = ctk.CTkLabel(
            action_card,
            text=self.get_text("status_synthetic_ready"),
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray"
        )
        self.manual_status_lbl.grid(row=1, column=0, pady=5)
        
        return frame

    def generate_manual_profiles(self):
        """Generates synthetic hourly profiles in a background thread."""
        self.generate_btn.configure(state="disabled", text=self.get_text("generating"))
        
        def run():
            try:
                households = int(self.households_slider.get())
                
                # Retrieve preset values using localized helper
                school_pr = self.get_preset_value(self.school_preset.get())
                clinic_pr = self.get_preset_value(self.clinic_preset.get())
                
                logger.info(f"Régénération du profil de charge synthétique: Ménages={households}, École={school_pr}, Clinique={clinic_pr}...")
                
                # Generate load
                new_load_df = generate_synthetic_load(
                    households=households,
                    school_preset=school_pr,
                    clinic_preset=clinic_pr,
                    year=2023
                )
                
                # Generate weather synthetically (stays aligned with load year)
                weather_handler = NASAWeatherDataHandler()
                new_weather_df = weather_handler.generate_synthetic_weather(lat=14.5, year=2023)
                
                # Update state safely in GUI thread
                self.after(0, lambda: self.finish_manual_generation(new_weather_df, new_load_df))
            except Exception as e:
                logger.error(f"Failed to generate synthetic profiles: {e}")
                self.after(0, lambda: self.finish_manual_generation(None, None, error=str(e)))
                
        threading.Thread(target=run, daemon=True).start()

    def finish_manual_generation(self, weather_df, load_df, error=None):
        self.generate_btn.configure(state="normal", text=self.get_text("apply_config"))
        if error:
            mb.showerror(self.get_text("error"), f"{error}")
            self.manual_status_lbl.configure(text=self.get_text("error"), text_color="red")
        else:
            self.weather_df = weather_df
            self.load_df = load_df
            logger.info("New profiles loaded successfully in the app.")
            self.manual_status_lbl.configure(text=self.get_text("status_synthetic_updated"), text_color="#2ca02c")
            # Automatically run a quick base simulation using the new data
            self.trigger_quick_base_simulation()
            self.update_previs_plot()

    def build_file_import_frame(self, parent):
        frame = ctk.CTkScrollableFrame(parent)
        frame.grid_columnconfigure(0, weight=1)
        
        # Weather Ingestion
        weather_card = ctk.CTkFrame(frame, corner_radius=12)
        weather_card.grid(row=0, column=0, padx=15, pady=20, sticky="nsew")
        weather_card.grid_columnconfigure(0, weight=1)
        
        w_title = ctk.CTkLabel(weather_card, text=self.get_text("weather_file_title"), font=ctk.CTkFont(size=16, weight="bold"))
        w_title.grid(row=0, column=0, padx=15, pady=(20, 10), sticky="ew")
        
        self.weather_file_lbl = ctk.CTkLabel(
            weather_card, 
            text=self.get_text("import_none"), 
            text_color="gray", 
            wraplength=200
        )
        self.weather_file_lbl.grid(row=1, column=0, padx=15, pady=15)
        
        w_btn = ctk.CTkButton(
            weather_card,
            text=self.get_text("import_btn"),
            command=self.import_weather_file
        )
        w_btn.grid(row=2, column=0, padx=15, pady=(5, 20), sticky="ew")
        
        # Load Ingestion
        load_card = ctk.CTkFrame(frame, corner_radius=12)
        load_card.grid(row=1, column=0, padx=15, pady=20, sticky="nsew")
        load_card.grid_columnconfigure(0, weight=1)
        
        l_title = ctk.CTkLabel(load_card, text=self.get_text("load_file_title"), font=ctk.CTkFont(size=16, weight="bold"))
        l_title.grid(row=0, column=0, padx=15, pady=(20, 10), sticky="ew")
        
        self.load_file_lbl = ctk.CTkLabel(
            load_card, 
            text=self.get_text("import_none"), 
            text_color="gray", 
            wraplength=200
        )
        self.load_file_lbl.grid(row=1, column=0, padx=15, pady=15)
        
        l_btn = ctk.CTkButton(
            load_card,
            text=self.get_text("import_btn"),
            command=self.import_load_file
        )
        l_btn.grid(row=2, column=0, padx=15, pady=(5, 20), sticky="ew")
        
        # File guide
        guide_card = ctk.CTkFrame(frame, corner_radius=12)
        guide_card.grid(row=2, column=0, padx=15, pady=(0, 20), sticky="ew")
        guide_card.grid_columnconfigure(0, weight=1)
        
        guide_title_lbl = ctk.CTkLabel(guide_card, text=self.get_text("format_guide_title"), font=ctk.CTkFont(size=13, weight="bold"), anchor=self.get_anchor())
        guide_title_lbl.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        
        guide_lbl = ctk.CTkLabel(guide_card, text=self.get_text("format_guide_desc"), justify="left", font=ctk.CTkFont(size=12))
        guide_lbl.grid(row=1, column=0, padx=20, pady=(0, 15))
        
        return frame

    def import_weather_file(self):
        filepath = fd.askopenfilename(
            title=self.get_text("weather_file_title"),
            filetypes=[(self.get_text("select_excel_csv"), "*.csv;*.xlsx;*.xls"), ("CSV", "*.csv"), ("Excel", "*.xlsx;*.xls")]
        )
        if not filepath:
            return
            
        try:
            filename = os.path.basename(filepath)
            logger.info(f"Reading weather file: {filename}")
            
            if filepath.endswith(".csv"):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
                
            if len(df) != 8760:
                raise ValueError(f"File must contain exactly 8760 rows (found: {len(df)}).")
                
            # Maps headers
            solar_col, temp_col, wind_col = None, None, None
            for col in df.columns:
                c_low = col.lower()
                if "solar" in c_low or "irrad" in c_low or "ghi" in c_low or "ray" in c_low:
                    solar_col = col
                elif "temp" in c_low or "t2m" in c_low or "celsius" in c_low:
                    temp_col = col
                elif "wind" in c_low or "speed" in c_low or "vent" in c_low:
                    wind_col = col
                    
            if not solar_col or not temp_col or not wind_col:
                missing = []
                if not solar_col: missing.append("solar_irradiance")
                if not temp_col: missing.append("temperature")
                if not wind_col: missing.append("wind_speed")
                raise ValueError(f"Could not identify columns: {', '.join(missing)}.")
                
            new_weather_df = pd.DataFrame({
                "solar_irradiance": df[solar_col].astype(float),
                "temperature": df[temp_col].astype(float),
                "wind_speed": df[wind_col].astype(float)
            })
            
            self.weather_df = new_weather_df
            self.weather_file_lbl.configure(text=f"{filename}\n✓ OK", text_color="#2ca02c")
            logger.info("Weather data loaded successfully.")
            self.trigger_quick_base_simulation()
            self.update_previs_plot()
            
        except Exception as e:
            logger.error(f"Failed to import weather: {e}")
            mb.showerror(self.get_text("error"), f"{e}")

    def import_load_file(self):
        filepath = fd.askopenfilename(
            title=self.get_text("load_file_title"),
            filetypes=[(self.get_text("select_excel_csv"), "*.csv;*.xlsx;*.xls"), ("CSV", "*.csv"), ("Excel", "*.xlsx;*.xls")]
        )
        if not filepath:
            return
            
        try:
            filename = os.path.basename(filepath)
            logger.info(f"Reading load file: {filename}")
            
            if filepath.endswith(".csv"):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
                
            if len(df) != 8760:
                raise ValueError(f"File must contain exactly 8760 rows (found: {len(df)}).")
                
            load_col = None
            for col in df.columns:
                c_low = col.lower()
                if "total_load" in c_low or "load" in c_low or "charge" in c_low or "demand" in c_low or "cons" in c_low:
                    load_col = col
                    break
                    
            if not load_col:
                load_col = df.columns[0]
                logger.warning(f"Load column not detected, using first column: {load_col}")
                
            new_load_df = pd.DataFrame({
                "total_load": df[load_col].astype(float)
            })
            
            if self.weather_df is not None:
                new_load_df.index = self.weather_df.index
                
            self.load_df = new_load_df
            self.load_file_lbl.configure(text=f"{filename}\n✓ OK", text_color="#2ca02c")
            logger.info("Load profile loaded successfully.")
            self.trigger_quick_base_simulation()
            self.update_previs_plot()
            
        except Exception as e:
            logger.error(f"Failed to import load: {e}")
            mb.showerror(self.get_text("error"), f"{e}")

    def build_geoloc_frame(self, parent):
        frame = ctk.CTkScrollableFrame(parent)
        frame.grid_columnconfigure(0, weight=1)
        
        geoloc_card = ctk.CTkFrame(frame, corner_radius=12)
        geoloc_card.grid(row=0, column=0, padx=30, pady=20, sticky="nsew")
        geoloc_card.grid_columnconfigure(0, weight=1)
        
        g_title = ctk.CTkLabel(geoloc_card, text=self.get_text("geoloc_title"), font=ctk.CTkFont(size=16, weight="bold"))
        g_title.grid(row=0, column=0, padx=15, pady=(20, 15), sticky="ew")
        
        self.lat_entry = LabeledEntry(geoloc_card, self.get_text("lat_lbl"), 14.5)
        self.lat_entry.grid(row=1, column=0, padx=15, pady=8, sticky="ew")
        
        self.lon_entry = LabeledEntry(geoloc_card, self.get_text("lon_lbl"), -16.2)
        self.lon_entry.grid(row=2, column=0, padx=15, pady=8, sticky="ew")
        
        self.year_entry = LabeledEntry(geoloc_card, self.get_text("year_lbl"), 2023)
        self.year_entry.grid(row=3, column=0, padx=15, pady=12, sticky="ew")
        
        # Actions
        self.fetch_nasa_btn = ctk.CTkButton(
            geoloc_card,
            text=self.get_text("nasa_btn"),
            height=45,
            font=ctk.CTkFont(weight="bold"),
            command=self.fetch_nasa_weather
        )
        self.fetch_nasa_btn.grid(row=4, column=0, padx=15, pady=(15, 10), sticky="ew")
        
        self.nasa_status_lbl = ctk.CTkLabel(
            geoloc_card,
            text=self.get_text("nasa_status_wait"),
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray"
        )
        self.nasa_status_lbl.grid(row=5, column=0, pady=(0, 20))
        
        return frame

    def fetch_nasa_weather(self):
        """Fetches NASA weather data in a background thread to prevent GUI freezing."""
        self.fetch_nasa_btn.configure(state="disabled", text=self.get_text("nasa_status_downloading"))
        self.nasa_status_lbl.configure(text=self.get_text("nasa_status_fetching"), text_color="#1f538d")
        
        lat = self.lat_entry.get_float(14.5)
        lon = self.lon_entry.get_float(-16.2)
        year = self.year_entry.get_int(2023)
        
        def run():
            try:
                logger.info(f"Launching NASA POWER query: Lat={lat}, Lon={lon}, Year={year}...")
                handler = NASAWeatherDataHandler()
                df = handler.fetch_weather_data(lat=lat, lon=lon, year=year)
                self.after(0, lambda: self.finish_nasa_fetch(df, lat, lon, year))
            except Exception as e:
                logger.error(f"NASA POWER API request failed: {e}")
                self.after(0, lambda: self.finish_nasa_fetch(None, lat, lon, year, error=str(e)))
                
        threading.Thread(target=run, daemon=True).start()

    def finish_nasa_fetch(self, df, lat, lon, year, error=None):
        self.fetch_nasa_btn.configure(state="normal", text=self.get_text("nasa_btn"))
        if error:
            mb.showerror(self.get_text("error"), f"{error}")
            self.nasa_status_lbl.configure(text=self.get_text("error"), text_color="red")
        else:
            self.weather_df = df
            if self.load_df is not None:
                self.load_df.index = self.weather_df.index
                
            self.nasa_status_lbl.configure(
                text=self.get_text("nasa_status_success").format(lat=lat, lon=lon), 
                text_color="#2ca02c"
            )
            logger.info("NASA weather data loaded successfully.")
            self.trigger_quick_base_simulation()
            self.update_previs_plot()

    def build_tab_optimization(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=0) # Title
        frame.grid_rowconfigure(1, weight=0) # Form
        frame.grid_rowconfigure(2, weight=1) # Log / Console area
        frame.grid_columnconfigure(0, weight=1)
        
        # Tab title
        title = ctk.CTkLabel(
            frame, 
            text=self.get_text("tab2_title"), 
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor=self.get_anchor()
        )
        title.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        
        # Grid parameters form (2 spacious columns)
        form_frame = ctk.CTkFrame(frame, corner_radius=12)
        form_frame.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Component availability section (spanning both columns at the top)
        comp_section = ctk.CTkFrame(form_frame, fg_color="transparent")
        comp_section.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="ew")
        for col_idx in range(5):
            comp_section.grid_columnconfigure(col_idx, weight=1)
            
        comp_title = ctk.CTkLabel(comp_section, text=self.get_text("comp_selection_title"), font=ctk.CTkFont(size=14, weight="bold"), anchor=self.get_anchor())
        comp_title.grid(row=0, column=0, columnspan=5, padx=10, pady=(0, 8), sticky="ew")
        
        self.enable_pv_cb = ctk.CTkCheckBox(comp_section, text=self.get_text("curve_pv"), command=self.on_component_toggle, font=ctk.CTkFont(weight="bold"))
        self.enable_pv_cb.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.enable_pv_cb.select()
        
        self.enable_wind_cb = ctk.CTkCheckBox(comp_section, text=self.get_text("kpi_wind"), command=self.on_component_toggle, font=ctk.CTkFont(weight="bold"))
        self.enable_wind_cb.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.enable_wind_cb.select()
        
        self.enable_bat_cb = ctk.CTkCheckBox(comp_section, text=self.get_text("kpi_bat"), command=self.on_component_toggle, font=ctk.CTkFont(weight="bold"))
        self.enable_bat_cb.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.enable_bat_cb.select()
        
        self.enable_diesel_cb = ctk.CTkCheckBox(comp_section, text=self.get_text("kpi_diesel"), command=self.on_component_toggle, font=ctk.CTkFont(weight="bold"))
        self.enable_diesel_cb.grid(row=1, column=3, padx=10, pady=5, sticky="w")
        self.enable_diesel_cb.select()
        
        # Constraints inputs (left column, row 1)
        c_section = ctk.CTkFrame(form_frame, fg_color="transparent")
        c_section.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        c_section.grid_columnconfigure(0, weight=1)
        
        cs_title = ctk.CTkLabel(c_section, text=self.get_text("design_criteria"), font=ctk.CTkFont(size=15, weight="bold"), anchor=self.get_anchor())
        cs_title.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        self.lolp_max_slider = LabeledSlider(c_section, self.get_text("lolp_max"), from_=0.0, to=20.0, default_value=5.0, resolution=0.5, value_suffix=" %")
        self.lolp_max_slider.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # GA inputs (right column, row 1)
        ga_section = ctk.CTkFrame(form_frame, fg_color="transparent")
        ga_section.grid(row=1, column=1, padx=15, pady=15, sticky="nsew")
        ga_section.grid_columnconfigure(0, weight=1)
        
        gas_title = ctk.CTkLabel(ga_section, text=self.get_text("ga_params"), font=ctk.CTkFont(size=15, weight="bold"), anchor=self.get_anchor())
        gas_title.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        self.generations_slider = LabeledSlider(ga_section, self.get_text("generations"), from_=5, to=100, default_value=25, resolution=5, value_suffix="")
        self.generations_slider.grid(row=1, column=0, padx=10, pady=6, sticky="ew")
        
        self.pop_size_slider = LabeledSlider(ga_section, self.get_text("pop_size"), from_=5, to=50, default_value=12, resolution=2, value_suffix="")
        self.pop_size_slider.grid(row=2, column=0, padx=10, pady=6, sticky="ew")
        
        self.force_numpy_checkbox = ctk.CTkCheckBox(ga_section, text=self.get_text("force_numpy"))
        self.force_numpy_checkbox.grid(row=3, column=0, padx=15, pady=(10, 5), sticky="w")
        
        # Run and progress elements (spanning both columns, row 2)
        run_section = ctk.CTkFrame(form_frame, fg_color="transparent")
        run_section.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        run_section.grid_columnconfigure(0, weight=1)
        
        self.run_opt_btn = ctk.CTkButton(
            run_section,
            text=self.get_text("run_opt"),
            height=50,
            fg_color="#2ca02c",
            hover_color="#228022",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_optimization
        )
        self.run_opt_btn.grid(row=0, column=0, sticky="ew")
        
        self.opt_progress_lbl = ctk.CTkLabel(
            run_section, 
            text=self.get_text("opt_status_idle"), 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.opt_progress_lbl.grid(row=1, column=0, pady=(10, 2))
        
        self.opt_progressbar = ctk.CTkProgressBar(run_section)
        self.opt_progressbar.grid(row=2, column=0, pady=(2, 10), sticky="ew")
        self.opt_progressbar.set(0.0)
        
        # Real-time logging console
        console_frame = ctk.CTkFrame(frame)
        console_frame.grid(row=2, column=0, padx=30, pady=(10, 30), sticky="nsew")
        console_frame.grid_rowconfigure(1, weight=1)
        console_frame.grid_columnconfigure(0, weight=1)
        
        console_title = ctk.CTkLabel(
            console_frame, 
            text=self.get_text("opt_console_title"), 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor=self.get_anchor()
        )
        console_title.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")
        
        self.console_textbox = ctk.CTkTextbox(console_frame, font=ctk.CTkFont(family="Courier", size=11))
        self.console_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.console_textbox.configure(state="disabled")
        
        return frame

    def setup_logging_interceptor(self):
        """Attaches our TextboxHandler to the root logger to display terminal logs in the UI."""
        handler = TextboxHandler(self.console_textbox)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

    def on_component_toggle(self):
        """Callback when any component is enabled/disabled. Instantly updates base simulation."""
        self.trigger_quick_base_simulation()
        self.update_previs_plot()

    def start_optimization(self):
        """Starts the optimization algorithm in a background thread."""
        if self.weather_df is None or self.load_df is None:
            mb.showerror(self.get_text("error"), self.get_text("missing_data_error"))
            return
            
        # Ensure at least one power source is active
        if not (self.enable_pv_cb.get() or self.enable_wind_cb.get() or self.enable_diesel_cb.get()):
            mb.showerror(self.get_text("error"), self.get_text("invalid_config_error"))
            return

        # Lock UI components
        self.run_opt_btn.configure(state="disabled", text=self.get_text("opt_running"))
        self.opt_progress_lbl.configure(text=self.get_text("opt_calculating"), text_color="#1f538d")
        self.opt_progressbar.set(0.0)
        self.console_textbox.configure(state="normal")
        self.console_textbox.delete("1.0", tk.END)
        self.console_textbox.configure(state="disabled")
        
        # Read parameters
        lolp_max = self.lolp_max_slider.get() / 100.0
        generations = int(self.generations_slider.get())
        pop_size = int(self.pop_size_slider.get())
        use_fallback = self.force_numpy_checkbox.get()
        
        cost_overrides = {
            "pv_capex": self.pv_capex_entry.get_float(1000.0),
            "wind_capex": self.wind_capex_entry.get_float(1600.0),
            "battery_capex": self.battery_capex_entry.get_float(300.0),
            "diesel_capex": self.diesel_capex_entry.get_float(400.0),
            "diesel_fuel_price": self.fuel_price_entry.get_float(1.2)
        }
        
        system_config_base = {
            "pv_derating_factor": 0.82,
            "pv_temp_coeff": -0.004,
            "battery_efficiency_charge": 0.96,
            "battery_efficiency_discharge": 0.96,
            "battery_min_soc": 0.2,
            "battery_max_soc": 1.0,
            "diesel_min_load_fraction": 0.3
        }
        
        # Determine optimization bounds (force (0, 0) if disabled)
        pv_bounds = (0.0, 200.0) if self.enable_pv_cb.get() else (0.0, 0.0)
        wind_bounds = (0.0, 100.0) if self.enable_wind_cb.get() else (0.0, 0.0)
        battery_bounds = (0.0, 500.0) if self.enable_bat_cb.get() else (0.0, 0.0)
        diesel_bounds = (0.0, 50.0) if self.enable_diesel_cb.get() else (0.0, 0.0)

        # Define background execution task
        def run():
            try:
                start_time = time.time()
                logger.info("Initialisation de l'Optimiseur HRES...")
                
                optimizer = GAOptimizer(
                    weather_df=self.weather_df,
                    load_df=self.load_df,
                    cost_params=cost_overrides,
                    system_config_base=system_config_base,
                    lolp_max=lolp_max,
                    pv_bounds=pv_bounds,
                    wind_bounds=wind_bounds,
                    battery_bounds=battery_bounds,
                    diesel_bounds=diesel_bounds,
                    num_generations=generations,
                    sol_per_pop=pop_size,
                    use_fallback_ga=use_fallback
                )
                
                # Wrap fitness function to count calls and report progress
                original_fitness = optimizer.fitness_func
                calls = 0
                total_calls = generations * pop_size
                
                def wrapped_fitness(ga_instance, solution, solution_idx):
                    nonlocal calls
                    calls += 1
                    gen = min(generations, (calls - 1) // pop_size + 1)
                    
                    # Schedule UI update on main thread safely
                    self.after(0, lambda g=gen, c=calls: self.update_optimization_progress(g, generations, c, total_calls))
                    
                    return original_fitness(ga_instance, solution, solution_idx)
                
                optimizer.fitness_func = wrapped_fitness
                
                # Execute optimization
                results = optimizer.optimize()
                duration = time.time() - start_time
                results["duration"] = duration
                
                # Send completion to main thread
                self.after(0, lambda: self.on_optimization_complete(results))
                
            except Exception as e:
                logger.error(f"GA Optimization crashed: {e}")
                self.after(0, lambda err=str(e): self.on_optimization_error(err))
                
        threading.Thread(target=run, daemon=True).start()

    def update_optimization_progress(self, gen, total_gen, calls, total_calls):
        """Updates the progress bar and status text safely from the GA thread."""
        progress = min(1.0, calls / total_calls)
        self.opt_progressbar.set(progress)
        
        # Build status string
        lang = getattr(self, "current_language", "fr")
        if lang == "ar":
            status_text = f"جاري التشغيل : جيل {gen}/{total_gen} | تقييم: {calls}/{total_calls} ({int(progress * 100)}%)"
        elif lang == "en":
            status_text = f"Running: Generation {gen}/{total_gen} | Evaluation: {calls}/{total_calls} ({int(progress * 100)}%)"
        else:
            status_text = f"Exécution : Génération {gen}/{total_gen} | Évaluations: {calls}/{total_calls} ({int(progress * 100)}%)"
            
        self.opt_progress_lbl.configure(text=status_text, text_color="#1f538d")

    def on_optimization_complete(self, results):
        """Updates the application state and switches to results view on success."""
        self.results = results
        self.run_opt_btn.configure(state="normal", text=self.get_text("run_opt"))
        
        lang = getattr(self, "current_language", "fr")
        if lang == "ar":
            done_txt = f"تم الانتهاء بنجاح في {results['duration']:.2f} ثانية!"
        elif lang == "en":
            done_txt = f"Completed successfully in {results['duration']:.2f}s!"
        else:
            done_txt = f"Terminé avec succès en {results['duration']:.2f}s !"
            
        self.opt_progress_lbl.configure(text=done_txt, text_color="#2ca02c")
        self.opt_progressbar.set(1.0)
        
        # Rerun simulation using best sizes to get full hourly dynamics
        best_cfg = results["best_configuration"]
        system_config_base = {
            "pv_derating_factor": 0.82,
            "pv_temp_coeff": -0.004,
            "battery_efficiency_charge": 0.96,
            "battery_efficiency_discharge": 0.96,
            "battery_min_soc": 0.2,
            "battery_max_soc": 1.0,
            "diesel_min_load_fraction": 0.3
        }
        
        config = {**system_config_base, **best_cfg}
        self.hourly_df, _ = run_simulation(self.weather_df, self.load_df, config)
        
        logger.info(f"Sizing Optimal Trouvé : PV={best_cfg['pv_capacity']:.2f} kW, Wind={best_cfg['wind_capacity']:.2f} kW, Bat={best_cfg['battery_capacity']:.2f} kWh, Diesel={best_cfg['diesel_capacity']:.2f} kW.")
        logger.info(f"Performance: LCOE=${results['metrics']['lcoe']:.4f}/kWh, NPC=${results['metrics']['npc']:,.2f}, LOLP={results['metrics']['lolp']*100.0:.3f}%.")
        
        # Refresh results tab UI
        self.results_page_needs_refresh = True
        
        # Automatically navigate the user to Tab 3
        self.select_tab("Résultats & Graphiques")

    def on_optimization_error(self, error_message):
        """Re-enables controls and shows error details on crash."""
        self.run_opt_btn.configure(state="normal", text=self.get_text("run_opt"))
        self.opt_progress_lbl.configure(text=self.get_text("error"), text_color="red")
        mb.showerror(self.get_text("error"), f"{error_message}")

    def trigger_quick_base_simulation(self):
        """Runs a fast simulation with default parameters on data changes to keep charts active."""
        if self.weather_df is None or self.load_df is None:
            return
            
        try:
            logger.info("Recalcul rapide des profils physiques de simulation...")
            raw_cfg = self.results["best_configuration"] if self.results else {
                "pv_capacity": 45.0, "wind_capacity": 15.0, "battery_capacity": 120.0, "diesel_capacity": 25.0
            }
            best_cfg = raw_cfg.copy()
            
            # Override capacity to 0.0 if disabled via checkboxes
            if hasattr(self, "enable_pv_cb") and not self.enable_pv_cb.get():
                best_cfg["pv_capacity"] = 0.0
            if hasattr(self, "enable_wind_cb") and not self.enable_wind_cb.get():
                best_cfg["wind_capacity"] = 0.0
            if hasattr(self, "enable_bat_cb") and not self.enable_bat_cb.get():
                best_cfg["battery_capacity"] = 0.0
            if hasattr(self, "enable_diesel_cb") and not self.enable_diesel_cb.get():
                best_cfg["diesel_capacity"] = 0.0
                
            system_config_base = {
                "pv_derating_factor": 0.82, "pv_temp_coeff": -0.004,
                "battery_efficiency_charge": 0.96, "battery_efficiency_discharge": 0.96,
                "battery_min_soc": 0.2, "battery_max_soc": 1.0, "diesel_min_load_fraction": 0.3
            }
            config = {**system_config_base, **best_cfg}
            self.hourly_df, summary = run_simulation(self.weather_df, self.load_df, config)
            
            # Recalculate financials
            cost_overrides = {
                "pv_capex": self.pv_capex_entry.get_float(1000.0),
                "wind_capex": self.wind_capex_entry.get_float(1600.0),
                "battery_capex": self.battery_capex_entry.get_float(300.0),
                "diesel_capex": self.diesel_capex_entry.get_float(400.0),
                "diesel_fuel_price": self.fuel_price_entry.get_float(1.2)
            }
            
            lcoe, details = calculate_lcoe(
                pv_capacity=best_cfg["pv_capacity"],
                wind_capacity=best_cfg["wind_capacity"],
                battery_capacity=best_cfg["battery_capacity"],
                diesel_capacity=best_cfg["diesel_capacity"],
                cost_params=cost_overrides,
                annual_diesel_operating_hours=float((self.hourly_df["diesel_output"] > 1e-3).sum()) if "diesel_output" in self.hourly_df.columns else 0.0,
                annual_fuel_consumption=summary["total_fuel_consumption_liters"],
                annual_battery_degradation_fraction=max(0.0, (100.0 - summary["battery_soh_pct"]) / 100.0),
                total_annual_load_kwh=float(self.load_df["total_load"].sum()),
                annual_unmet_load_kwh=summary["total_unmet_load_kwh"]
            )
            
            self.results = {
                "best_configuration": best_cfg,
                "metrics": {
                    "lcoe": lcoe,
                    "npc": details["npc"],
                    "capital_cost": details["capital_cost"],
                    "annual_om_cost": details["annual_om_cost"],
                    "annual_fuel_cost": details["annual_fuel_cost"],
                    "unmet_load_kwh": summary["total_unmet_load_kwh"],
                    "lolp": summary["lolp"],
                    "renewable_fraction": summary["renewable_fraction"],
                    "diesel_operating_hours": float((self.hourly_df["diesel_output"] > 1e-3).sum()) if "diesel_output" in self.hourly_df.columns else 0.0,
                    "fuel_consumption_liters": summary["total_fuel_consumption_liters"],
                    "battery_soh_pct": summary["battery_soh_pct"]
                },
                "financial_details": details,
                "optimization_method": "Recalcul Données"
            }
            
            self.results_page_needs_refresh = True
            logger.info("Recalcul de simulation terminé.")
        except Exception as e:
            logger.error(f"Failing quick simulation recalculation: {e}")

    # =========================================================================
    # TAB 3: RÉSULTATS & GRAPHIQUES (Results Display)
    # =========================================================================
    def build_tab_results(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=0) # Title
        frame.grid_rowconfigure(1, weight=1) # Core split view
        frame.grid_columnconfigure(0, weight=1)
        
        self.results_page_needs_refresh = True
        
        # Tab title
        title = ctk.CTkLabel(
            frame, 
            text=self.get_text("tab3_title"), 
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor=self.get_anchor()
        )
        title.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        
        # Split layout using tk.PanedWindow
        split_frame = self.create_paned_window(frame, tk.HORIZONTAL)
        split_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")
        
        # LEFT: Cards Summary
        left_container = ctk.CTkFrame(split_frame, fg_color="transparent")
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_columnconfigure(0, weight=1)
        
        left_scroller = ctk.CTkScrollableFrame(left_container, width=350)
        left_scroller.grid(row=0, column=0, sticky="nsew")
        left_scroller.grid_columnconfigure(0, weight=1)
        
        # Sizing title
        sec1 = ctk.CTkLabel(left_scroller, text=self.get_text("optimal_capacity"), font=ctk.CTkFont(size=15, weight="bold"), anchor=self.get_anchor())
        sec1.grid(row=0, column=0, columnspan=1, padx=10, pady=(10, 5), sticky="ew")
        
        # PV Card
        self.card_pv = self.create_kpi_row(left_scroller, self.get_text("kpi_pv"), "0.0 kW", 1, "#1f538d")
        # Wind Card
        self.card_wind = self.create_kpi_row(left_scroller, self.get_text("kpi_wind"), "0.0 kW", 2, "#1f538d")
        # Battery Card
        self.card_bat = self.create_kpi_row(left_scroller, self.get_text("kpi_bat"), "0.0 kWh", 3, "#1f538d")
        # Diesel Card
        self.card_diesel = self.create_kpi_row(left_scroller, self.get_text("kpi_diesel"), "0.0 kW", 4, "#1f538d")
        
        # Financial & Performance title
        sec2 = ctk.CTkLabel(left_scroller, text=self.get_text("perf_finance"), font=ctk.CTkFont(size=15, weight="bold"), anchor=self.get_anchor())
        sec2.grid(row=5, column=0, columnspan=1, padx=10, pady=(20, 5), sticky="ew")
        
        # LCOE Card
        self.card_lcoe = self.create_kpi_row(left_scroller, self.get_text("kpi_lcoe"), "$0.000", 6, "#2c4c38")
        # NPC Card
        self.card_npc = self.create_kpi_row(left_scroller, self.get_text("kpi_npc"), "$0", 7, "#2c4c38")
        # Fuel Card
        self.card_fuel = self.create_kpi_row(left_scroller, self.get_text("kpi_fuel"), "0 Litres", 8, "#735c18")
        # LOLP Card
        self.card_lolp = self.create_kpi_row(left_scroller, self.get_text("kpi_lolp"), "0.00%", 9, "#7b1c1c")
        # Renewables Share
        self.card_ren = self.create_kpi_row(left_scroller, self.get_text("kpi_ren"), "0.0%", 10, "#2c5f2d")
        # Battery SOH
        self.card_soh = self.create_kpi_row(left_scroller, self.get_text("kpi_soh"), "100.0%", 11, "#1e6b7b")
        
        # RIGHT: Plots Section using vertical tk.PanedWindow
        right_frame = self.create_paned_window(split_frame, tk.VERTICAL)
        
        # RTL support: swap columns inside split_frame horizontal sashes
        is_rtl = (getattr(self, "current_language", "fr") == "ar")
        if is_rtl:
            split_frame.add(right_frame)
            split_frame.add(left_container, width=350)
        else:
            split_frame.add(left_container, width=350)
            split_frame.add(right_frame)
        
        # Container for hourly line plot + toggles + sliders
        hourly_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        hourly_container.grid_rowconfigure(0, weight=1)  # Plot
        hourly_container.grid_rowconfigure(1, weight=0)  # Curve Toggles
        hourly_container.grid_rowconfigure(2, weight=0)  # Sliders
        hourly_container.grid_columnconfigure(0, weight=1)
        right_frame.add(hourly_container, height=420)
        
        # Plot 1: Line Chart
        self.plot_hourly = PlotCanvas(hourly_container, dpi=90)
        self.plot_hourly.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        
        # Curve Toggles Frame
        curve_toggle_frame = ctk.CTkFrame(hourly_container, fg_color="transparent")
        curve_toggle_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        for c in range(5):
            curve_toggle_frame.grid_columnconfigure(c, weight=1)
            
        self.show_curve_pv = tk.BooleanVar(value=True)
        self.show_curve_wind = tk.BooleanVar(value=True)
        self.show_curve_diesel = tk.BooleanVar(value=True)
        self.show_curve_load = tk.BooleanVar(value=True)
        self.show_curve_soc = tk.BooleanVar(value=True)
        
        cb_pv = ctk.CTkCheckBox(curve_toggle_frame, text=self.get_text("curve_pv"), variable=self.show_curve_pv, command=self.update_hourly_plot, text_color="#e6a100", font=ctk.CTkFont(weight="bold"))
        cb_pv.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        cb_wind = ctk.CTkCheckBox(curve_toggle_frame, text=self.get_text("curve_wind"), variable=self.show_curve_wind, command=self.update_hourly_plot, text_color="#00a8e6", font=ctk.CTkFont(weight="bold"))
        cb_wind.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        cb_diesel = ctk.CTkCheckBox(curve_toggle_frame, text=self.get_text("curve_diesel"), variable=self.show_curve_diesel, command=self.update_hourly_plot, text_color="#735c18", font=ctk.CTkFont(weight="bold"))
        cb_diesel.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        
        cb_load = ctk.CTkCheckBox(curve_toggle_frame, text=self.get_text("curve_load"), variable=self.show_curve_load, command=self.update_hourly_plot, text_color="#c7254e", font=ctk.CTkFont(weight="bold"))
        cb_load.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        
        cb_soc = ctk.CTkCheckBox(curve_toggle_frame, text=self.get_text("curve_soc"), variable=self.show_curve_soc, command=self.update_hourly_plot, text_color="#2ca02c", font=ctk.CTkFont(weight="bold"))
        cb_soc.grid(row=0, column=4, padx=5, pady=2, sticky="w")
        
        # Slicing frame
        slider_frame = ctk.CTkFrame(hourly_container, fg_color="transparent")
        slider_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        slider_frame.grid_columnconfigure(0, weight=1)
        slider_frame.grid_columnconfigure(1, weight=1)
        
        self.start_day_slider = ctk.CTkSlider(slider_frame, from_=1, to=360, number_of_steps=360, command=self.on_plot_slider_move)
        self.start_day_slider.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        self.start_day_slider.set(1)
        
        self.duration_slider = ctk.CTkSlider(slider_frame, from_=1, to=30, number_of_steps=30, command=self.on_plot_slider_move)
        self.duration_slider.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.duration_slider.set(7)
        
        self.plot_slider_lbl = ctk.CTkLabel(
            slider_frame, 
            text="", 
            font=ctk.CTkFont(size=12, slant="italic")
        )
        self.plot_slider_lbl.grid(row=1, column=0, columnspan=2, pady=(2, 5))
        
        # Container for energy share bar / pie chart
        share_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        share_container.grid_rowconfigure(0, weight=1)
        share_container.grid_columnconfigure(0, weight=1)
        right_frame.add(share_container, height=320)
        
        # Plot 2: Share Bar / Pie Chart
        self.plot_share = PlotCanvas(share_container, dpi=90)
        self.plot_share.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
        
        # Hook show event to reload card widgets values
        frame.on_show = self.refresh_results_tab_contents
        
        return frame

    def create_kpi_row(self, parent, title, value, row, fg_color):
        card = ctk.CTkFrame(parent, corner_radius=6, fg_color=fg_color, height=35)
        card.grid(row=row, column=0, padx=10, pady=4, sticky="ew")
        
        app = self.winfo_toplevel()
        is_rtl = hasattr(app, "current_language") and app.current_language == "ar"
        
        # Swapped pack directions for Arabic
        pack_title = "right" if is_rtl else "left"
        pack_val = "left" if is_rtl else "right"
        
        title_lbl = ctk.CTkLabel(
            card, 
            text=title, 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="white"
        )
        title_lbl.pack(side=pack_title, padx=15, pady=5)
        
        val_lbl = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color="white",
            width=130,
            anchor="w" if is_rtl else "e"
        )
        val_lbl.pack(side=pack_val, padx=15, pady=5)
        
        return val_lbl

    def refresh_results_tab_contents(self):
        """Loads and draws numerical cards and charts in Tab 3."""
        if not self.results or not self.results_page_needs_refresh:
            return
            
        best = self.results["best_configuration"]
        metrics = self.results["metrics"]
        
        # Update cards (show "Exclu" if component is disabled in Tab 2)
        exclu_txt = self.get_text("exclu")
        
        pv_txt = f"{best['pv_capacity']:.2f} kW" if (hasattr(self, "enable_pv_cb") and self.enable_pv_cb.get()) else exclu_txt
        self.card_pv.configure(text=pv_txt)
        
        wind_txt = f"{best['wind_capacity']:.2f} kW" if (hasattr(self, "enable_wind_cb") and self.enable_wind_cb.get()) else exclu_txt
        self.card_wind.configure(text=wind_txt)
        
        bat_txt = f"{best['battery_capacity']:.2f} kWh" if (hasattr(self, "enable_bat_cb") and self.enable_bat_cb.get()) else exclu_txt
        self.card_bat.configure(text=bat_txt)
        
        diesel_txt = f"{best['diesel_capacity']:.2f} kW" if (hasattr(self, "enable_diesel_cb") and self.enable_diesel_cb.get()) else exclu_txt
        self.card_diesel.configure(text=diesel_txt)
        
        self.card_lcoe.configure(text=f"${metrics['lcoe']:.4f} /kWh")
        self.card_npc.configure(text=f"${metrics['npc']:,.2f}")
        
        # LITRES translation
        lang = getattr(self, "current_language", "fr")
        litres_lbl = "لتر" if lang == "ar" else ("Liters" if lang == "en" else "Litres")
        self.card_fuel.configure(text=f"{metrics['fuel_consumption_liters']:,.1f} {litres_lbl}")
        
        self.card_lolp.configure(text=f"{metrics['lolp']*100.0:.3f}%")
        self.card_ren.configure(text=f"{metrics['renewable_fraction']*100.0:.1f}%")
        self.card_soh.configure(text=f"{metrics['battery_soh_pct']:.2f}%")
        
        # Redraw plots
        self.update_hourly_plot()
        self.update_energy_share_plot()
        
        self.results_page_needs_refresh = False

    def on_plot_slider_move(self, _):
        """Updates date ranges text and updates line plot."""
        self.update_hourly_plot()

    def update_hourly_plot(self):
        """Draws the dynamic timeseries line chart of physical microgrid operation."""
        if self.hourly_df is None:
            return
            
        start_day = int(self.start_day_slider.get())
        duration_days = int(self.duration_slider.get())
        
        # Slicing indexes
        start_idx = (start_day - 1) * 24
        end_idx = min(8760, start_idx + duration_days * 24)
        
        sliced_df = self.hourly_df.iloc[start_idx:end_idx]
        
        # Label date format
        st = self.hourly_df.index[start_idx]
        en = self.hourly_df.index[min(8759, end_idx - 1)]
        
        lang = getattr(self, "current_language", "fr")
        if lang == "ar":
            period_text = f"الفترة: من {st.strftime('%Y-%m-%d %H:%M')} إلى {en.strftime('%Y-%m-%d %H:%M')} ({duration_days} يوم)"
        elif lang == "en":
            period_text = f"Period: {st.strftime('%Y-%m-%d %H:%M')} to {en.strftime('%Y-%m-%d %H:%M')} ({duration_days} days)"
        else:
            period_text = f"Période: {st.strftime('%Y-%m-%d %H:%M')} au {en.strftime('%Y-%m-%d %H:%M')} ({duration_days} jours)"
            
        self.plot_slider_lbl.configure(text=period_text)
        
        # Matplotlib drawing
        fig = self.plot_hourly.fig
        fig.clear()
        ax = fig.add_subplot(111)
        
        # Plot physical lines
        if "pv_output" in sliced_df.columns and getattr(self, "show_curve_pv", None) and self.show_curve_pv.get():
            lbl = self.get_text("curve_pv") + " (kW)"
            ax.plot(sliced_df.index, sliced_df["pv_output"], label=lbl, color="#e6a100", linewidth=1.5)
        if "wind_output" in sliced_df.columns and getattr(self, "show_curve_wind", None) and self.show_curve_wind.get():
            lbl = self.get_text("curve_wind") + " (kW)"
            ax.plot(sliced_df.index, sliced_df["wind_output"], label=lbl, color="#00a8e6", linewidth=1.5)
        if "diesel_output" in sliced_df.columns and getattr(self, "show_curve_diesel", None) and self.show_curve_diesel.get():
            lbl = self.get_text("curve_diesel") + " (kW)"
            ax.plot(sliced_df.index, sliced_df["diesel_output"], label=lbl, color="#735c18", linewidth=1.5)
        if getattr(self, "show_curve_load", None) and self.show_curve_load.get():
            lbl = self.get_text("curve_load") + " (kW)"
            if "total_load" in sliced_df.columns:
                ax.plot(sliced_df.index, sliced_df["total_load"], label=lbl, color="#c7254e", linewidth=2.0, linestyle="--")
            elif "load" in sliced_df.columns:
                ax.plot(sliced_df.index, sliced_df["load"], label=lbl, color="#c7254e", linewidth=2.0, linestyle="--")
            
        # SOC on secondary y-axis if available
        has_soc = "battery_soc" in sliced_df.columns and getattr(self, "show_curve_soc", None) and self.show_curve_soc.get()
        if has_soc:
            ax2 = ax.twinx()
            lbl = self.get_text("curve_soc") + " (%)"
            ax2.plot(sliced_df.index, sliced_df["battery_soc"] * 100.0, label=lbl, color="#2ca02c", linewidth=1.2, linestyle=":")
            ax2.set_ylabel(lbl, color="#2ca02c")
            ax2.tick_params(colors="#2ca02c")
            ax2.set_ylim(-5, 105)
            
        ax.set_title(self.get_text("chart_hourly_title"), fontsize=11, fontweight="bold")
        ax.set_xlabel(self.get_text("chart_hourly_x"))
        ax.set_ylabel(self.get_text("chart_hourly_y"))
        ax.grid(True, linestyle=":", alpha=0.6)
        
        # Build composite legend
        lines, labels = ax.get_legend_handles_labels()
        if has_soc:
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines + lines2, labels + labels2, loc="upper right", fontsize=8, framealpha=0.6)
        else:
            ax.legend(loc="upper right", fontsize=8, framealpha=0.6)
            
        self.plot_hourly.draw()

    def update_energy_share_plot(self):
        """Draws the annual generation share breakdown chart."""
        if self.hourly_df is None:
            return
            
        fig = self.plot_share.fig
        fig.clear()
        ax = fig.add_subplot(111)
        
        # Calculate sum energy (kWh)
        pv_kwh = float(self.hourly_df["pv_output"].sum()) if "pv_output" in self.hourly_df.columns else 0.0
        wind_kwh = float(self.hourly_df["wind_output"].sum()) if "wind_output" in self.hourly_df.columns else 0.0
        diesel_kwh = float(self.hourly_df["diesel_output"].sum()) if "diesel_output" in self.hourly_df.columns else 0.0
        
        total_gen = pv_kwh + wind_kwh + diesel_kwh
        
        if total_gen <= 0:
            lbl = "لا توجد بيانات إنتاج" if getattr(self, "current_language", "fr") == "ar" else "No generation data"
            ax.text(0.5, 0.5, lbl, ha="center", va="center")
            self.plot_share.draw()
            return
            
        labels = []
        sizes = []
        colors = []
        
        pv_lbl = self.get_text("curve_pv")
        wind_lbl = self.get_text("curve_wind")
        diesel_lbl = self.get_text("curve_diesel")
        
        if pv_kwh > 0:
            labels.append(f"{pv_lbl}: {pv_kwh/1000.0:.1f} MWh")
            sizes.append(pv_kwh)
            colors.append("#e6a100")
        if wind_kwh > 0:
            labels.append(f"{wind_lbl}: {wind_kwh/1000.0:.1f} MWh")
            sizes.append(wind_kwh)
            colors.append("#00a8e6")
        if diesel_kwh > 0:
            labels.append(f"{diesel_lbl}: {diesel_kwh/1000.0:.1f} MWh")
            sizes.append(diesel_kwh)
            colors.append("#735c18")
            
        # Draw Pie
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct="%1.1f%%",
            startangle=90, 
            colors=colors,
            textprops=dict(color="black" if ctk.get_appearance_mode().lower() == "light" else "white")
        )
        
        # Formatting text colors inside wedges
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
            
        ax.set_title(self.get_text("chart_share_title"), fontsize=11, fontweight="bold")
        
        self.plot_share.draw()

    def refresh_all_plots(self):
        """Forces replotting canvases to match changing visual appearance mode themes."""
        self.plot_hourly.apply_theme()
        self.plot_share.apply_theme()
        if hasattr(self, "scenario_canvas"):
            self.scenario_canvas.apply_theme()
        self.update_hourly_plot()
        self.update_energy_share_plot()
        self.update_scenario_comparison_chart()

    # =========================================================================
    # TAB 4: COMPARATIF DE SCÉNARIOS (Scenario Manager)
    # =========================================================================
    def build_tab_scenario_comparison(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=0) # Title
        frame.grid_rowconfigure(1, weight=1) # Content split view
        frame.grid_columnconfigure(0, weight=1)
        
        # Tab title
        title = ctk.CTkLabel(
            frame, 
            text=self.get_text("tab4_title"), 
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor=self.get_anchor()
        )
        title.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        
        # Split view using tk.PanedWindow
        split_frame = self.create_paned_window(frame, tk.HORIZONTAL)
        split_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")
        
        # LEFT: Add & controls
        control_card = ctk.CTkFrame(split_frame, corner_radius=12)
        control_card.grid_columnconfigure(0, weight=1)
        
        c_title = ctk.CTkLabel(control_card, text=self.get_text("scenario_actions"), font=ctk.CTkFont(size=16, weight="bold"))
        c_title.grid(row=0, column=0, padx=15, pady=(20, 15), sticky="ew")
        
        self.scenario_name_entry = LabeledEntry(control_card, self.get_text("scenario_name"), "")
        self.scenario_name_entry.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        save_btn = ctk.CTkButton(
            control_card,
            text=self.get_text("btn_save_scenario"),
            height=40,
            command=self.save_current_scenario
        )
        save_btn.grid(row=2, column=0, padx=15, pady=(10, 5), sticky="ew")
        
        reset_btn = ctk.CTkButton(
            control_card,
            text=self.get_text("btn_reset_scenario"),
            height=40,
            fg_color="#7b1c1c",
            hover_color="#5a1414",
            command=self.reset_all_scenarios
        )
        reset_btn.grid(row=3, column=0, padx=15, pady=(5, 20), sticky="ew")
        
        # Quick notes info card
        info_card = ctk.CTkFrame(control_card, fg_color="transparent", border_width=1, border_color="gray")
        info_card.grid(row=4, column=0, padx=15, pady=20, sticky="ew")
        
        info_lbl = ctk.CTkLabel(
            info_card, 
            text=self.get_text("scenario_info_text"),
            justify="left",
            wraplength=180,
            font=ctk.CTkFont(size=11, slant="italic")
        )
        info_lbl.grid(row=0, column=0, padx=15, pady=15)
        
        # RIGHT: Scrollable table & Bar charts using vertical tk.PanedWindow
        right_panel = self.create_paned_window(split_frame, tk.VERTICAL)
        
        # RTL support: swap columns inside split_frame horizontal sashes
        is_rtl = (getattr(self, "current_language", "fr") == "ar")
        if is_rtl:
            split_frame.add(right_panel)
            split_frame.add(control_card, width=280)
        else:
            split_frame.add(control_card, width=280)
            split_frame.add(right_panel)
        
        # 1. Table Container
        table_container = ctk.CTkFrame(right_panel)
        right_panel.add(table_container, height=280)
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        t_title = ctk.CTkLabel(table_container, text=self.get_text("scenarios_saved_title"), font=ctk.CTkFont(size=14, weight="bold"), anchor=self.get_anchor())
        t_title.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")
        
        self.scenarios_table_scroller = ctk.CTkScrollableFrame(table_container)
        self.scenarios_table_scroller.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # 2. Comparison Chart Container
        canvas_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        right_panel.add(canvas_container, height=350)
        
        self.scenario_canvas = PlotCanvas(canvas_container, dpi=90)
        self.scenario_canvas.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        
        # Bind refresh event on tab showing
        frame.on_show = self.refresh_scenarios_tab
        
        return frame

    def refresh_scenarios_tab(self):
        """Reloads scenario tables and compares them visually in the bar chart."""
        self.rebuild_scenarios_table_view()
        self.update_scenario_comparison_chart()
        
        # Generate default localized scenario name
        lang = getattr(self, "current_language", "fr")
        prefix = "سيناريو" if lang == "ar" else ("Scenario" if lang == "en" else "Scénario")
        self.scenario_name_entry.set(f"{prefix} {len(self.saved_scenarios) + 1}")

    def save_current_scenario(self):
        """Adds current optimization configuration to saved list."""
        lang = getattr(self, "current_language", "fr")
        if lang == "ar":
            title_over = "استبدال"
            msg_over = f"السيناريو باسم '{self.scenario_name_entry.get()}' موجود بالفعل. هل تريد استبداله؟"
            title_no = "لا توجد نتائج"
            msg_no = "لا توجد نتائج محاكاة متوفرة. يرجى تشغيل عملية التحسين أولاً."
            title_req = "الاسم مطلوب"
            msg_req = "يرجى كتابة اسم صحيح ومقبول للسيناريو."
        elif lang == "en":
            title_over = "Overwrite"
            msg_over = f"A scenario named '{self.scenario_name_entry.get()}' already exists. Do you want to replace it?"
            title_no = "No results"
            msg_no = "No simulation results available. Please run optimization first."
            title_req = "Name required"
            msg_req = "Please assign a descriptive name to the scenario."
        else:
            title_over = "Écraser"
            msg_over = f"Un scénario nommé '{self.scenario_name_entry.get()}' existe déjà. Voulez-vous le remplacer ?"
            title_no = "Aucun résultat"
            msg_no = "Aucun résultat de simulation n'est disponible. Lancez d'abord une optimisation."
            title_req = "Nom requis"
            msg_req = "Veuillez attribuer un nom descriptif au scénario."

        if not self.results:
            mb.showwarning(title_no, msg_no)
            return
            
        name = self.scenario_name_entry.get().strip()
        if not name:
            mb.showwarning(title_req, msg_req)
            return
            
        # Check duplicate
        if any(x["name"].lower() == name.lower() for x in self.saved_scenarios):
            if not mb.askyesno(title_over, msg_over):
                return
            # Remove duplicate
            self.saved_scenarios = [x for x in self.saved_scenarios if x["name"].lower() != name.lower()]
            
        best = self.results["best_configuration"]
        metrics = self.results["metrics"]
        
        # Create dict
        scen_dict = {
            "name": name,
            "pv_capacity": best["pv_capacity"],
            "wind_capacity": best["wind_capacity"],
            "battery_capacity": best["battery_capacity"],
            "diesel_capacity": best["diesel_capacity"],
            "lcoe": metrics["lcoe"],
            "npc": metrics["npc"],
            "lolp": metrics["lolp"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M")
        }
        
        self.saved_scenarios.append(scen_dict)
        self.save_scenarios_to_file()
        logger.info(f"Scenario '{name}' saved successfully.")
        
        # Re-draw UI
        self.refresh_scenarios_tab()

    def reset_all_scenarios(self):
        """Clears all saved scenarios after user confirmation."""
        if not self.saved_scenarios:
            return
            
        lang = getattr(self, "current_language", "fr")
        if lang == "ar":
            title_conf = "تأكيد"
            msg_conf = "هل أنت متأكد من رغبتك في حذف جميع السيناريوهات المحفوظة؟ هذه العملية غير قابلة للتراجع."
        elif lang == "en":
            title_conf = "Confirm"
            msg_conf = "Are you sure you want to delete all saved scenarios? This action is irreversible."
        else:
            title_conf = "Confirmer"
            msg_conf = "Voulez-vous vraiment supprimer tous les scénarios sauvegardés ? Cette opération est irréversible."

        if mb.askyesno(title_conf, msg_conf):
            self.saved_scenarios = []
            self.save_scenarios_to_file()
            logger.info("All scenarios cleared.")
            self.refresh_scenarios_tab()

    def delete_scenario(self, idx):
        """Deletes a single scenario by index."""
        if 0 <= idx < len(self.saved_scenarios):
            name = self.saved_scenarios[idx]["name"]
            del self.saved_scenarios[idx]
            self.save_scenarios_to_file()
            logger.info(f"Scenario '{name}' deleted.")
            self.refresh_scenarios_tab()

    def rebuild_scenarios_table_view(self):
        """Renders the scenario rows dynamically inside the scrollable container."""
        # Clear scroller children
        for widget in self.scenarios_table_scroller.winfo_children():
            widget.destroy()
            
        # Draw Headers
        lang = getattr(self, "current_language", "fr")
        if lang == "ar":
            headers = ["الاسم", "شمس (ك.و)", "رياح (ك.و)", "بطارية (ك.و.س)", "ديزل (ك.و)", "LCOE ($/kWh)", "NPC ($)", "LOLP (%)", "إجراء"]
            empty_txt = "لا توجد سيناريوهات محفوظة. استخدم الزر الجانبي لحفظ التكوين الحالي."
            del_txt = "حذف"
        elif lang == "en":
            headers = ["Name", "PV (kW)", "Wind (kW)", "Bat (kWh)", "Diesel (kW)", "LCOE ($/kWh)", "NPC ($)", "LOLP (%)", "Action"]
            empty_txt = "No saved scenarios. Use the button on the left to save the current configuration."
            del_txt = "Del."
        else:
            headers = ["Nom", "PV (kW)", "Éolien (kW)", "Bat (kWh)", "Diesel (kW)", "LCOE ($/kWh)", "NPC ($)", "LOLP (%)", "Action"]
            empty_txt = "Aucun scénario enregistré. Utilisez le bouton ci-contre pour sauvegarder la configuration active."
            del_txt = "Suppr."

        for col, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.scenarios_table_scroller, 
                text=h, 
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="center"
            )
            lbl.grid(row=0, column=col, padx=8, pady=5, sticky="ew")
            
        # Draw Rows
        if not self.saved_scenarios:
            lbl = ctk.CTkLabel(
                self.scenarios_table_scroller, 
                text=empty_txt,
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="gray"
            )
            lbl.grid(row=1, column=0, columnspan=len(headers), pady=20)
            return
            
        for r, sc in enumerate(self.saved_scenarios):
            row_idx = r + 1
            
            # Format row elements
            fields = [
                sc["name"],
                f"{sc['pv_capacity']:.1f}",
                f"{sc['wind_capacity']:.1f}",
                f"{sc['battery_capacity']:.1f}",
                f"{sc['diesel_capacity']:.1f}",
                f"${sc['lcoe']:.4f}",
                f"${sc['npc']:,.0f}",
                f"{sc['lolp']*100.0:.2f}%"
            ]
            
            # Draw fields
            for col, text in enumerate(fields):
                lbl = ctk.CTkLabel(
                    self.scenarios_table_scroller, 
                    text=text, 
                    font=ctk.CTkFont(size=11),
                    anchor="center"
                )
                lbl.grid(row=row_idx, column=col, padx=8, pady=4)
                
            # Delete button
            del_btn = ctk.CTkButton(
                self.scenarios_table_scroller,
                text=del_txt,
                width=50,
                height=22,
                fg_color="#7b1c1c",
                hover_color="#5a1414",
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda idx=r: self.delete_scenario(idx)
            )
            del_btn.grid(row=row_idx, column=len(fields), padx=8, pady=4)

    def update_scenario_comparison_chart(self):
        """Draws a dual-axis (NPC vs LCOE) bar chart comparing all saved scenarios side-by-side."""
        fig = self.scenario_canvas.fig
        fig.clear()
        
        lang = getattr(self, "current_language", "fr")
        if lang == "ar":
            chart_placeholder = "أضف سيناريوهات لعرض المخطط البياني للمقارنة"
            chart_title = "المقارنة الاقتصادية لسيناريوهات الشبكة"
            ylabel_lcoe = "LCOE ($/kWh)"
            ylabel_npc = "NPC ($ USD)"
        elif lang == "en":
            chart_placeholder = "Add scenarios to display the comparison chart"
            chart_title = "Economic Comparison of Scenario Architectures"
            ylabel_lcoe = "LCOE ($/kWh)"
            ylabel_npc = "NPC ($ USD)"
        else:
            chart_placeholder = "Ajoutez des scénarios pour afficher le graphique comparatif"
            chart_title = "Comparatif Économique des Architectures de Scénario"
            ylabel_lcoe = "LCOE ($/kWh)"
            ylabel_npc = "NPC ($ USD)"
            
        if not self.saved_scenarios:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, chart_placeholder, ha="center", va="center", fontsize=12)
            self.scenario_canvas.draw()
            return
            
        names = [sc["name"] for sc in self.saved_scenarios]
        lcoes = [sc["lcoe"] for sc in self.saved_scenarios]
        npcs = [sc["npc"] for sc in self.saved_scenarios]
        
        # Set up coordinates
        x = np.arange(len(names))
        width = 0.35
        
        ax1 = fig.add_subplot(111)
        
        # Left axis (LCOE bars)
        bar_lcoe = ax1.bar(x - width/2, lcoes, width, label='LCOE', color='#1f538d')
        ax1.set_ylabel(ylabel_lcoe, color='#1f538d', fontweight="bold")
        ax1.tick_params(axis='y', labelcolor='#1f538d')
        
        # Right axis (NPC bars)
        ax2 = ax1.twinx()
        bar_npc = ax2.bar(x + width/2, npcs, width, label='NPC', color='#2ca52c')
        ax2.set_ylabel(ylabel_npc, color='#2ca52c', fontweight="bold")
        ax2.tick_params(axis='y', labelcolor='#2ca52c')
        
        # Formatting
        ax1.set_title(chart_title, fontsize=11, fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(names, rotation=15, ha="right")
        ax1.grid(True, linestyle=":", alpha=0.5)
        
        # Single consolidated legend
        bars = [bar_lcoe, bar_npc]
        labels = [b.get_label() for b in bars]
        ax1.legend(bars, labels, loc='upper left', fontsize=9)
        
        self.scenario_canvas.draw()

    def build_tab_help(self):
        """Builds a beautiful, scrollable Help & Documentation tab."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=0) # Title
        frame.grid_rowconfigure(1, weight=1) # Scrollable Content
        frame.grid_columnconfigure(0, weight=1)
        
        # Tab title
        title = ctk.CTkLabel(
            frame, 
            text=self.get_text("tab5_title"), 
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor=self.get_anchor()
        )
        title.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        
        # Scrollable Container
        scroller = ctk.CTkScrollableFrame(frame)
        scroller.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")
        scroller.grid_columnconfigure(0, weight=1)
        
        # Card 1: Project context & clean energy
        card_context = ctk.CTkFrame(scroller, corner_radius=12)
        card_context.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        card_context.grid_columnconfigure(0, weight=1)
        
        lbl_ctx_title = ctk.CTkLabel(
            card_context,
            text=self.get_text("doc_project_context_title"),
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor=self.get_anchor()
        )
        lbl_ctx_title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        
        lbl_ctx_text = ctk.CTkLabel(
            card_context,
            text=self.get_text("doc_project_context_text"),
            justify="left" if self.current_language != "ar" else "right",
            wraplength=900,
            font=ctk.CTkFont(size=13),
            anchor=self.get_anchor()
        )
        lbl_ctx_text.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        
        # Card 2: Technical terms defined: LOLP, LCOE, NPC, SOH
        card_terms = ctk.CTkFrame(scroller, corner_radius=12)
        card_terms.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        card_terms.grid_columnconfigure(0, weight=1)
        
        lbl_terms_title = ctk.CTkLabel(
            card_terms,
            text=self.get_text("doc_terms_title"),
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor=self.get_anchor()
        )
        lbl_terms_title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        
        lbl_terms_text = ctk.CTkLabel(
            card_terms,
            text=self.get_text("doc_terms_text"),
            justify="left" if self.current_language != "ar" else "right",
            wraplength=900,
            font=ctk.CTkFont(size=13),
            anchor=self.get_anchor()
        )
        lbl_terms_text.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        
        # Card 3: System models summary
        card_models = ctk.CTkFrame(scroller, corner_radius=12)
        card_models.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        card_models.grid_columnconfigure(0, weight=1)
        
        lbl_models_title = ctk.CTkLabel(
            card_models,
            text=self.get_text("doc_models_title"),
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor=self.get_anchor()
        )
        lbl_models_title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        
        lbl_models_text = ctk.CTkLabel(
            card_models,
            text=self.get_text("doc_models_text"),
            justify="left" if self.current_language != "ar" else "right",
            wraplength=900,
            font=ctk.CTkFont(size=13),
            anchor=self.get_anchor()
        )
        lbl_models_text.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        
        # Card 4: Genetic Algorithm
        card_ga = ctk.CTkFrame(scroller, corner_radius=12)
        card_ga.grid(row=3, column=0, padx=15, pady=10, sticky="ew")
        card_ga.grid_columnconfigure(0, weight=1)
        
        lbl_ga_title = ctk.CTkLabel(
            card_ga,
            text=self.get_text("doc_ga_title"),
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor=self.get_anchor()
        )
        lbl_ga_title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        
        lbl_ga_text = ctk.CTkLabel(
            card_ga,
            text=self.get_text("doc_ga_text"),
            justify="left" if self.current_language != "ar" else "right",
            wraplength=900,
            font=ctk.CTkFont(size=13),
            anchor=self.get_anchor()
        )
        lbl_ga_text.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        
        # Card 5: Community Parameters Impact
        card_comm = ctk.CTkFrame(scroller, corner_radius=12)
        card_comm.grid(row=4, column=0, padx=15, pady=10, sticky="ew")
        card_comm.grid_columnconfigure(0, weight=1)
        
        lbl_comm_title = ctk.CTkLabel(
            card_comm,
            text=self.get_text("doc_community_title"),
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor=self.get_anchor()
        )
        lbl_comm_title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        
        lbl_comm_text = ctk.CTkLabel(
            card_comm,
            text=self.get_text("doc_community_text"),
            justify="left" if self.current_language != "ar" else "right",
            wraplength=900,
            font=ctk.CTkFont(size=13),
            anchor=self.get_anchor()
        )
        lbl_comm_text.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        
        # Card 6: Restart tutorial button
        card_action = ctk.CTkFrame(scroller, corner_radius=12, fg_color="transparent")
        card_action.grid(row=5, column=0, padx=15, pady=20, sticky="ew")
        card_action.grid_columnconfigure(0, weight=1)
        
        restart_btn = ctk.CTkButton(
            card_action,
            text=self.get_text("restart_tutorial_btn"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.restart_tutorial
        )
        restart_btn.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        return frame

    def prompt_first_time_tutorial(self):
        """Checks if tutorial has been completed. If not, prompts the user."""
        tut_done_file = os.path.join(project_root, ".tutorial_done")
        if not os.path.exists(tut_done_file):
            # Render and display the main application window first
            self.update_idletasks()
            self.update()
            
            confirm = mb.askyesno(
                self.get_text("first_launch_title"),
                self.get_text("first_launch_question")
            )
            if confirm:
                self.start_interactive_tutorial()
            else:
                self.on_tutorial_cancelled()

    def start_interactive_tutorial(self):
        """Launches the step-by-step floating tutorial dialog."""
        from gui.tutorial import TutorialDialog
        
        steps = [
            {
                "tab": "Données d'Entrée",
                "widget_attr": None,
                "title_key": "tut_step0_title",
                "desc_key": "tut_step0_desc",
            },
            {
                "tab": "Données d'Entrée",
                "widget_attr": "input_container",
                "title_key": "tut_step1_title",
                "desc_key": "tut_step1_desc",
                "setup_func": lambda app: app.input_segmented_btn.set(app.get_text("seg_manual")) or app.on_input_segment_changed(app.get_text("seg_manual")),
            },
            {
                "tab": "Données d'Entrée",
                "widget_attr": "fetch_nasa_btn",
                "title_key": "tut_step2_title",
                "desc_key": "tut_step2_desc",
                "setup_func": lambda app: app.input_segmented_btn.set(app.get_text("seg_geoloc")) or app.on_input_segment_changed(app.get_text("seg_geoloc")),
            },
            {
                "tab": "Simulation & Optimisation",
                "widget_attr": "lolp_max_slider",
                "title_key": "tut_step3_title",
                "desc_key": "tut_step3_desc",
            },
            {
                "tab": "Simulation & Optimisation",
                "widget_attr": "run_opt_btn",
                "title_key": "tut_step4_title",
                "desc_key": "tut_step4_desc",
            },
            {
                "tab": "Résultats & Graphiques",
                "widget_attr": "plot_hourly",
                "title_key": "tut_step5_title",
                "desc_key": "tut_step5_desc",
            },
            {
                "tab": "Comparatif de Scénarios",
                "widget_attr": "scenario_name_entry",
                "title_key": "tut_step6_title",
                "desc_key": "tut_step6_desc",
            }
        ]
        
        # Instantiate and show the dialog
        TutorialDialog(self, steps)

    def on_tutorial_finished(self):
        """Callback when the user finishes all tutorial steps."""
        tut_done_file = os.path.join(project_root, ".tutorial_done")
        with open(tut_done_file, "w", encoding="utf-8") as f:
            f.write("done")
        logger.info("Interactive tutorial completed successfully.")

    def on_tutorial_cancelled(self):
        """Callback when the user skips or closes the tutorial dialog."""
        tut_done_file = os.path.join(project_root, ".tutorial_done")
        with open(tut_done_file, "w", encoding="utf-8") as f:
            f.write("cancelled")
        logger.info("Interactive tutorial cancelled/skipped by user.")

    def restart_tutorial(self):
        """Deletes the local .tutorial_done file and forces tutorial relaunch."""
        tut_done_file = os.path.join(project_root, ".tutorial_done")
        if os.path.exists(tut_done_file):
            try:
                os.remove(tut_done_file)
            except Exception as e:
                logger.error(f"Failed to delete {tut_done_file}: {e}")
        self.start_interactive_tutorial()


if __name__ == "__main__":
    app = Application()
    app.mainloop()
