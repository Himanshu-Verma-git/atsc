import traci
from sumo_runner import start_simulation, get_signalized_intersections, close_simulation
from algo_scoot import ScootIntersection
from monitoring_system import MonitoringSystem

def run_scoot():
    print("Starting SCOOT Simulation...")
    start_simulation(run_name="scoot")
    
    tls_ids = get_signalized_intersections()
    managers = {tls: ScootIntersection(tls) for tls in tls_ids}
    
    print(f"Initialized {len(managers)} SCOOT Intersections.")
    
    controlled_edges = set()
    for mgr in managers.values():
        controlled_edges.update(mgr.edges)
        
    monitor = MonitoringSystem("scoot", controlled_edges)
    
    step_length = 1
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        time = traci.simulation.getTime()
        monitor.step(time)
        
        for tls, mgr in managers.items():
            mgr.step(step_length)
            
    close_simulation()
    print("SCOOT Simulation finished.")

if __name__ == "__main__":
    run_scoot()
