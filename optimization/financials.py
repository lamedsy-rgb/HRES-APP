import math
from typing import Dict, Any, Tuple

DEFAULT_COST_PARAMS = {
    # PV costs and lifetime
    "pv_capex": 1000.0,            # Capital cost ($/kW)
    "pv_opex": 15.0,               # O&M cost ($/kW/year)
    "pv_replacement": 800.0,       # Replacement cost ($/kW)
    "pv_lifetime": 25,             # Technical lifetime (years)
    
    # Wind costs and lifetime
    "wind_capex": 1600.0,          # Capital cost ($/kW)
    "wind_opex": 40.0,             # O&M cost ($/kW/year)
    "wind_replacement": 1200.0,    # Replacement cost ($/kW)
    "wind_lifetime": 20,           # Technical lifetime (years)
    
    # Battery costs and lifetime
    "battery_capex": 300.0,        # Capital cost ($/kWh)
    "battery_opex": 10.0,          # O&M cost ($/kWh/year)
    "battery_replacement": 250.0,  # Replacement cost ($/kWh)
    "battery_calendar_lifetime": 10.0, # Calendar lifetime (years)
    
    # Diesel costs and lifetime
    "diesel_capex": 400.0,         # Capital cost ($/kW)
    "diesel_opex": 20.0,           # O&M cost ($/kW/year)
    "diesel_replacement": 300.0,   # Replacement cost ($/kW)
    "diesel_lifetime_hours": 15000.0, # Engine lifetime operating hours
    
    # Fuel cost
    "diesel_fuel_price": 1.2,      # Diesel price ($/L)
    
    # Financial assumptions
    "discount_rate": 0.08,         # Discount rate (decimal)
    "project_lifetime": 25         # Project lifetime (years)
}

def calculate_component_replacements_and_salvage(
    capacity: float,
    capex_rate: float,
    replacement_rate: float,
    component_lifetime: float,
    project_lifetime: int,
    discount_rate: float
) -> Tuple[float, float, list]:
    """
    Calculates the discounted replacement cost and discounted salvage value of a component.
    
    Parameters:
        capacity (float): Capacity of the component (kW or kWh).
        capex_rate (float): Capital cost rate ($/kW or $/kWh).
        replacement_rate (float): Replacement cost rate ($/kW or $/kWh).
        component_lifetime (float): Technical/operational lifetime of the component in years.
        project_lifetime (int): Project lifetime in years.
        discount_rate (float): Discount rate.
        
    Returns:
        Tuple[float, float, list]: 
            - discounted_replacement_cost ($)
            - discounted_salvage_value ($) (at year project_lifetime)
            - list of replacement events (dict with year, cost, discounted_cost)
    """
    if capacity <= 0 or component_lifetime <= 0 or component_lifetime == float('inf') or math.isnan(component_lifetime):
        return 0.0, 0.0, []
        
    discounted_replacement_cost = 0.0
    replacement_events = []
    
    total_replacement_cost = capacity * replacement_rate
    initial_cost = capacity * capex_rate
    
    # Calculate replacement years
    i = 1
    while True:
        rep_year = int(round(i * component_lifetime))
        if rep_year >= project_lifetime:
            break
        if rep_year > 0:
            discounted_cost = total_replacement_cost / ((1.0 + discount_rate) ** rep_year)
            discounted_replacement_cost += discounted_cost
            replacement_events.append({
                "index": i,
                "year": rep_year,
                "cost": total_replacement_cost,
                "discounted_cost": discounted_cost
            })
        i += 1
        
    # Calculate Salvage Value at the end of project lifetime
    num_replacements = len(replacement_events)
    if num_replacements > 0:
        last_installation_year = int(round(num_replacements * component_lifetime))
        base_cost = total_replacement_cost
    else:
        last_installation_year = 0
        base_cost = initial_cost
        
    age_at_end = project_lifetime - last_installation_year
    remaining_lifetime = component_lifetime - age_at_end
    
    salvage_val = 0.0
    discounted_salvage_val = 0.0
    
    if remaining_lifetime > 0:
        # Linear depreciation
        salvage_val = base_cost * (remaining_lifetime / component_lifetime)
        discounted_salvage_val = salvage_val / ((1.0 + discount_rate) ** project_lifetime)
        
    return discounted_replacement_cost, discounted_salvage_val, replacement_events

