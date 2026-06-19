import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import os

MODELS = ["baseline", "fuzzy", "scats", "scoot"]

def parse_summary(xml_file):
    data = []
    if not os.path.exists(xml_file): return pd.DataFrame()
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for step in root.findall('step'):
            data.append({
                'time': float(step.get('time', 0)),
                'running': int(step.get('running', 0)),
                'halting': int(step.get('halting', 0)),
                'meanWaitingTime': float(step.get('meanWaitingTime', 0)),
                'meanTravelTime': float(step.get('meanTravelTime', 0))
            })
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        
    return pd.DataFrame(data)

def parse_tripinfo(xml_file):
    data = []
    if not os.path.exists(xml_file): return pd.DataFrame()
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for trip in root.findall('tripinfo'):
            data.append({
                'id': trip.get('id', ''),
                'duration': float(trip.get('duration', 0)),
                'routeLength': float(trip.get('routeLength', 0)),
                'waitingTime': float(trip.get('waitingTime', 0)),
                'timeLoss': float(trip.get('timeLoss', 0))
            })
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        
    return pd.DataFrame(data)

def run_benchmarking():
    print("Running benchmarking analysis...")
    
    summaries = {}
    tripinfos = {}
    
    for model in MODELS:
        summ_file = f"summary_{model}.xml"
        trip_file = f"tripinfo_{model}.xml"
        
        df_summ = parse_summary(summ_file)
        df_trip = parse_tripinfo(trip_file)
        
        if not df_summ.empty: summaries[model] = df_summ
        if not df_trip.empty: tripinfos[model] = df_trip
        
    if not summaries:
        print("No summary data found. Please run the simulations first.")
        return
        
    # Plot Mean Waiting Time over time
    plt.figure(figsize=(10, 6))
    for model, df in summaries.items():
        plt.plot(df['time'], df['meanWaitingTime'], label=model)
    plt.xlabel('Simulation Time (s)')
    plt.ylabel('Mean Waiting Time (s)')
    plt.title('Mean Waiting Time Comparison')
    plt.legend()
    plt.grid(True)
    plt.savefig('benchmark_waiting_time.png')
    
    # Plot Halting Vehicles over time
    plt.figure(figsize=(10, 6))
    for model, df in summaries.items():
        plt.plot(df['time'], df['halting'], label=model)
    plt.xlabel('Simulation Time (s)')
    plt.ylabel('Number of Halting Vehicles')
    plt.title('Halting Vehicles Comparison')
    plt.legend()
    plt.grid(True)
    plt.savefig('benchmark_halting_vehicles.png')
    
    # Bar chart for Trip Info aggregates
    if tripinfos:
        metrics = []
        for model, df in tripinfos.items():
            metrics.append({
                'Model': model,
                'Avg Duration': df['duration'].mean(),
                'Avg Time Loss': df['timeLoss'].mean(),
                'Avg Waiting Time': df['waitingTime'].mean()
            })
        
        df_metrics = pd.DataFrame(metrics).set_index('Model')
        print("\nAggregated Trip Metrics:")
        print(df_metrics)
        
        df_metrics.plot(kind='bar', figsize=(10, 6))
        plt.title('Trip Metrics Comparison')
        plt.ylabel('Time (s)')
        plt.tight_layout()
        plt.savefig('benchmark_trip_metrics.png')
        
    print("Benchmarking plots saved: benchmark_waiting_time.png, benchmark_halting_vehicles.png, benchmark_trip_metrics.png")

if __name__ == "__main__":
    run_benchmarking()
