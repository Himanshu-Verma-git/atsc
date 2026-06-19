import traci
import json
import os
from config import SLOT_DURATION, HISTORIC_DATA_FILE, COMMUNICATION_INTERVAL
from sumo_runner import start_simulation, get_signalized_intersections, close_simulation
from intersection_manager import IntersectionManager
from monitoring_system import MonitoringSystem

def run_fuzzy():
    print("Starting Fuzzy ATSC Simulation...")
    start_simulation(run_name="fuzzy", use_gui=True)
    
    historic_data = {}
    if os.path.exists(HISTORIC_DATA_FILE):
        with open(HISTORIC_DATA_FILE, 'r') as f:
            historic_data = json.load(f)
            
    tls_ids = get_signalized_intersections()
    managers = {tls: IntersectionManager(tls) for tls in tls_ids}
    
    print(f"Initialized {len(managers)} Fuzzy Intersection Managers.")
    
    controlled_edges = set()
    for mgr in managers.values():
        controlled_edges.update(mgr.edges)
        
    monitor = MonitoringSystem("fuzzy", controlled_edges)
    
    step_length = 1 # We use 1s steps
    last_comm_time = 0
    shared_info = {}
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        time = traci.simulation.getTime()
        monitor.step(time)
        
        current_slot = int(time // SLOT_DURATION)
        
        # Periodic data sharing
        if time - last_comm_time >= COMMUNICATION_INTERVAL:
            shared_info = {tls: mgr.get_shared_data() for tls, mgr in managers.items()}
            last_comm_time = time
            
        for tls, mgr in managers.items():
            mgr.step(step_length, historic_data, current_slot, shared_info)
            
    close_simulation()
    print("Fuzzy ATSC Simulation finished.")

if __name__ == "__main__":
    run_fuzzy()