def calculate_npc(
    pv_capacity: float,
    wind_capacity: float,
    battery_capacity: float,
    diesel_capacity: float,
    cost_params: Dict[str, Any],
    annual_diesel_operating_hours: float,
    annual_fuel_consumption: float,
    annual_battery_degradation_fraction: float,
) -> Dict[str, Any]:
    """
    Calculates the Net Present Cost (NPC) and breaks down all cost components.
    
    Parameters:
        pv_capacity (float): PV capacity in kW.
        wind_capacity (float): Wind capacity in kW.
        battery_capacity (float): Battery capacity in kWh.
        diesel_capacity (float): Diesel capacity in kW.
        cost_params (Dict[str, Any]): Cost parameters to override defaults.
        annual_diesel_operating_hours (float): Annual operating hours of the diesel generator.
        annual_fuel_consumption (float): Annual fuel consumption of the diesel generator in liters.
        annual_battery_degradation_fraction (float): SOH degradation of the battery per year (0.0 to 1.0).
        
    Returns:
        Dict[str, Any]: Detailed breakdown of the HRES Net Present Cost.
    """
    # Merge input cost parameters with defaults
    p = {**DEFAULT_COST_PARAMS, **cost_params}
    
    project_lifetime = int(p["project_lifetime"])
    discount_rate = float(p["discount_rate"])
    
    # 1. Initial Capital Cost (CAPEX)
    pv_cap = pv_capacity * p["pv_capex"]
    wind_cap = wind_capacity * p["wind_capex"]
    battery_cap = battery_capacity * p["battery_capex"]
    diesel_cap = diesel_capacity * p["diesel_capex"]
    total_capital_cost = pv_cap + wind_cap + battery_cap + diesel_cap
    
    # 2. Annual O&M Cost (OPEX)
    pv_om = pv_capacity * p["pv_opex"]
    wind_om = wind_capacity * p["wind_opex"]
    battery_om = battery_capacity * p["battery_opex"]
    diesel_om = diesel_capacity * p["diesel_opex"]
    
    annual_fuel_cost = annual_fuel_consumption * p["diesel_fuel_price"]
    
    annual_om = pv_om + wind_om + battery_om + diesel_om + annual_fuel_cost
    
    # Discounted O&M Cost
    # O&M is assumed constant over the project lifetime and discounted to year 0
    if discount_rate == 0:
        discount_factor = float(project_lifetime)
    else:
        discount_factor = sum(1.0 / ((1.0 + discount_rate) ** t) for t in range(1, project_lifetime + 1))
        
    total_discounted_om = annual_om * discount_factor
    
    # 3. Replacement and Salvage Costs
    # Battery Lifetime Calculation
    if annual_battery_degradation_fraction > 0:
        battery_lifetime = min(p["battery_calendar_lifetime"], 1.0 / annual_battery_degradation_fraction)
    else:
        battery_lifetime = p["battery_calendar_lifetime"]
        
    # Diesel Generator Lifetime Calculation
    if annual_diesel_operating_hours > 0:
        diesel_lifetime = p["diesel_lifetime_hours"] / annual_diesel_operating_hours
    else:
        diesel_lifetime = float('inf')
        
    # PV and Wind Lifetime
    pv_lifetime = p["pv_lifetime"]
    wind_lifetime = p["wind_lifetime"]
    
    # Calculate replacements and salvage for each component
    pv_rep, pv_salvage, pv_rep_events = calculate_component_replacements_and_salvage(
        pv_capacity, p["pv_capex"], p["pv_replacement"], pv_lifetime, project_lifetime, discount_rate
    )
    
    wind_rep, wind_salvage, wind_rep_events = calculate_component_replacements_and_salvage(
        wind_capacity, p["wind_capex"], p["wind_replacement"], wind_lifetime, project_lifetime, discount_rate
    )
    
    bat_rep, bat_salvage, bat_rep_events = calculate_component_replacements_and_salvage(
        battery_capacity, p["battery_capex"], p["battery_replacement"], battery_lifetime, project_lifetime, discount_rate
    )
    
    diesel_rep, diesel_salvage, diesel_rep_events = calculate_component_replacements_and_salvage(
        diesel_capacity, p["diesel_capex"], p["diesel_replacement"], diesel_lifetime, project_lifetime, discount_rate
    )
    
    total_discounted_replacement = pv_rep + wind_rep + bat_rep + diesel_rep
    total_discounted_salvage = pv_salvage + wind_salvage + bat_salvage + diesel_salvage
    
    # Total NPC
    total_npc = total_capital_cost + total_discounted_om + total_discounted_replacement - total_discounted_salvage
    
    return {
        "npc": total_npc,
        "capital_cost": total_capital_cost,
        "pv_capital": pv_cap,
        "wind_capital": wind_cap,
        "battery_capital": battery_cap,
        "diesel_capital": diesel_cap,
        "annual_om_cost": annual_om,
        "annual_fuel_cost": annual_fuel_cost,
        "discounted_om": total_discounted_om,
        "discounted_replacement": total_discounted_replacement,
        "discounted_salvage": total_discounted_salvage,
        "battery_lifetime_years": battery_lifetime,
        "diesel_lifetime_years": diesel_lifetime,
        "battery_replacements": bat_rep_events,
        "diesel_replacements": diesel_rep_events,
        "battery_salvage": bat_salvage,
        "diesel_salvage": diesel_salvage,
        "pv_salvage": pv_salvage,
        "wind_salvage": wind_salvage,
        "discount_rate": discount_rate,
        "project_lifetime": project_lifetime
    }

