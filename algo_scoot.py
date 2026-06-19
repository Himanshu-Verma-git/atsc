import traci
from sumo_runner import get_edge_phases

class ScootIntersection:
    def __init__(self, tls_id):
        self.tls_id = tls_id
        
        self.edge_phases = get_edge_phases(tls_id)
        self.edges = [ep['edge_id'] for ep in self.edge_phases]
        
        self.cycle_length = 60
        num_phases = len(self.edge_phases)
        self.phase_durations = {i: max(10, int(self.cycle_length / num_phases)) for i in range(num_phases)} if num_phases else {}
        
        self.current_phase_idx = 0
        if self.edge_phases:
            traci.trafficlight.setRedYellowGreenState(tls_id, self.edge_phases[0]['state'])
            
        self.time_in_phase = 0
        self.edge_vehicle_counts = {i: 0 for i in range(num_phases)}
        
    def step(self, step_length):
        if not self.edge_phases: return
        
        ep = self.edge_phases[self.current_phase_idx]
        count = 0
        for lane in ep['lanes']:
            try:
                count += traci.lane.getLastStepVehicleNumber(lane)
            except: pass
        self.edge_vehicle_counts[self.current_phase_idx] += count
        
        self.time_in_phase += step_length
        current_duration = self.phase_durations.get(self.current_phase_idx, 10)
        
        if self.time_in_phase >= current_duration:
            self.current_phase_idx = (self.current_phase_idx + 1) % len(self.edge_phases)
            traci.trafficlight.setRedYellowGreenState(self.tls_id, self.edge_phases[self.current_phase_idx]['state'])
            self.time_in_phase = 0
            
            if self.current_phase_idx == 0:
                self.optimize_split()
                
    def optimize_split(self):
        ds = {}
        for p_idx, ep in enumerate(self.edge_phases):
            lane_count = max(1, len(ep['lanes']))
            ds[p_idx] = self.edge_vehicle_counts[p_idx] / max(1, self.phase_durations[p_idx] * lane_count)
            self.edge_vehicle_counts[p_idx] = 0
            
        if not ds: return
        
        max_ds_phase = max(ds, key=ds.get)
        min_ds_phase = min(ds, key=ds.get)
        
        if ds[max_ds_phase] > ds[min_ds_phase] + 0.1:
            if self.phase_durations[min_ds_phase] > 10:
                self.phase_durations[min_ds_phase] -= 1
                self.phase_durations[max_ds_phase] += 1
