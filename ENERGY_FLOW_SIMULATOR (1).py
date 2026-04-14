#!/usr/bin/env python3
"""
Energy Flow Simulator - Complete Version with Enhanced OOP
"""

import math, sys, os
from datetime import datetime
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import numpy as np

# =============================================================================
# UTILITIES
# =============================================================================
def safe_float(prompt, min_val=None, max_val=None):
    while True:
        try:
            v = float(input(prompt).strip())
            if min_val is not None and v < min_val:
                print(f"Value must be >= {min_val}")
                continue
            if max_val is not None and v > max_val:
                print(f"Value must be <= {max_val}")
                continue
            return v
        except Exception as e:
            print(f"Error: {e}")

def safe_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            v = int(input(prompt).strip())
            if min_val is not None and v < min_val:
                print(f"Value must be >= {min_val}")
                continue
            if max_val is not None and v > max_val:
                print(f"Value must be <= {max_val}")
                continue
            return v
        except Exception as e:
            print(f"Error: {e}")

def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def ensure_dir(d):
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)

def mw_to_kw(mw): return mw * 1000.0
def kw_to_mw(kw): return kw / 1000.0

# =============================================================================
# SEGMENT 1: GENERATION SYSTEM
# =============================================================================
class Generator(ABC):
    total_generators = 0  # Class variable
    
    def __init__(self, name, capacity_mw, efficiency=0.9, voltage_kv=11.0):
        self.name = name
        self.capacity_mw = float(capacity_mw)
        self.efficiency = float(efficiency)
        self.voltage_kv = float(voltage_kv)
        self.is_on = True
        Generator.total_generators += 1

    @abstractmethod
    def generate_power(self, requested_mw, **kwargs):
        pass

    # Method overloading simulation
    def generate_power_overloaded(self, *args, **kwargs):
        """Method overloading: handle different parameter patterns"""
        if len(args) == 1 and not kwargs:
            return self.generate_power(args[0])  # Single MW value
        elif len(args) == 2:
            return self.generate_power(args[0], duration_hours=args[1], **kwargs)  # MW + hours
        else:
            return self.generate_power(*args, **kwargs)  # Default

    def turn_off(self): self.is_on = False
    def turn_on(self): self.is_on = True

    # Operator overloading
    def __add__(self, other):
        """Combine generator capacities"""
        if isinstance(other, Generator):
            total_capacity = self.capacity_mw + other.capacity_mw
            avg_efficiency = (self.efficiency + other.efficiency) / 2
            return ThermalPlant(f"{self.name}+{other.name}", total_capacity, avg_efficiency)
        return NotImplemented

    def __str__(self):
        return f"{self.__class__.__name__} {self.name}: {self.capacity_mw}MW"

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}', {self.capacity_mw})"

    # Class method
    @classmethod
    def get_generator_count(cls):
        return cls.total_generators

class ThermalPlant(Generator):
    def generate_power(self, requested_mw, **kwargs):
        if not self.is_on: return {"output_mw": 0.0, "loss_mw": 0.0}
        available = min(self.capacity_mw, requested_mw)
        output = available * self.efficiency
        return {"output_mw": output, "loss_mw": available - output}

class HydroPlant(Generator):
    def generate_power(self, requested_mw, **kwargs):
        if not self.is_on: return {"output_mw": 0.0, "loss_mw": 0.0}
        available = min(self.capacity_mw, requested_mw)
        output = available * max(0.85, self.efficiency)
        return {"output_mw": output, "loss_mw": available - output}

class SolarPlant(Generator):
    def generate_power(self, requested_mw, irradiance=1.0, **kwargs):
        if not self.is_on: return {"output_mw": 0.0, "loss_mw": 0.0}
        available = min(self.capacity_mw * irradiance, requested_mw)
        output = available * max(0.0, self.efficiency * 4.5)
        return {"output_mw": output, "loss_mw": max(0.0, available - output)}

