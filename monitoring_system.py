import traci
import os
import csv
from config import TELEPORT_WARNING_TIME
import sumo_runner

class MonitoringSystem:
    def __init__(self, run_name, controlled_edges):
        self.run_name = run_name
        self.controlled_edges = controlled_edges
        self.out_dir = f"outputs/{run_name}"
        os.makedirs(self.out_dir, exist_ok=True)
        
        self.teleport_file = f"{self.out_dir}/teleport_report.csv"
        with open(self.teleport_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["time", "vehicle_id", "edge_id", "x", "y"])
            
        self.currently_tracked_vehicle = None
        
    def step(self, time):
        # 1. Log actual teleports
        try:
            teleports = traci.simulation.getStartingTeleportIDList()
            if teleports:
                with open(self.teleport_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    for veh in teleports:
                        try:
                            x, y = traci.vehicle.getPosition(veh)
                            edge = traci.vehicle.getRoadID(veh)
                            writer.writerow([time, veh, edge, x, y])
                        except traci.exceptions.TraCIException:
                            writer.writerow([time, veh, "unknown", 0.0, 0.0])
        except traci.exceptions.TraCIException:
            pass
                    
        # 2. GUI Camera tracking
        if sumo_runner.GUI_ENABLED:
            if self.currently_tracked_vehicle:
                try:
                    # If it has moved and wait time reset, or it left the network
                    if traci.vehicle.getWaitingTime(self.currently_tracked_vehicle) < 10:
                        self.currently_tracked_vehicle = None
                except traci.exceptions.TraCIException:
                    # Vehicle teleported or left
                    self.currently_tracked_vehicle = None
                    
            if not self.currently_tracked_vehicle:
                for edge in self.controlled_edges:
                    try:
                        vehicles = traci.edge.getLastStepVehicleIDs(edge)
                        for veh in vehicles:
                            if traci.vehicle.getWaitingTime(veh) >= TELEPORT_WARNING_TIME:
                                self.currently_tracked_vehicle = veh
                                traci.gui.trackVehicle("View #0", veh)
                                traci.gui.setZoom("View #0", 2000)
                                break
                        if self.currently_tracked_vehicle:
                            break
                    except traci.exceptions.TraCIException:
                        pass
