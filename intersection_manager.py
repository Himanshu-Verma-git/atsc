import traci
from config import BOUND_TIME, MAX_WAIT_TIME, MINIMUM_GREEN_TIME
from fuzzy_logic import setup_fuzzy_system, calculate_priority
from fuzzy_logic import setup_fuzzy_system, calculate_priority
from sumo_runner import get_edge_phases

class IntersectionManager:
    def __init__(self, tls_id):
        self.tls_id = tls_id
        
        # We now use custom edge phases instead of default phases
        self.edge_phases = get_edge_phases(tls_id)
        
        self.edges = [ep['edge_id'] for ep in self.edge_phases]
        
        self.fuzzy_sim = setup_fuzzy_system()
        
        self.edge_wait_time = {edge: 0 for edge in self.edges}
        self.edge_green_time = {edge: 0 for edge in self.edges}
        
        self.current_phase_idx = 0
        if self.edge_phases:
            traci.trafficlight.setRedYellowGreenState(tls_id, self.edge_phases[0]['state'])
            
        self.time_in_current_phase = 0
        self.next_phase_idx = None
        
    def get_shared_data(self):
        data = {}
        for ep in self.edge_phases:
            edge = ep['edge_id']
            veh_num = 0
            occ_sum = 0
            for lane in ep['lanes']:
                try:
                    veh_num += traci.lane.getLastStepVehicleNumber(lane)
                    occ_sum += traci.lane.getLastStepOccupancy(lane)
                except: pass
            
            data[edge] = {
                "vehicles": veh_num,
                "occupancy": occ_sum / len(ep['lanes']) if ep['lanes'] else 0
            }
        return data
        
    def step(self, step_length, historic_data, current_slot, adjacent_info):
        if not self.edge_phases: return
        
        current_state = traci.trafficlight.getRedYellowGreenState(self.tls_id)
        
        # Handle yellow phase transition
        if 'y' in current_state or 'Y' in current_state:
            self.time_in_current_phase += step_length
            if self.time_in_current_phase >= 3:
                if self.next_phase_idx is not None:
                    self.set_phase(self.next_phase_idx)
                    self.next_phase_idx = None
            return
            
        vehicles_on_edge = {}
        occupancy_on_edge = {}
        
        for ep in self.edge_phases:
            edge = ep['edge_id']
            v = 0
            o = 0
            for lane in ep['lanes']:
                try:
                    v += traci.lane.getLastStepVehicleNumber(lane)
                    o += traci.lane.getLastStepOccupancy(lane)
                except: pass
            vehicles_on_edge[edge] = v
            occupancy_on_edge[edge] = o / len(ep['lanes']) if ep['lanes'] else 0
            
        any_other_vehicles = sum(vehicles_on_edge.values()) > 0
        
        current_green_edge = None
        if self.current_phase_idx != -1:
            current_green_edge = self.edge_phases[self.current_phase_idx]['edge_id']
                
        # Update waiting and green times
        for edge in self.edges:
            if edge == current_green_edge:
                self.edge_green_time[edge] += step_length
                if vehicles_on_edge[edge] > 0:
                    self.edge_wait_time[edge] = 0
            else:
                self.edge_green_time[edge] = 0
                if vehicles_on_edge[edge] > 0:
                    self.edge_wait_time[edge] += step_length
                else:
                    self.edge_wait_time[edge] = 0
                    
        forced_edges = [edge for edge, wait in self.edge_wait_time.items() if wait >= MAX_WAIT_TIME]
        
        best_phase = self.current_phase_idx
        max_priority = -1
        
        for p_idx, ep in enumerate(self.edge_phases):
            edge = ep['edge_id']
                
            if forced_edges and edge not in forced_edges:
                continue
                
            flow = vehicles_on_edge[edge] * 10
            density = occupancy_on_edge[edge] * 100
            
            hist_weight = 50
            if edge in historic_data and current_slot < len(historic_data[edge]):
                hist_data = historic_data[edge][min(current_slot, len(historic_data[edge])-1)]
                hist_weight = hist_data.get('flow', 0) * 10
                
            phase_priority = calculate_priority(self.fuzzy_sim, flow, density, hist_weight)
                
            if phase_priority > max_priority:
                max_priority = phase_priority
                best_phase = p_idx
                
        # Enforce BOUND_TIME
        if best_phase == self.current_phase_idx and any_other_vehicles:
            if self.edge_green_time.get(current_green_edge, 0) >= BOUND_TIME:
                best_phase = self._get_alternative_phase(vehicles_on_edge)
                
        if best_phase != self.current_phase_idx and best_phase != -1:
            # Enforce MINIMUM_GREEN_TIME
            if current_green_edge is None or self.edge_green_time.get(current_green_edge, 0) >= MINIMUM_GREEN_TIME:
                self.transition_to(best_phase)
            else:
                self.time_in_current_phase += step_length
        else:
            self.time_in_current_phase += step_length
            
    def _get_alternative_phase(self, vehicles_on_edge):
        # Find next phase with vehicles waiting
        for i in range(1, len(self.edge_phases)):
            idx = (self.current_phase_idx + i) % len(self.edge_phases)
            edge = self.edge_phases[idx]['edge_id']
            if vehicles_on_edge[edge] > 0:
                return idx
        # If no other vehicles, just return the next phase
        return (self.current_phase_idx + 1) % len(self.edge_phases)

    def transition_to(self, new_phase_idx):
        self.next_phase_idx = new_phase_idx
        current_state = traci.trafficlight.getRedYellowGreenState(self.tls_id)
        next_state = self.edge_phases[new_phase_idx]['state']
        
        yellow_state = ""
        for i in range(len(current_state)):
            if current_state[i] in ('G', 'g') and next_state[i] in ('r', 'R'):
                yellow_state += 'y'
            else:
                yellow_state += current_state[i]
                
        traci.trafficlight.setRedYellowGreenState(self.tls_id, yellow_state)
        self.time_in_current_phase = 0
        self.current_phase_idx = -1
        
    def set_phase(self, phase_idx):
        traci.trafficlight.setRedYellowGreenState(self.tls_id, self.edge_phases[phase_idx]['state'])
        self.current_phase_idx = phase_idx
        self.time_in_current_phase = 0