class WindFarm(Generator):
    def generate_power(self, requested_mw, wind=1.0, **kwargs):
        if not self.is_on: return {"output_mw": 0.0, "loss_mw": 0.0}
        available = min(self.capacity_mw * wind, requested_mw)
        output = available * max(0.25, self.efficiency)
        return {"output_mw": output, "loss_mw": max(0.0, available - output)}

class NuclearPlant(Generator):
    def generate_power(self, requested_mw, **kwargs):
        if not self.is_on: return {"output_mw": 0.0, "loss_mw": 0.0}
        available = min(self.capacity_mw, requested_mw)
        output = available * max(0.9, self.efficiency)
        return {"output_mw": output, "loss_mw": available - output}

# =============================================================================
# SEGMENT 2: TRANSMISSION SYSTEM
# =============================================================================
class TransmissionLine:
    def __init__(self, name, length_km, r_per_km, x_per_km, voltage_kv=220.0, capacity_mva=1000.0):
        self.name = name
        self.length_km = float(length_km)
        self.r_per_km = float(r_per_km)
        self.x_per_km = float(x_per_km)
        self.voltage_kv = float(voltage_kv)
        self.capacity_mva = float(capacity_mva)

    def total_resistance(self): 
        return self.r_per_km * self.length_km

    def total_reactance(self):
        return self.x_per_km * self.length_km

    def calc_line_loss_mw(self, power_mw, pf=1.0):
        try:
            I = (power_mw * 1e6) / (math.sqrt(3) * self.voltage_kv * 1e3 * pf)
            R = self.total_resistance()
            return (I ** 2) * R / 1e6
        except:
            return 0.0

    def voltage_drop(self, power_mw, pf=1.0):
        try:
            I = (power_mw * 1e6) / (math.sqrt(3) * self.voltage_kv * 1e3 * pf)
            R = self.total_resistance()
            X = self.total_reactance()
            return I * math.sqrt((R**2 + X**2)) / 1000.0
        except:
            return 0.0

    # Operator overloading
    def __add__(self, other):
        """Combine transmission lines"""
        if isinstance(other, TransmissionLine):
            new_length = self.length_km + other.length_km
            new_r = (self.r_per_km + other.r_per_km) / 2
            new_x = (self.x_per_km + other.x_per_km) / 2
            new_voltage = min(self.voltage_kv, other.voltage_kv)
            new_capacity = min(self.capacity_mva, other.capacity_mva)
            return TransmissionLine(f"{self.name}+{other.name}", new_length, new_r, new_x, new_voltage, new_capacity)
        return NotImplemented

    def __mul__(self, factor):
        """Scale line capacity"""
        if isinstance(factor, (int, float)):
            return TransmissionLine(
                f"{self.name}x{factor}", self.length_km, self.r_per_km,
                self.x_per_km, self.voltage_kv, self.capacity_mva * factor
            )
        return NotImplemented

    def __str__(self):
        return f"Line {self.name}: {self.length_km}km, {self.voltage_kv}kV"

    def transmit(self, power_mw, pf=1.0):
        loss = self.calc_line_loss_mw(power_mw, pf)
        received = max(0.0, power_mw - loss)
        v_drop = self.voltage_drop(power_mw, pf)
        return {"sent_mw": power_mw, "loss_mw": loss, "received_mw": received, "voltage_drop_kv": v_drop}

