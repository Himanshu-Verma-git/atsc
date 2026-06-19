import traci
from sumo_runner import get_edge_phases

class ScatsIntersection:
    def __init__(self, tls_id):
        self.tls_id = tls_id
        
        self.edge_phases = get_edge_phases(tls_id)
        self.edges = [ep['edge_id'] for ep in self.edge_phases]
        
        # SCATS cycle defaults
        self.cycle_length = 60 # Default initial cycle length
        num_phases = len(self.edge_phases)
        
        self.splits = {i: 1.0 / num_phases for i in range(num_phases)} if num_phases else {}
        self.phase_durations = {i: max(10, int(self.cycle_length * self.splits[i])) for i in range(num_phases)}
        
        self.current_phase_idx = 0
        if self.edge_phases:
            traci.trafficlight.setRedYellowGreenState(tls_id, self.edge_phases[0]['state'])
            
        self.time_in_phase = 0
        self.edge_occupancy_sum = {i: 0.0 for i in range(num_phases)}
        self.edge_step_count = {i: 0 for i in range(num_phases)}
        
    def step(self, step_length):
        if not self.edge_phases: return
        
        # Accumulate occupancy for the active edge phase
        ep = self.edge_phases[self.current_phase_idx]
        max_occ = 0
        for lane in ep['lanes']:
            try:
                occ = traci.lane.getLastStepOccupancy(lane)
                if occ > max_occ: max_occ = occ
            except: pass
            
        self.edge_occupancy_sum[self.current_phase_idx] += max_occ
        self.edge_step_count[self.current_phase_idx] += 1
        
        self.time_in_phase += step_length
        current_duration = self.phase_durations.get(self.current_phase_idx, 10)
        
        if self.time_in_phase >= current_duration:
            self.current_phase_idx = (self.current_phase_idx + 1) % len(self.edge_phases)
            traci.trafficlight.setRedYellowGreenState(self.tls_id, self.edge_phases[self.current_phase_idx]['state'])
            self.time_in_phase = 0
            
            if self.current_phase_idx == 0:
                self.recalculate_cycle_and_splits()
                
    def recalculate_cycle_and_splits(self):
        ds = {}
        for p_idx in range(len(self.edge_phases)):
            if self.edge_step_count[p_idx] > 0:
                ds[p_idx] = self.edge_occupancy_sum[p_idx] / self.edge_step_count[p_idx]
            else:
                ds[p_idx] = 0.0
                
            self.edge_occupancy_sum[p_idx] = 0
            self.edge_step_count[p_idx] = 0
            
        max_ds = max(ds.values()) if ds else 0
        
        if max_ds > 0.85:
            self.cycle_length = min(self.cycle_length + 10, 160)
        elif max_ds < 0.60:
            self.cycle_length = max(self.cycle_length - 10, 60)
            
        total_ds = sum(ds.values())
        if total_ds > 0:
            for p_idx in range(len(self.edge_phases)):
                new_split = ds[p_idx] / total_ds
                self.splits[p_idx] = 0.7 * self.splits[p_idx] + 0.3 * new_split
                
        for p_idx in range(len(self.edge_phases)):
            self.phase_durations[p_idx] = max(10, int(self.cycle_length * self.splits[p_idx]))
