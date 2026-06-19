import traci
import json
import os
from collections import defaultdict
from config import SLOT_DURATION, HISTORIC_DATA_FILE
from sumo_runner import start_simulation, get_signalized_intersections, close_simulation, get_edge_phases
from monitoring_system import MonitoringSystem

def run_baseline():
    print("Starting Baseline Simulation at Edge Level...")
    start_simulation(run_name="baseline")
    
    tls_ids = get_signalized_intersections()
    
    # Store custom phases and tracking state per intersection
    tls_data = {}
    controlled_edges = set()
    
    for tls in tls_ids:
        edge_phases = get_edge_phases(tls)
        if not edge_phases:
            continue
        
        # Start with the first edge phase
        traci.trafficlight.setRedYellowGreenState(tls, edge_phases[0]['state'])
        
        for ep in edge_phases:
            controlled_edges.add(ep['edge_id'])
            
        tls_data[tls] = {
            'phases': edge_phases,
            'current_idx': 0,
            'time_in_phase': 0,
            'fixed_duration': 30  # 30 seconds fixed green time per edge
        }
        
    print(f"Monitoring {len(controlled_edges)} approach edges across {len(tls_ids)} intersections.")
    
    monitor = MonitoringSystem("baseline", controlled_edges)
    
    # Data structure: edge_id -> list of slots -> {flow, density}
    current_slot = 0
    slot_data = {edge: {"flow_sum": 0.0, "density_sum": 0.0, "steps": 0} for edge in controlled_edges}
    
    historic_data = defaultdict(list)
    step_length = 1
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        time = traci.simulation.getTime()
        monitor.step(time)
        
        # Manage fixed-time round-robin signal control for edge phases
        for tls, data in tls_data.items():
            data['time_in_phase'] += step_length
            if data['time_in_phase'] >= data['fixed_duration']:
                # Move to next phase
                data['current_idx'] = (data['current_idx'] + 1) % len(data['phases'])
                new_state = data['phases'][data['current_idx']]['state']
                traci.trafficlight.setRedYellowGreenState(tls, new_state)
                data['time_in_phase'] = 0
        
        # Check if we moved to a new slot
        new_slot = int(time // SLOT_DURATION)
        if new_slot > current_slot:
            # Save averages for the completed slot
            for edge in controlled_edges:
                steps = slot_data[edge]["steps"]
                if steps > 0:
                    avg_flow = slot_data[edge]["flow_sum"] / steps
                    avg_density = slot_data[edge]["density_sum"] / steps
                else:
                    avg_flow = 0.0
                    avg_density = 0.0
                    
                historic_data[edge].append({
                    "flow": round(avg_flow, 2),
                    "density": round(avg_density, 2)
                })
                # Reset for new slot
                slot_data[edge] = {"flow_sum": 0.0, "density_sum": 0.0, "steps": 0}
            
            current_slot = new_slot
            print(f"Completed time slot {current_slot - 1}. Simulation time: {time}s")
            
        # Collect metric data per edge
        for tls, data in tls_data.items():
            for ep in data['phases']:
                edge = ep['edge_id']
                lanes = ep['lanes']
                
                edge_veh_num = 0
                edge_occupancy_sum = 0
                
                for lane in lanes:
                    try:
                        edge_veh_num += traci.lane.getLastStepVehicleNumber(lane)
                        edge_occupancy_sum += traci.lane.getLastStepOccupancy(lane) * 100.0
                    except traci.exceptions.TraCIException:
                        pass
                
                # Average occupancy across lanes on this edge
                avg_occ = edge_occupancy_sum / len(lanes) if lanes else 0
                
                slot_data[edge]["flow_sum"] += edge_veh_num
                slot_data[edge]["density_sum"] += avg_occ
                slot_data[edge]["steps"] += 1

    # Save any remaining data for the last partial slot
    for edge in controlled_edges:
        steps = slot_data[edge]["steps"]
        if steps > 0:
            avg_flow = slot_data[edge]["flow_sum"] / steps
            avg_density = slot_data[edge]["density_sum"] / steps
            historic_data[edge].append({
                "flow": round(avg_flow, 2),
                "density": round(avg_density, 2)
            })

    with open(HISTORIC_DATA_FILE, 'w') as f:
        json.dump(historic_data, f, indent=4)
        
    close_simulation()
    print(f"Baseline finished. Historic data saved to {HISTORIC_DATA_FILE}")

if __name__ == "__main__":
    run_baseline()