# =============================================================================
# SEGMENT 3: DISTRIBUTION SYSTEM
# =============================================================================
class DistributionSystem:
    def __init__(self, name, input_voltage_kv=132.0, output_voltage_kv=11.0, transformer_efficiency=0.98):
        self.name = name
        self.input_voltage_kv = float(input_voltage_kv)
        self.output_voltage_kv = float(output_voltage_kv)
        self.transformer_efficiency = float(transformer_efficiency)
        self.feeders = []

    def add_feeder(self, feeder_name, load_mw):
        self.feeders.append({"name": feeder_name, "load_mw": float(load_mw)})

    def step_down(self, power_mw):
        out = power_mw * self.transformer_efficiency
        return {"out_mw": out, "loss_mw": power_mw - out}

    def allocate_loads(self, available_mw):
        total_demand = sum(f["load_mw"] for f in self.feeders)
        if total_demand == 0: return []
        return [{"feeder": f["name"], "allocated_mw": (f["load_mw"] / total_demand) * available_mw} 
                for f in self.feeders]

    def total_demand(self):
        return sum(f["load_mw"] for f in self.feeders)

    def auto_adjust_feeders(self, new_total_demand):
        current_total = self.total_demand()
        if current_total == 0:
            for feeder in self.feeders:
                feeder["load_mw"] = new_total_demand / len(self.feeders)
        else:
            scale = new_total_demand / current_total
            for feeder in self.feeders:
                feeder["load_mw"] *= scale

    def __str__(self):
        return f"Distribution {self.name}: {len(self.feeders)} feeders"

# =============================================================================
# SEGMENT 4: UTILIZATION SYSTEM (CONSUMERS)
# =============================================================================
class Consumer:
    consumer_registry = []
    total_energy_consumed = 0.0  # Class variable
    
    def __init__(self, consumer_id, consumer_type, power_rating_kw, daily_hours):
        self.consumer_id = consumer_id
        self.consumer_type = consumer_type
        self.power_rating_kw = float(power_rating_kw)
        self.daily_hours = float(daily_hours)
        Consumer.consumer_registry.append(self)

    # Property (getter)
    @property
    def daily_energy_kwh(self):
        energy = self.power_rating_kw * self.daily_hours
        Consumer.total_energy_consumed += energy
        return energy

    def peak_power_kw(self):
        return self.power_rating_kw

    # Operator overloading
    def __add__(self, other):
        """Combine consumer loads"""
        if isinstance(other, Consumer):
            return self.power_rating_kw + other.power_rating_kw
        return NotImplemented

    def __radd__(self, other):
        """Support sum() function"""
        if other == 0:
            return self.power_rating_kw
        return self.power_rating_kw + other

    def __str__(self):
        return f"Consumer {self.consumer_id}: {self.power_rating_kw}kW {self.consumer_type}"

    # Class methods
    @classmethod
    def get_total_consumers(cls):
        return len(cls.consumer_registry)

    @classmethod  
    def get_total_demand_kw(cls):
        return sum(c.peak_power_kw() for c in cls.consumer_registry)

    # Static method
    @staticmethod
    def validate_power_rating(power_kw):
        return 0.1 <= power_kw <= 10000

