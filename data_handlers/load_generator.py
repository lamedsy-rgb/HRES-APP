import os
import logging
import numpy as np
import pandas as pd

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_synthetic_load(
    households: int,
    school_preset: str,
    clinic_preset: str,
    noise_level: float = 0.1,
    year: int = 2023,
    save_path: str = None
) -> pd.DataFrame:
    """
    Generates an 8760-hour electrical load profile (kW) for a community based on households,
    school, and clinic configurations.
    
    Args:
        households (int): Number of households in the community.
        school_preset (str or float/int): Preset size ('none', 'small', 'medium', 'large') or raw peak kW.
        clinic_preset (str or float/int): Preset size ('none', 'small', 'medium', 'large') or raw base kW.
        noise_level (float): Scale of randomized hourly noise (relative to the load). Defaults to 0.1.
        year (int): Calendar year to generate DatetimeIndex (to align weekdays/weekends). Defaults to 2023.
        save_path (str): Optional path to save the generated profile as a CSV file.
        
    Returns:
        pd.DataFrame: 8760 hourly rows with columns:
                      'household_load', 'school_load', 'clinic_load', 'total_load'.
    """
    logger.info(f"Generating synthetic load for households={households}, school={school_preset}, clinic={clinic_preset}, year={year}...")
    
    # Create hourly datetime index for the entire year
    start_date = f"{year}-01-01 00:00:00"
    end_date = f"{year}-12-31 23:00:00"
    idx = pd.date_range(start=start_date, end=end_date, freq='h')
    
    # Filter out Feb 29 for leap years to guarantee exactly 8760 hours
    idx = idx[~((idx.month == 2) & (idx.day == 29))]
    N = len(idx)
    
    # Ensure reproducibility
    np.random.seed(42 + households)
    
    # ---------------------------------------------
    # 1. Household Load Profile
    # ---------------------------------------------
    household_load = np.zeros(N)
    if households > 0:
        # Standard domestic appliances parameters (per household kW)
        base_h = 0.08      # 24/7 background standby (refrigerators, standby devices)
        morning_peak = 0.18 # breakfast activity, water heating (6:00-8:00)
        evening_peak = 0.45 # cooking, lights, TV, cooling (18:00-22:00)
        
        for h in range(N):
            hour = idx[h].hour
            load = base_h
            
            # Morning peak: 6:00 - 8:00 (inclusive)
            if 6 <= hour <= 8:
                load += morning_peak
            # Evening peak: 18:00 - 22:00 (inclusive)
            elif 18 <= hour <= 22:
                load += evening_peak
                
            household_load[h] = load * households
            
        # Add random variation per hour
        h_noise = np.random.normal(0, noise_level * household_load, N)
        household_load = np.clip(household_load + h_noise, 0.0, None)

    # ---------------------------------------------
    # 2. School Load Profile
    # ---------------------------------------------
    school_load = np.zeros(N)
    
    # Parse school peak capacity
    school_peak = 0.0
    if isinstance(school_preset, (int, float)):
        school_peak = float(school_preset)
    elif isinstance(school_preset, str):
        preset_lower = school_preset.lower()
        if preset_lower == 'small':
            school_peak = 3.0   # small primary school
        elif preset_lower == 'medium':
            school_peak = 12.0  # secondary school with some labs/fans
        elif preset_lower == 'large':
            school_peak = 35.0  # larger boarding school or regional center
        elif preset_lower in ['none', '']:
            school_peak = 0.0
        else:
            try:
                school_peak = float(school_preset)
            except ValueError:
                logger.warning(f"Unknown school preset '{school_preset}', defaulting to 0.0 kW.")
                school_peak = 0.0

    if school_peak > 0:
        for h in range(N):
            dt = idx[h]
            # Zero on weekends (Saturday=5, Sunday=6)
            if dt.dayofweek >= 5:
                continue
            
            # School hours: 8:00 to 16:00 (exclusive of 16:00)
            if 8 <= dt.hour < 16:
                # Bell curve pattern peaking at noon (hour 12)
                # Max value reaches school_peak
                h_frac = (dt.hour - 8) / 8.0  # 0.0 to 1.0
                bell_factor = np.sin(np.pi * h_frac)  # peaks at 0.5 (12:00) with 1.0
                school_load[h] = school_peak * bell_factor
                
        # Add minor random noise
        s_noise = np.random.normal(0, noise_level * school_load, N)
        school_load = np.clip(school_load + s_noise, 0.0, None)

    # ---------------------------------------------
    # 3. Clinic Load Profile
    # ---------------------------------------------
    clinic_load = np.zeros(N)
    
    # Parse clinic base capacity
    clinic_base = 0.0
    clinic_peak_add = 0.0
    
    if isinstance(clinic_preset, (int, float)):
        clinic_base = float(clinic_preset)
        clinic_peak_add = 0.3 * clinic_base  # daytime operations add 30%
    elif isinstance(clinic_preset, str):
        preset_lower = clinic_preset.lower()
        if preset_lower == 'small':
            clinic_base = 1.2      # vaccine refrigerators + lights + basic equipment
            clinic_peak_add = 0.5   # daytime diagnostic tools / sterilization
        elif preset_lower == 'medium':
            clinic_base = 4.0
            clinic_peak_add = 2.0
        elif preset_lower == 'large':
            clinic_base = 12.0
            clinic_peak_add = 6.0
        elif preset_lower in ['none', '']:
            clinic_base = 0.0
        else:
            try:
                clinic_base = float(clinic_preset)
                clinic_peak_add = 0.3 * clinic_base
            except ValueError:
                logger.warning(f"Unknown clinic preset '{clinic_preset}', defaulting to 0.0 kW.")
                clinic_base = 0.0

    if clinic_base > 0:
        for h in range(N):
            hour = idx[h].hour
            load = clinic_base
            
            # Daytime clinic operational fluctuations: 8:00 to 17:00
            if 8 <= hour < 17:
                # Add minor day operational load
                load += clinic_peak_add * np.sin(np.pi * (hour - 8) / 9.0)
                
            clinic_load[h] = load
            
        # Add random fluctuations (continuous medical devices turning on/off)
        c_noise = np.random.normal(0, noise_level * clinic_load, N)
        clinic_load = np.clip(clinic_load + c_noise, 0.0, None)

    # ---------------------------------------------
    # 4. Aggregate & Create DataFrame
    # ---------------------------------------------
    total_load = household_load + school_load + clinic_load
    
    df = pd.DataFrame({
        'household_load': household_load,
        'school_load': school_load,
        'clinic_load': clinic_load,
        'total_load': total_load
    }, index=idx)
    
    if save_path:
        # Create directory path if it doesn't exist
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        df.to_csv(save_path)
        logger.info(f"Successfully saved load profile to {save_path}")
        
    return df
