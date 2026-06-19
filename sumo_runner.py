import traci
from config import SUMO_CMD
import sys
import os
from collections import defaultdict

GUI_ENABLED = False

def start_simulation(run_name="baseline", use_gui=False, additional_args=None):
    global GUI_ENABLED
    GUI_ENABLED = use_gui
    
    cmd = SUMO_CMD.copy()
    if use_gui:
        cmd[0] = "sumo-gui"
        
    out_dir = f"outputs/{run_name}"
    os.makedirs(out_dir, exist_ok=True)
        
    cmd.extend([
        "--summary-output", f"{out_dir}/summary_{run_name}.xml",
        "--tripinfo-output", f"{out_dir}/tripinfo_{run_name}.xml",
        "--collision-output", f"{out_dir}/collisions_{run_name}.xml",
        "--log", f"{out_dir}/sumo_log.txt",
        "--message-log", f"{out_dir}/sumo_messages.txt"
    ])
    
    if "--verbose" in sys.argv:
        cmd.append("--verbose")
    
    if additional_args:
        cmd.extend(additional_args)

    
    print(cmd)
    traci.start(cmd)
    
def get_signalized_intersections():
    """Returns a list of all traffic light IDs."""
    return traci.trafficlight.getIDList()

def get_edge_phases(tls_id):
    """
    Generates custom phases where each unique approach edge gets one exclusive green phase.
    Returns: list of dicts {'edge_id': str, 'state': str, 'lanes': list}
    """
    links = traci.trafficlight.getControlledLinks(tls_id)
    
    edge_to_indices = defaultdict(list)
    edge_to_lanes = defaultdict(list)
    
    for i, phase_links in enumerate(links):
        for link in phase_links:
            if link:
                incoming_lane = link[0]
                edge_id = traci.lane.getEdgeID(incoming_lane)
                edge_to_indices[edge_id].append(i)
                if incoming_lane not in edge_to_lanes[edge_id]:
                    edge_to_lanes[edge_id].append(incoming_lane)
                    
    phases = []
    num_links = len(links)
    for edge_id, indices in edge_to_indices.items():
        state = ['r'] * num_links
        for idx in indices:
            state[idx] = 'G'
        phases.append({
            'edge_id': edge_id,
            'state': "".join(state),
            'lanes': edge_to_lanes[edge_id]
        })
        
    return phases

def close_simulation():
    traci.close()
    sys.stdout.flush()