# =============================================================================
# GRID OPERATOR - MANAGES ALL SEGMENTS
# =============================================================================
class GridOperator:
    def __init__(self):
        self.generators = []
        self.lines = []
        self.distributions = []
        self.logs = []
        self.simulation_history = []
        self._setup_default_infrastructure()

    def _setup_default_infrastructure(self):
        self.generators = [
            ThermalPlant("Thermal_A", 500, 0.85), 
            ThermalPlant("Thermal_B", 400, 0.88),
            HydroPlant("Hydro_C", 300, 0.9), 
            SolarPlant("Solar_PV", 200, 0.18),
            WindFarm("Wind_Farm", 150, 0.35), 
            NuclearPlant("Nuclear_D", 800, 0.92)
        ]
        
        self.lines = [
            TransmissionLine("Line_A", 150, 0.05, 0.08, 220, 800),
            TransmissionLine("Line_B", 300, 0.04, 0.06, 400, 1500),
            TransmissionLine("Line_C", 80, 0.06, 0.09, 132, 500)
        ]
        
        dist = DistributionSystem("City_Distribution", 220, 11, 0.985)
        dist.add_feeder("Residential", 50)
        dist.add_feeder("Commercial", 40)
        dist.add_feeder("Industrial", 60)
        dist.add_feeder("Public_Services", 20)
        self.distributions = [dist]

    def total_generation_capacity(self):
        return sum(g.capacity_mw for g in self.generators if g.is_on)

    def auto_adjust_system(self, new_total_demand):
        for dist in self.distributions:
            dist.auto_adjust_feeders(new_total_demand)
        
        current_capacity = self.total_generation_capacity()
        if new_total_demand > current_capacity:
            for gen in sorted(self.generators, key=lambda x: -x.efficiency):
                if not gen.is_on and current_capacity < new_total_demand:
                    gen.turn_on()
                    current_capacity += gen.capacity_mw
                    self.logs.append(f"Auto-activated {gen.name}")
        
        self.logs.append(f"System adjusted for {new_total_demand:.2f} MW")

    def dispatch_merit_order(self, demand_mw, **kwargs):
        remaining = demand_mw
        dispatch = []
        
        for g in sorted(self.generators, key=lambda x: (-x.efficiency, -x.capacity_mw)):
            if remaining <= 0: 
                if g.is_on: g.turn_off()
                continue
                
            if not g.is_on: g.turn_on()
                
            request = min(g.capacity_mw, remaining)
            result = g.generate_power(request, **kwargs)
            dispatch.append({
                "gen": g.name, 
                "requested_mw": request, 
                "supplied_mw": result["output_mw"], 
                "loss_mw": result["loss_mw"]
            })
            remaining -= result["output_mw"]
            
        return {"dispatch": dispatch, "shortfall_mw": max(0.0, remaining)}

    def choose_lines_for_power(self, required_mw):
        used = []
        remaining = required_mw
        
        for L in sorted(self.lines, key=lambda x: (-x.voltage_kv, -x.capacity_mva)):
            if remaining <= 0: break
            can_send = min(remaining, L.capacity_mva * 0.8)
            res = L.transmit(can_send)
            used.append((L, res))
            remaining -= res["sent_mw"]
            
        return used

    def distribute_to_feeders(self, distribution, available_mw):
        step = distribution.step_down(available_mw)
        allocations = distribution.allocate_loads(step["out_mw"])
        return {"transformer": step, "allocations": allocations}

    def system_efficiency_and_losses(self, dispatch_results, line_usages, distribution_reports):
        gen_loss = sum(d["loss_mw"] for d in dispatch_results)
        tx_loss = sum(ru["loss_mw"] for (_, ru) in line_usages)
        dist_loss = sum(d["transformer"]["loss_mw"] for d in distribution_reports)
        
        total_supplied = sum(d["supplied_mw"] for d in dispatch_results)
        total_loss = gen_loss + tx_loss + dist_loss
        efficiency = (total_supplied / (total_supplied + total_loss)) * 100 if (total_supplied + total_loss) > 0 else 0
        
        return {
            "gen_loss_mw": gen_loss, "tx_loss_mw": tx_loss, "dist_loss_mw": dist_loss,
            "total_loss_mw": total_loss, "system_efficiency_pct": efficiency,
            "total_supplied_mw": total_supplied
        }

    def reset_logs(self): 
        self.logs = []

    def __str__(self):
        return f"GridOperator: {len(self.generators)} generators, {len(self.lines)} lines"

# =============================================================================
# REPORTING & VISUALIZATION SYSTEM
# =============================================================================
REPORT_DIR = "reports"
PLOT_DIR = "plots"
ensure_dir(REPORT_DIR); ensure_dir(PLOT_DIR)

def save_report(filename, content_lines):
    try:
        path = os.path.join(REPORT_DIR, filename)
        with open(path, "w") as f:
            f.write("\n".join(content_lines))
        print(f"Report saved: {path}")
    except Exception as e:
        print(f"Error saving report: {e}")

