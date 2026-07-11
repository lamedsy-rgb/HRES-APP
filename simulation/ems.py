import logging
from typing import Dict, Any, Optional
from models.battery_system import BatterySystem
from models.diesel_system import DieselSystem

logger = logging.getLogger(__name__)

def dispatch_hour(
    pv_power: float,
    wind_power: float,
    load: float,
    battery: Optional[BatterySystem],
    diesel: Optional[DieselSystem],
    duration_hr: float = 1.0
) -> Dict[str, float]:
    """
    Chronological dispatch logic for a single hour of the HRES.
    
    Balances renewable generation, load demand, battery storage, and diesel generation.
    Updates the battery system's internal state (SoC, capacity degradation).
    
    Parameters:
        pv_power (float): PV power generated (kW).
        wind_power (float): Wind power generated (kW).
        load (float): Load demand (kW).
        battery (BatterySystem, optional): Battery system instance.
        diesel (DieselSystem, optional): Diesel system instance.
        duration_hr (float): Time step duration in hours (default 1.0).
        
    Returns:
        Dict[str, float]: Dispatch metrics for the hour containing:
            - pv_power (kW)
            - wind_power (kW)
            - load (kW)
            - net_load (kW)
            - battery_charge (kW)
            - battery_discharge (kW)
            - battery_soc (0.0 to 1.0)
            - diesel_power (kW)
            - diesel_fuel (L)
            - dump_power (kW)
            - unmet_load (kW)
    """
    # 1. Calculate net load
    renewables = pv_power + wind_power
    net_load = load - renewables
    
    # Initialize dispatch outputs
    battery_charge = 0.0
    battery_discharge = 0.0
    diesel_power = 0.0
    diesel_fuel = 0.0
    dump_power = 0.0
    unmet_load = 0.0
    
    # 2. Surplus Renewable Energy (Net Load <= 0)
    if net_load <= 0:
        surplus = abs(net_load)
        if battery is not None and battery.capacity > 0:
            # Charge the battery with the surplus energy
            actual_charge_energy = battery.charge(surplus * duration_hr, duration_hr)
            battery_charge = actual_charge_energy / duration_hr
            dump_power = surplus - battery_charge
        else:
            dump_power = surplus
            
    # 3. Deficit Energy (Net Load > 0)
    else:
        deficit = net_load
        if battery is not None and battery.capacity > 0:
            # Discharge the battery to meet the deficit
            actual_discharge_energy = battery.discharge(deficit * duration_hr, duration_hr)
            battery_discharge = actual_discharge_energy / duration_hr
            remaining_deficit = deficit - battery_discharge
        else:
            remaining_deficit = deficit
            
        # If battery discharge was not enough, run diesel generator
        if remaining_deficit > 0:
            if diesel is not None and diesel.capacity > 0:
                min_load = diesel.min_load_fraction * diesel.capacity
                max_load = diesel.capacity
                
                if remaining_deficit < min_load:
                    # Run generator at minimum load
                    diesel_power = min_load
                    excess_gen = min_load - remaining_deficit
                    
                    # Charge battery with the excess generator power, if possible
                    if battery is not None and battery.capacity > 0:
                        # Temporarily disable self-discharge on the charge call
                        # to avoid double-counting self-discharge in the same hour
                        orig_self_discharge = battery.self_discharge_rate
                        battery.self_discharge_rate = 0.0
                        
                        actual_charge_energy = battery.charge(excess_gen * duration_hr, duration_hr)
                        battery_charge = actual_charge_energy / duration_hr
                        
                        battery.self_discharge_rate = orig_self_discharge
                        dump_power = excess_gen - battery_charge
                    else:
                        dump_power = excess_gen
                        
                elif remaining_deficit <= max_load:
                    # Run generator to match the deficit
                    diesel_power = remaining_deficit
                else:
                    # Run generator at maximum capacity
                    diesel_power = max_load
                    unmet_load = remaining_deficit - max_load
                    
                # Calculate fuel consumption
                diesel_fuel = diesel.calculate_fuel(diesel_power)
            else:
                # No diesel generator available
                unmet_load = remaining_deficit
        else:
            # Battery fully covered the deficit; diesel generator remains OFF
            # But we should still apply self-discharge (wait, discharge() already did that)
            pass
            
    # Get current SoC (or 0.0 if battery is None)
    current_soc = battery.soc if battery is not None else 0.0
    
    return {
        "pv_power": pv_power,
        "wind_power": wind_power,
        "load": load,
        "net_load": net_load,
        "battery_charge": battery_charge,
        "battery_discharge": battery_discharge,
        "battery_soc": current_soc,
        "diesel_power": diesel_power,
        "diesel_fuel": diesel_fuel,
        "dump_power": dump_power,
        "unmet_load": unmet_load
    }

class EMS:
    """
    Wrapper class representing the Energy Management System (EMS) dispatcher.
    """
    def __init__(self, battery: Optional[BatterySystem] = None, diesel: Optional[DieselSystem] = None):
        self.battery = battery
        self.diesel = diesel
        
    def dispatch(
        self,
        pv_power: float,
        wind_power: float,
        load: float,
        duration_hr: float = 1.0
    ) -> Dict[str, float]:
        """
        Dispatch energy for a single hour.
        """
        return dispatch_hour(
            pv_power=pv_power,
            wind_power=wind_power,
            load=load,
            battery=self.battery,
            diesel=self.diesel,
            duration_hr=duration_hr
        )
