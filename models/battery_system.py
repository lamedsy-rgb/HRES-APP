import numpy as np
from typing import Dict, Any

class BatterySystem:
    """
    Battery Energy Storage System (BESS) class tracking state of charge (SoC)
    and capacity degradation over time.
    """
    def __init__(
        self,
        capacity: float,
        nominal_voltage: float = 48.0,
        min_soc: float = 0.2,
        max_soc: float = 1.0,
        initial_soc: float = 0.5,
        efficiency_charge: float = 0.95,
        efficiency_discharge: float = 0.95,
        max_charge_rate: float = 0.5,
        max_discharge_rate: float = 0.5,
        self_discharge_rate: float = 0.0001,
        lifetime_cycles: float = 3000.0
    ):
        """
        Initialize the battery system parameters.

        Parameters:
            capacity (float): Nominal/initial battery capacity in kWh.
            nominal_voltage (float): Nominal DC voltage of the battery pack (default 48.0 V).
            min_soc (float): Minimum allowable State of Charge (default 0.2).
            max_soc (float): Maximum allowable State of Charge (default 1.0).
            initial_soc (float): Initial State of Charge (default 0.5).
            efficiency_charge (float): Charging efficiency (default 0.95).
            efficiency_discharge (float): Discharging efficiency (default 0.95).
            max_charge_rate (float): Maximum charging C-rate (default 0.5).
            max_discharge_rate (float): Maximum discharging C-rate (default 0.5).
            self_discharge_rate (float): Self-discharge rate fraction of capacity per hour (default 0.0001).
            lifetime_cycles (float): Lifetime nominal full cycles before capacity drops to zero (default 3000.0).
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive.")
        if not (0.0 <= min_soc < max_soc <= 1.0):
            raise ValueError("SoC limits must satisfy 0.0 <= min_soc < max_soc <= 1.0")
        if not (0.0 <= initial_soc <= 1.0):
            raise ValueError("Initial SoC must be between 0.0 and 1.0")

        self.capacity = capacity  # Initial nominal capacity (kWh)
        self.nominal_voltage = nominal_voltage
        self.min_soc = min_soc
        self.max_soc = max_soc
        self.efficiency_charge = efficiency_charge
        self.efficiency_discharge = efficiency_discharge
        self.max_charge_rate = max_charge_rate  # C-rate (e.g., 0.5C means max power = 0.5 * capacity)
        self.max_discharge_rate = max_discharge_rate  # C-rate
        self.self_discharge_rate = self_discharge_rate
        self.lifetime_cycles = lifetime_cycles

        # State tracking
        self.current_capacity = capacity  # Current degraded capacity limit (kWh)
        self.stored_energy = initial_soc * capacity  # Current stored energy (kWh)
        self.total_throughput = 0.0  # Cumulative energy throughput (kWh)

        # Lifetime throughput limit: lifetime_cycles * capacity (kWh)
        self.lifetime_throughput_limit = lifetime_cycles * capacity

    @property
    def soc(self) -> float:
        """
        Get the current State of Charge (SoC).
        """
        if self.current_capacity <= 0:
            return 0.0
        return self.stored_energy / self.current_capacity

    def apply_self_discharge(self, duration_hr: float) -> float:
        """
        Apply hourly self-discharge to the battery.

        Parameters:
            duration_hr (float): Time step duration in hours.

        Returns:
            float: Energy lost due to self-discharge in kWh.
        """
        loss = self.self_discharge_rate * self.current_capacity * duration_hr
        actual_loss = min(self.stored_energy, loss)
        self.stored_energy = max(0.0, self.stored_energy - actual_loss)
        return actual_loss

    def charge(self, energy_in: float, duration_hr: float) -> float:
        """
        Charge the battery with a given energy input.

        Parameters:
            energy_in (float): Proposed energy input to the battery from the external system (kWh).
            duration_hr (float): Time step duration in hours.

        Returns:
            float: Actual energy accepted by the battery (kWh).
        """
        # Apply self-discharge first
        self.apply_self_discharge(duration_hr)

        # 1. Limit input energy by maximum charge C-rate (Power = C-rate * capacity)
        max_power = self.max_charge_rate * self.current_capacity
        max_energy_c_rate = max_power * duration_hr

        # 2. Limit input energy by the headroom left in the battery
        # Let E_added be the net energy stored. E_added = E_accepted * efficiency_charge.
        # E_added <= (max_soc * current_capacity) - stored_energy
        # E_accepted <= ((max_soc * current_capacity) - stored_energy) / efficiency_charge
        max_stored_addition = max(0.0, (self.max_soc * self.current_capacity) - self.stored_energy)
        max_energy_soc = max_stored_addition / self.efficiency_charge

        # Actual energy accepted by the charging circuitry
        actual_energy_accepted = min(energy_in, max_energy_c_rate, max_energy_soc)
        actual_energy_accepted = max(0.0, actual_energy_accepted)

        # Update stored energy
        self.stored_energy += actual_energy_accepted * self.efficiency_charge
        
        # Safeguard boundaries
        self.stored_energy = min(self.stored_energy, self.max_soc * self.current_capacity)

        # Track throughput (charge throughput is half of total round-trip cycle)
        # We define throughput as cumulative energy added to the battery chemistry
        added_throughput = actual_energy_accepted * self.efficiency_charge
        self.total_throughput += added_throughput

        # Degrade maximum capacity based on throughput
        self._update_degradation()

        return actual_energy_accepted

    def discharge(self, energy_out: float, duration_hr: float) -> float:
        """
        Discharge the battery to meet a given energy demand.

        Parameters:
            energy_out (float): Proposed energy demand from the external system (kWh).
            duration_hr (float): Time step duration in hours.

        Returns:
            float: Actual energy delivered by the battery to the external system (kWh).
        """
        # Apply self-discharge first
        self.apply_self_discharge(duration_hr)

        # 1. Limit output energy by maximum discharge C-rate
        max_power = self.max_discharge_rate * self.current_capacity
        max_energy_c_rate = max_power * duration_hr

        # 2. Limit output energy by the capacity available down to min SoC
        # Let E_removed be the internal energy reduction. E_delivered = E_removed * efficiency_discharge.
        # E_removed <= stored_energy - (min_soc * current_capacity)
        # E_delivered <= (stored_energy - (min_soc * current_capacity)) * efficiency_discharge
        max_stored_extraction = max(0.0, self.stored_energy - (self.min_soc * self.current_capacity))
        max_energy_soc = max_stored_extraction * self.efficiency_discharge

        # Actual energy delivered to the load
        actual_energy_delivered = min(energy_out, max_energy_c_rate, max_energy_soc)
        actual_energy_delivered = max(0.0, actual_energy_delivered)

        # Update stored energy
        self.stored_energy -= (actual_energy_delivered / self.efficiency_discharge)
        
        # Safeguard boundaries
        self.stored_energy = max(self.stored_energy, 0.0)

        # Track throughput (discharge energy contributes to cycle count)
        self.total_throughput += actual_energy_delivered

        # Degrade maximum capacity based on throughput
        self._update_degradation()

        return actual_energy_delivered

    def _update_degradation(self):
        """
        Update the degraded capacity based on cumulative throughput.
        """
        if self.lifetime_throughput_limit > 0:
            # Linear cyclic degradation model
            decay_factor = 1.0 - (self.total_throughput / self.lifetime_throughput_limit)
            self.current_capacity = max(0.0, self.capacity * decay_factor)
            
            # Ensure stored energy does not exceed the degraded max_soc limit
            max_allowed = self.max_soc * self.current_capacity
            if self.stored_energy > max_allowed:
                self.stored_energy = max_allowed

    def get_status(self) -> Dict[str, Any]:
        """
        Return the current state dictionary of the battery.
        """
        return {
            "capacity_nominal_kwh": self.capacity,
            "current_capacity_kwh": self.current_capacity,
            "stored_energy_kwh": self.stored_energy,
            "soc": self.soc,
            "total_throughput_kwh": self.total_throughput,
            "degradation_pct": (1.0 - self.current_capacity / self.capacity) * 100.0 if self.capacity > 0 else 100.0
        }

if __name__ == "__main__":
    print("Testing battery_system.py...")
    # Initialize a battery: 100 kWh, 48V, initial SoC = 0.5 (50 kWh stored)
    bat = BatterySystem(capacity=100.0, nominal_voltage=48.0, initial_soc=0.5)
    
    print(f"Initial State: {bat.get_status()}")
    assert bat.soc == 0.5, "Initial SoC test failed"
    assert bat.stored_energy == 50.0, "Initial stored energy test failed"

    # Test charging: charge 30 kWh over 1 hour
    # Max charge power = 0.5C * 100kW = 50kW -> max energy in 1hr = 50 kWh.
    # 30 kWh is well within limit.
    # Space to max SoC = (1.0 - 0.5) * 100 = 50 kWh stored needed, which requires 50 / 0.95 = 52.63 kWh in.
    # 30 kWh is accepted.
    accepted_charge = bat.charge(30.0, 1.0)
    print(f"Charge action: input 30 kWh -> accepted = {accepted_charge:.4f} kWh (Expected: 30.0000 kWh)")
    print(f"After Charge State: {bat.get_status()}")
    assert accepted_charge == 30.0, "Charge acceptance test failed"
    # Stored energy: 50.0 + 30.0 * 0.95 - self_discharge(0.0001 * 100 * 1)
    # self-discharge = 0.01 kWh. So stored before charge = 49.99 kWh.
    # stored after charge = 49.99 + 28.5 = 78.49 kWh.
    assert abs(bat.stored_energy - 78.49) < 1e-6, f"Stored energy check failed: {bat.stored_energy}"

    # Test discharging: discharge 60 kWh over 1 hour
    # Max discharge power = 0.5C * current_capacity (which is 99.9905 kW after degradation) -> max energy in 1hr = 49.99525 kWh.
    # So discharging 60 kWh should be limited to 49.99525 kWh!
    delivered = bat.discharge(60.0, 1.0)
    print(f"Discharge action: demand 60 kWh -> delivered = {delivered:.4f} kWh (Expected: ~49.9953 kWh due to C-rate and degradation)")
    print(f"After Discharge State: {bat.get_status()}")
    assert abs(delivered - 49.99525) < 1e-5, "C-rate discharge limit failed"

    # Test degradation: Run many high-energy cycles to simulate aging
    print("\nRunning degradation simulation...")
    # Reset battery for clean numbers
    bat_degrade = BatterySystem(capacity=100.0, nominal_voltage=48.0, initial_soc=0.5, lifetime_cycles=100)
    # Total throughput limit = 100 * 100 = 10000 kWh
    
    # Discharge all remaining energy multiple times
    for _ in range(50):
        bat_degrade.charge(100.0, 1.0)
        bat_degrade.discharge(100.0, 1.0)
        
    status = bat_degrade.get_status()
    print(f"After simulated cycles: {status}")
    # Capacity should have degraded significantly
    assert status["current_capacity_kwh"] < 100.0, "Capacity degradation failed to trigger"
    print("All Battery system tests passed successfully!")