def calculate_lcoe(
    pv_capacity: float,
    wind_capacity: float,
    battery_capacity: float,
    diesel_capacity: float,
    cost_params: Dict[str, Any],
    annual_diesel_operating_hours: float,
    annual_fuel_consumption: float,
    annual_battery_degradation_fraction: float,
    total_annual_load_kwh: float,
    annual_unmet_load_kwh: float
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculates the Levelized Cost of Energy (LCOE) for the hybrid system.
    
    Parameters:
        pv_capacity (float): PV capacity in kW.
        wind_capacity (float): Wind capacity in kW.
        battery_capacity (float): Battery capacity in kWh.
        diesel_capacity (float): Diesel capacity in kW.
        cost_params (Dict[str, Any]): Cost parameters.
        annual_diesel_operating_hours (float): Annual operating hours of the diesel generator.
        annual_fuel_consumption (float): Annual fuel consumption in liters.
        annual_battery_degradation_fraction (float): SOH degradation of the battery per year.
        total_annual_load_kwh (float): Total load demand in kWh.
        annual_unmet_load_kwh (float): Annual unmet load in kWh.
        
    Returns:
        Tuple[float, Dict[str, Any]]: (LCOE value in $/kWh, detailed npc_details dictionary)
    """
    npc_details = calculate_npc(
        pv_capacity=pv_capacity,
        wind_capacity=wind_capacity,
        battery_capacity=battery_capacity,
        diesel_capacity=diesel_capacity,
        cost_params=cost_params,
        annual_diesel_operating_hours=annual_diesel_operating_hours,
        annual_fuel_consumption=annual_fuel_consumption,
        annual_battery_degradation_fraction=annual_battery_degradation_fraction
    )
    
    npc = npc_details["npc"]
    d = npc_details["discount_rate"]
    N = npc_details["project_lifetime"]
    
    # Capital Recovery Factor (CRF)
    if d == 0:
        crf = 1.0 / N
    else:
        crf = (d * (1.0 + d)**N) / (((1.0 + d)**N) - 1.0)
        
    annualized_cost = npc * crf
    
    total_annual_served_load = total_annual_load_kwh - annual_unmet_load_kwh
    
    if total_annual_served_load <= 0:
        lcoe = 1e6  # Return high fallback cost if no load served
    else:
        lcoe = annualized_cost / total_annual_served_load
        
    npc_details["crf"] = crf
    npc_details["annualized_cost"] = annualized_cost
    npc_details["total_served_load_kwh"] = total_annual_served_load
    npc_details["lcoe"] = lcoe
    
    return lcoe, npc_details

if __name__ == "__main__":
    print("Testing financials.py cost calculations...")
    
    pv_cap = 60.0
    wind_cap = 30.0
    bat_cap = 100.0
    diesel_cap = 25.0
    
    cost_overrides = {
        "diesel_fuel_price": 1.2,
        "discount_rate": 0.08,
        "project_lifetime": 25
    }
    
    # Simulated annual metrics
    diesel_hours = 1200.0
    fuel_cons = 4500.0
    bat_deg = 0.025
    total_load = 120000.0
    unmet_load = 1000.0
    
    lcoe, details = calculate_lcoe(
        pv_capacity=pv_cap,
        wind_capacity=wind_cap,
        battery_capacity=bat_cap,
        diesel_capacity=diesel_cap,
        cost_params=cost_overrides,
        annual_diesel_operating_hours=diesel_hours,
        annual_fuel_consumption=fuel_cons,
        annual_battery_degradation_fraction=bat_deg,
        total_annual_load_kwh=total_load,
        annual_unmet_load_kwh=unmet_load
    )
    
    print("\n--- Cost Breakdown Results ---")
    print(f"Initial Capital Cost : ${details['capital_cost']:,.2f}")
    print(f"PV Capital Cost      : ${details['pv_capital']:,.2f}")
    print(f"Wind Capital Cost    : ${details['wind_capital']:,.2f}")
    print(f"Battery Capital Cost : ${details['battery_capital']:,.2f}")
    print(f"Diesel Capital Cost  : ${details['diesel_capital']:,.2f}")
    print(f"Annual O&M Cost      : ${details['annual_om_cost']:,.2f}/year")
    print(f"Annual Fuel Cost     : ${details['annual_fuel_cost']:,.2f}/year")
    print(f"Discounted O&M Cost  : ${details['discounted_om']:,.2f}")
    print(f"Discounted Repl. Cost: ${details['discounted_replacement']:,.2f}")
    print(f"Discounted Salvage   : ${details['discounted_salvage']:,.2f}")
    print(f"Net Present Cost (NPC): ${details['npc']:,.2f}")
    print(f"Capital Recovery Fact: {details['crf']:.6f}")
    print(f"Annualized Cost      : ${details['annualized_cost']:,.2f}/year")
    print(f"Served Load          : {details['total_served_load_kwh']:,.2f} kWh/year")
    print(f"LCOE                 : ${lcoe:.4f} / kWh")
    
    assert details["capital_cost"] == 60 * 1000 + 30 * 1600 + 100 * 300 + 25 * 400, "CAPEX calculation error"
    assert details["battery_lifetime_years"] == 10.0, "Battery lifetime min error"
    assert details["diesel_lifetime_years"] == 15000 / 1200, "Diesel lifetime division error"
    
    print("\nBattery Replacements:")
    for r in details["battery_replacements"]:
        print(f"  - Year {r['year']}: Cost ${r['cost']:,.2f} (Discounted: ${r['discounted_cost']:,.2f})")
    
    print("\nDiesel Replacements:")
    for r in details["diesel_replacements"]:
        print(f"  - Year {r['year']}: Cost ${r['cost']:,.2f} (Discounted: ${r['discounted_cost']:,.2f})")
        
    print("\nAll financial tests passed!")