def create_all_plots(grid, dispatch, line_usages, distributions, timestamp_tag):
    plot_files = {}
    
    try:
        active_gens = [g for g in grid.generators if g.is_on]
        if active_gens:
            plt.figure(figsize=(8, 6))
            sizes = [g.capacity_mw for g in active_gens]
            labels = [f"{g.name}\n({g.capacity_mw} MW)" for g in active_gens]
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.title('Generation Capacity Mix')
            plot_files["gen_mix"] = os.path.join(PLOT_DIR, f"gen_mix_{timestamp_tag}.png")
            plt.savefig(plot_files["gen_mix"])
            plt.close()
    except Exception as e:
        print(f"Error in generation plot: {e}")

    try:
        if line_usages:
            plt.figure(figsize=(10, 6))
            time_hours = np.linspace(0, 24, 100)
            total_tx_loss = sum(res["loss_mw"] for _, res in line_usages)
            daily_load = 0.6 + 0.4 * np.sin(2 * np.pi * (time_hours - 6) / 24)
            tx_loss_curve = total_tx_loss * daily_load
            
            plt.plot(time_hours, tx_loss_curve, 'r-', linewidth=3, label='Transmission Loss')
            plt.xlabel('Time of Day (Hours)')
            plt.ylabel('Transmission Loss (MW)')
            plt.title('Transmission Losses Over 24 Hours')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            plot_files["tx_losses"] = os.path.join(PLOT_DIR, f"tx_losses_{timestamp_tag}.png")
            plt.savefig(plot_files["tx_losses"])
            plt.close()
    except Exception as e:
        print(f"Error in transmission plot: {e}")

    try:
        if distributions and distributions[0]["allocations"]:
            plt.figure(figsize=(10, 6))
            allocs = distributions[0]["allocations"]
            feeders = [a["feeder"] for a in allocs]
            allocations = [a["allocated_mw"] for a in allocs]
            
            colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightsalmon']
            bars = plt.bar(feeders, allocations, color=colors[:len(feeders)], alpha=0.7)
            plt.xlabel('Distribution Feeders')
            plt.ylabel('Power Allocated (MW)')
            plt.title('Distribution Feeder Power Allocation')
            
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{height:.2f} MW', ha='center', va='bottom')
            
            plt.tight_layout()
            plot_files["feeder_alloc"] = os.path.join(PLOT_DIR, f"feeder_alloc_{timestamp_tag}.png")
            plt.savefig(plot_files["feeder_alloc"])
            plt.close()
    except Exception as e:
        print(f"Error in distribution plot: {e}")

    try:
        gen_total = sum(d["supplied_mw"] for d in dispatch) * 1000
        tx_loss = sum(res["loss_mw"] for (_, res) in line_usages) * 1000
        dist_loss = sum(r["transformer"]["loss_mw"] for r in distributions) * 1000
        delivered = gen_total - tx_loss - dist_loss

        if tx_loss == 0:
            tx_loss = max(gen_total * 0.02, 100)
        
        categories = ['Generation', 'Tx Loss', 'Dist Loss', 'Delivered']
        values = [gen_total, tx_loss, dist_loss, delivered]
        colors = ['green', 'red', 'orange', 'blue']

        plt.figure(figsize=(12, 6))
        bars = plt.bar(categories, values, color=colors, alpha=0.75)
        plt.ylabel('Power (kW)')
        plt.title('System Energy Flow Overview')
        
        total = gen_total
        for bar, value in zip(bars, values):
            height = bar.get_height()
            percentage = (value / total) * 100 if total > 0 else 0
            plt.text(bar.get_x() + bar.get_width()/2., height + 1000,
                    f'{value/1000:.1f} MW\n({value:.0f} kW)', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plot_files["system_flow"] = os.path.join(PLOT_DIR, f"system_flow_{timestamp_tag}.png")
        plt.savefig(plot_files["system_flow"])
        plt.close()
    except Exception as e:
        print(f"Error in system flow plot: {e}")

    try:
        if Consumer.consumer_registry:
            plt.figure(figsize=(8, 6))
            consumer_types = {}
            for consumer in Consumer.consumer_registry:
                consumer_types[consumer.consumer_type] = consumer_types.get(consumer.consumer_type, 0) + 1
            
            plt.pie(consumer_types.values(), labels=consumer_types.keys(), autopct='%1.1f%%', startangle=90)
            plt.title('Consumer Type Distribution')
            plot_files["consumer_dist"] = os.path.join(PLOT_DIR, f"consumer_dist_{timestamp_tag}.png")
            plt.savefig(plot_files["consumer_dist"])
            plt.close()
    except Exception as e:
        print(f"Error in consumer plot: {e}")

    return plot_files

def generate_report_and_plots(grid, demand_mw, dispatch_summary, line_usages, distribution_reports, stats, ts_tag):
    lines = [
        "=" * 70,
        "ENERGY FLOW SIMULATOR - COMPREHENSIVE REPORT",
        "=" * 70,
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total System Demand: {demand_mw:.2f} MW",
        f"Total Consumers: {Consumer.get_total_consumers()}",
        f"Total Generators: {Generator.get_generator_count()}",
        ""
    ]
    
    lines.extend(["UTILIZATION SEGMENT", "-" * 50])
    total_energy_kwh = 0
    for consumer in Consumer.consumer_registry:
        daily_energy = consumer.daily_energy_kwh
        total_energy_kwh += daily_energy
        lines.append(f"ID: {consumer.consumer_id:15} Type: {consumer.consumer_type:12} "
                    f"Power: {consumer.power_rating_kw:6.1f} kW  Daily Energy: {daily_energy:8.1f} kWh")
    
    lines.extend([
        f"Total Daily Energy: {total_energy_kwh:.1f} kWh",
        f"Peak Power Demand: {Consumer.get_total_demand_kw():.1f} kW",
        ""
    ])
    
    lines.extend(["GENERATION SEGMENT", "-" * 50])
    total_supplied = 0
    for d in dispatch_summary:
        total_supplied += d["supplied_mw"]
        lines.append(f"{d['gen']:15} Supplied: {d['supplied_mw']:6.2f} MW  Loss: {d['loss_mw']:6.4f} MW")
    
    lines.extend(["", "TRANSMISSION SEGMENT", "-" * 50])
    for L, res in line_usages:
        lines.append(f"{L.name:15} Sent: {res['sent_mw']:6.2f} MW  Received: {res['received_mw']:6.2f} MW  Loss: {res['loss_mw']:6.4f} MW")
    
    lines.extend(["", "DISTRIBUTION SEGMENT", "-" * 50])
    for alloc in distribution_reports[0]['allocations']:
        lines.append(f"{alloc['feeder']:20} -> {alloc['allocated_mw']:6.2f} MW")
    
    lines.extend(["", "SYSTEM STATISTICS", "-" * 50])
    lines.extend([
        f"Power Supplied: {stats['total_supplied_mw']:.2f} MW",
        f"System Efficiency: {stats['system_efficiency_pct']:.2f}%",
        f"Total Loss: {stats['total_loss_mw']:.4f} MW",
        f"Power Delivery Ratio: {(stats['total_supplied_mw'] - stats['total_loss_mw']) / stats['total_supplied_mw'] * 100:.2f}%"
    ])
    
    fname = f"report_{ts_tag}.txt"
    save_report(fname, lines)
    plot_files = create_all_plots(grid, dispatch_summary, line_usages, distribution_reports, ts_tag)
    return fname, plot_files

def run_simulation_once(grid, demand_mw, **kwargs):
    grid.reset_logs()
    grid.auto_adjust_system(demand_mw)
    
    try:
        dispatch_res = grid.dispatch_merit_order(demand_mw, **kwargs)
        dispatch_list = dispatch_res["dispatch"]
        line_usages = grid.choose_lines_for_power(sum(d["supplied_mw"] for d in dispatch_list))
        distribution_reports = [grid.distribute_to_feeders(dist, sum(res["received_mw"] for (_, res) in line_usages)) 
                               for dist in grid.distributions]
        stats = grid.system_efficiency_and_losses(dispatch_list, line_usages, distribution_reports)
        
        ts_tag = timestamp()
        grid.simulation_history.append({'demand_mw': demand_mw, 'stats': stats, 'timestamp': ts_tag})
        
        report_file, plot_files = generate_report_and_plots(grid, demand_mw, dispatch_list, line_usages, distribution_reports, stats, ts_tag)
        
        return {
            "dispatch": dispatch_list, "shortfall_mw": dispatch_res["shortfall_mw"],
            "line_usages": line_usages, "distribution_reports": distribution_reports,
            "stats": stats, "report": report_file, "plots": plot_files
        }
    except Exception as e:
        print(f"Error in simulation: {e}")
        return None

# =============================================================================
# MAIN MENU SYSTEM
# =============================================================================
def print_header():
    print("=" * 70)
    print("ENERGY FLOW SIMULATOR - COMPLETE SYSTEM WITH OOP")
    print("Segments: Generation | Transmission | Distribution | Utilization")
    print("=" * 70)

def add_consumer():
    print("\nADD CONSUMER")
    
    try:
        consumer_id = input("Enter consumer ID: ").strip()
        if not consumer_id:
            print("Error: Consumer ID cannot be empty")
            return
            
        print("Select consumer type:")
        print("1. Domestic")
        print("2. Commercial") 
        print("3. Industrial")
        
        type_choice = input("Enter choice (1/2/3): ").strip()
        if type_choice == "1":
            consumer_type = "Domestic"
        elif type_choice == "2":
            consumer_type = "Commercial"
        elif type_choice == "3":
            consumer_type = "Industrial"
        else:
            print("Error: Invalid type selection")
            return
            
        power_rating = safe_float("Enter power rating (kW): ", min_val=0.1)
        daily_hours = safe_float("Enter daily operating hours: ", min_val=0.0, max_val=24.0)
        
        if not Consumer.validate_power_rating(power_rating):
            print("Error: Power rating must be between 0.1 kW and 10000 kW")
            return
            
        consumer = Consumer(consumer_id, consumer_type, power_rating, daily_hours)
        print(f"Consumer added: {consumer}")
              
    except Exception as e:
        print(f"Error: {e}")

def run_simulation(grid):
    if not Consumer.consumer_registry:
        print("Error: No consumers added. Please add consumers first.")
        return
        
    try:
        total_demand_kw = Consumer.get_total_demand_kw()
        total_demand_mw = kw_to_mw(total_demand_kw)
        
        print(f"\nRUNNING COMPLETE SYSTEM SIMULATION")
        print(f"Consumers: {Consumer.get_total_consumers()}")
        print(f"Total Demand: {total_demand_mw:.3f} MW")
        
        irradiance = safe_float("Solar factor [0.0-1.0]: ", 0.0, 1.0) or 1.0
        wind = safe_float("Wind factor [0.0-1.0]: ", 0.0, 1.0) or 1.0
        
        print("Simulating...")
        result = run_simulation_once(grid, total_demand_mw, irradiance=irradiance, wind=wind)
        
        if result:
            print("\nSIMULATION COMPLETED SUCCESSFULLY")
            print("=" * 50)
            print(f"GENERATION: {len(result['dispatch'])} plants")
            print(f"TRANSMISSION: {len(result['line_usages'])} lines") 
            print(f"Efficiency: {result['stats']['system_efficiency_pct']:.2f}%")
            print(f"Total Loss: {result['stats']['total_loss_mw']:.4f} MW")
            print(f"Report: {result['report']}")
            
            if result['plots']:
                print("Plots generated in /plots folder")
                
    except Exception as e:
        print(f"Error: {e}")

def main_menu():
    grid = GridOperator()
    print_header()
    
    while True:
        print("\nMAIN MENU")
        print("1. Add Consumer")
        print("2. Run Simulation") 
        print("3. Exit")
        
        choice = input("Choice (1-3): ").strip()
        
        if choice == "1":
            add_consumer()
        elif choice == "2":
            run_simulation(grid)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nProgram interrupted.")
    except Exception as e:
        print(f"Unexpected error: {e}")