import traci
from sumo_runner import start_simulation, get_signalized_intersections, close_simulation
from algo_scats import ScatsIntersection
from monitoring_system import MonitoringSystem

def run_scats():
    print("Starting SCATS Simulation...")
    start_simulation(run_name="scats")
    
    tls_ids = get_signalized_intersections()
    managers = {tls: ScatsIntersection(tls) for tls in tls_ids}
    
    print(f"Initialized {len(managers)} SCATS Intersections.")
    
    controlled_edges = set()
    for mgr in managers.values():
        controlled_edges.update(mgr.edges)
        
    monitor = MonitoringSystem("scats", controlled_edges)
    
    step_length = 1
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        time = traci.simulation.getTime()
        monitor.step(time)
        
        for tls, mgr in managers.items():
            mgr.step(step_length)
            
    close_simulation()
    print("SCATS Simulation finished.")

if __name__ == "__main__":
    run_scats()
