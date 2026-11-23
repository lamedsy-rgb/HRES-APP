import os
import json
import math
import logging
import numpy as np
import pandas as pd
import requests

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NASAWeatherDataHandler:
    """
    Handler for retrieving hourly meteorological data (solar irradiance, temperature, wind speed)
    for a full year (8760 hours) from NASA POWER hourly API.
    Caches responses locally to avoid redundant API hits.
    Falls back to a scientifically realistic synthetic generator if API is offline.
    """
    def __init__(self, cache_dir: str = None):
        """
        Initializes the weather data handler.
        
        Args:
            cache_dir (str): Directory for local JSON caches. Defaults to 'cache/' next to this file.
        """
        if cache_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.cache_dir = os.path.join(current_dir, 'cache')
        else:
            self.cache_dir = cache_dir
        
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_weather_data(self, lat: float, lon: float, year: int) -> pd.DataFrame:
        """
        Retrieves 8760 hours of meteorological data for the given coordinates and year.
        Tries to load from cache, then NASA POWER API, then falls back to synthetic data.
        
        Args:
            lat (float): Latitude in degrees.
            lon (float): Longitude in degrees.
            year (int): Year (e.g. 2023).
            
        Returns:
            pd.DataFrame: DataFrame containing solar_irradiance (kW/m2), temperature (C), and wind_speed (m/s).
        """
        # Format filename to be safe and unique
        cache_filename = f"weather_lat_{lat:.4f}_lon_{lon:.4f}_year_{year}.json"
        cache_filepath = os.path.join(self.cache_dir, cache_filename)
        
        # Check cache
        if os.path.exists(cache_filepath):
            logger.info(f"Loading weather data from cache: {cache_filepath}")
            try:
                with open(cache_filepath, 'r') as f:
                    cached_data = json.load(f)
                return self._parse_api_json(cached_data, year)
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_filepath}: {e}. Querying API...")

        # If not cached, attempt to fetch from NASA POWER API
        # Parameters requested:
        # ALLSKY_SFC_SW_DWN (GHI in Wh/m2)
        # T2M (2m Temperature in C)
        # WS10M (10m Wind Speed in m/s)
        url = (
            f"https://power.larc.nasa.gov/api/temporal/hourly/point"
            f"?parameters=ALLSKY_SFC_SW_DWN,T2M,WS10M"
            f"&community=RE&longitude={lon}&latitude={lat}"
            f"&start={year}0101&end={year}1231&format=JSON"
        )
        
        logger.info(f"Fetching hourly weather data from NASA POWER API: {url}")
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data_json = response.json()
                # Verify that required parameters are present in the response
                properties = data_json.get('properties', {})
                parameter_data = properties.get('parameter', {})
                if parameter_data:
                    # Save to cache
                    with open(cache_filepath, 'w') as f:
                        json.dump(data_json, f, indent=2)
                    logger.info(f"Successfully cached weather data to {cache_filepath}")
                    return self._parse_api_json(data_json, year)
                else:
                    raise ValueError("API response did not contain expected parameter data.")
            else:
                logger.error(f"NASA POWER API returned status code {response.status_code}: {response.text}")
                raise RuntimeError(f"API Error {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Error fetching data from NASA POWER API: {e}. Falling back to synthetic weather generation.")
            return self.generate_synthetic_weather(lat, year)

    def _parse_api_json(self, data_json: dict, year: int) -> pd.DataFrame:
        """
        Parses NASA POWER JSON response into a clean 8760-hour DataFrame.
        """
        properties = data_json.get('properties', {})
        parameter_data = properties.get('parameter', {})
        
        # Determine the keys for solar, temperature, wind speed
        solar_key = None
        temp_key = None
        wind_key = None
        
        for k in parameter_data.keys():
            if k in ['ALLSKY_SFC_SW_DWN', 'ALLSKY_SND_DEC'] or 'ALLSKY' in k or 'SW_DWN' in k:
                solar_key = k
            if k == 'T2M' or 'TEMP' in k:
                temp_key = k
            if k in ['WS10M', 'WS50M'] or 'WS' in k or 'WIND' in k:
                wind_key = k

        # If keys are missing, map dynamically
        if not solar_key and parameter_data.keys():
            solar_key = list(parameter_data.keys())[0]
        if not temp_key and len(parameter_data.keys()) > 1:
            temp_key = list(parameter_data.keys())[1]
        if not wind_key and len(parameter_data.keys()) > 2:
            wind_key = list(parameter_data.keys())[2]

        if not solar_key or not temp_key or not wind_key:
            raise ValueError("Could not resolve parameters in the JSON data.")

        solar_raw = parameter_data[solar_key]
        temp_raw = parameter_data[temp_key]
        wind_raw = parameter_data[wind_key]
        
        # Get timestamps and align
        timestamps = list(solar_raw.keys())
        
        # Convert timestamps from 'YYYYMMDDHH' to datetime
        datetime_idx = pd.to_datetime(timestamps, format='%Y%m%d%H')
        
        df = pd.DataFrame({
            'solar_irradiance': [solar_raw[t] for t in timestamps],
            'temperature': [temp_raw[t] for t in timestamps],
            'wind_speed': [wind_raw[t] for t in timestamps]
        }, index=datetime_idx)
        
        # Clean fill_value / invalid values BEFORE unit conversion (NASA uses -999.0 for missing data)
        fill_val = data_json.get('header', {}).get('fill_value', -999.0)
        df[df == fill_val] = np.nan
        df = df.ffill().bfill()  # simple forward/backward fill for missing hours

        # NASA hourly irradiance ALLSKY_SFC_SW_DWN is in Wh/m^2.
        # To convert to kW/m^2 for the hourly interval: Wh/m^2 / 1000 = kW/m^2
        df['solar_irradiance'] = df['solar_irradiance'] / 1000.0
        
        # Ensure values are physically bound
        df['solar_irradiance'] = df['solar_irradiance'].clip(lower=0.0)
        df['wind_speed'] = df['wind_speed'].clip(lower=0.0)
        
        # Ensure exactly 8760 hours (drop Feb 29 if leap year)
        df = df[~((df.index.month == 2) & (df.index.day == 29))]
        
        if len(df) != 8760:
            logger.warning(f"Parsed DataFrame has {len(df)} rows instead of 8760. Re-indexing to standard 8760 profile.")
            standard_idx = pd.date_range(start=f"{year}-01-01 00:00:00", end=f"{year}-12-31 23:00:00", freq='h')
            # Drop Feb 29 from standard index to keep it exactly 8760
            standard_idx = standard_idx[~((standard_idx.month == 2) & (standard_idx.day == 29))]
            df = df.reindex(standard_idx).ffill().bfill()
            
        return df

    def generate_synthetic_weather(self, lat: float, year: int) -> pd.DataFrame:
        """
        Generates 8760 hours of synthetic meteorological data based on simple physical models.
        
        Args:
            lat (float): Latitude in degrees (determines seasonal shift and temperature profiles).
            year (int): The target year.
            
        Returns:
            pd.DataFrame: 8760 hourly rows.
        """
        logger.info(f"Generating synthetic weather data for lat={lat}, year={year}...")
        
        # Create standard index
        start_date = f"{year}-01-01 00:00:00"
        end_date = f"{year}-12-31 23:00:00"
        idx = pd.date_range(start=start_date, end=end_date, freq='h')
        
        # Drop Feb 29 to ensure exactly 8760 hours
        idx = idx[~((idx.month == 2) & (idx.day == 29))]
        
        N = len(idx)
        solar = np.zeros(N)
        temp = np.zeros(N)
        wind = np.zeros(N)
        
        # Set random seed for reproducibility
        np.random.seed(42 + int(abs(lat)))
        
        # Latitude influence parameters
        is_northern = lat >= 0
        lat_abs = abs(lat)
        
        # Mean annual temperature and seasonal swings
        mean_temp = 26.0 - 0.25 * lat_abs
        temp_amplitude = 2.0 + 0.3 * lat_abs
        temp_diurnal_amp = 4.0 + 0.1 * lat_abs
        
        # Solar peak parameter
        base_peak_solar = 0.85 # kW/m2
        
        # Wind Weibull parameters
        mean_wind = 4.0 + 0.05 * lat_abs
        weibull_shape = 2.0
        weibull_scale = mean_wind / math.gamma(1.0 + 1.0 / weibull_shape)
        
        # Generate daily cloud/clear factors (so some days are clear, others overcast)
        # We model this using a low-frequency wave plus noise to simulate weather systems
        days = N // 24
        daily_clear_sky = 0.75 + 0.2 * np.sin(2 * np.pi * np.arange(days) / 10) + np.random.uniform(-0.15, 0.15, days)
        daily_clear_sky = np.clip(daily_clear_sky, 0.15, 1.0)
        
        # Wind baseline AR(1) initialization
        current_wind = mean_wind
        
        for h in range(N):
            day_of_year = h // 24
            hour_of_day = h % 24
            
            # Solar Irradiance
            # Diurnal sine wave peaking at hour 12 (noon) and zero at night (6:00 to 18:00)
            solar_diurnal = max(0.0, np.sin(np.pi * (hour_of_day - 6) / 12))
            
            # Seasonal variation of daylight/solar intensity
            # Northern hemisphere peaks in June (doy ~172), Southern peaks in Dec (doy ~355)
            peak_day = 172 if is_northern else 355
            seasonal_solar = 1.0 + 0.15 * np.cos(2 * np.pi * (day_of_year - peak_day) / 365)
            
            clear_sky_factor = daily_clear_sky[day_of_year]
            # Hourly variation within the day (clouds passing by)
            hourly_noise = np.random.uniform(0.85, 1.0) if solar_diurnal > 0 else 0.0
            
            solar[h] = solar_diurnal * base_peak_solar * seasonal_solar * clear_sky_factor * hourly_noise
            
            # Temperature
            # Diurnal temperature peaks around hour 15 (3 PM)
            temp_diurnal = np.cos(2 * np.pi * (hour_of_day - 15) / 24)
            # Seasonal temperature peaks in July/Jan
            peak_temp_day = 197 if is_northern else 15
            seasonal_temp = mean_temp + temp_amplitude * np.cos(2 * np.pi * (day_of_year - peak_temp_day) / 365)
            
            # Add daily weather front variation and minor hourly noise
            daily_weather_var = 1.5 * np.sin(2 * np.pi * day_of_year / 7)
            hourly_temp_noise = np.random.normal(0, 0.3)
            
            temp[h] = seasonal_temp + temp_diurnal_amp * temp_diurnal + daily_weather_var + hourly_temp_noise
            
            # Wind Speed
            # Autoregressive wind speed with Weibull noise
            # Diurnal wind speed peaks around 15:00 due to convection
            wind_diurnal = 1.0 + 0.12 * np.cos(2 * np.pi * (hour_of_day - 15) / 24)
            
            # Draw sample from Weibull distribution
            wind_sample = weibull_scale * np.random.weibull(weibull_shape) * wind_diurnal
            
            # AR(1) smoothing to represent physical inertia of air masses
            current_wind = 0.8 * current_wind + 0.2 * wind_sample
            wind[h] = current_wind
            
        df = pd.DataFrame({
            'solar_irradiance': solar,
            'temperature': temp,
            'wind_speed': wind
        }, index=idx)
        
        # Ensure physical boundaries
        df['solar_irradiance'] = df['solar_irradiance'].clip(lower=0.0)
        df['wind_speed'] = df['wind_speed'].clip(lower=0.0)
        
        return df
