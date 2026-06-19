# Adaptive Traffic Signal Control (ATSC) Benchmarking

This project implements and benchmarks multiple Adaptive Traffic Signal Control algorithms using SUMO and TraCI within a Docker environment.

## Implemented Algorithms
1. **Baseline Model:** Fixed-time traditional signals. Collects baseline data into `historic_data.json` for 15-minute intervals.
2. **Fuzzy Logic Model:** Uses `scikit-fuzzy` to dynamically prioritize phases based on real-time flow, density, and historical weights. Enforces `BOUND_TIME` and `MAX_WAIT_TIME`. Shares data between adjacent intersections.
3. **SCATS Model (Simplified):** Adjusts intersection cycle lengths and splits dynamically at the end of each cycle based on Degree of Saturation (measured via stop-line occupancy).
4. **SCOOT Model (Simplified):** Makes incremental adjustments (+/- 1s) to splits and cycle times continuously based on cyclic flow profiles.

## Environment Setup

The entire project runs inside a Docker container based on `ghcr.io/eclipse-sumo/sumo:latest`. This ensures all Python dependencies (`scikit-fuzzy`, `pandas`, `matplotlib`, `traci`) and the SUMO environment are correctly configured.

1. **Build the Docker Environment:**
   ```bash
   docker-compose build
   ```

2. **Access the Container:**
   To run the scripts, open a shell inside the container:
   ```bash
   docker-compose run --rm sumo-sim /bin/bash
   ```
   *(All following commands should be run inside this container shell)*

## Execution Workflow

Run the scripts in the following order:

1. **Generate Historic Data (Baseline Run)**
   ```bash
   python3 run_baseline.py
   ```
   *This will run the fixed-time scenario, generate `summary_baseline.xml`, `tripinfo_baseline.xml`, and output `historic_data.json`.*

2. **Run Fuzzy ATSC**
   ```bash
   python3 run_fuzzy.py
   ```
   *Outputs `summary_fuzzy.xml` and `tripinfo_fuzzy.xml`.*

3. **Run SCATS**
   ```bash
   python3 run_scats.py
   ```
   *Outputs `summary_scats.xml` and `tripinfo_scats.xml`.*

4. **Run SCOOT**
   ```bash
   python3 run_scoot.py
   ```
   *Outputs `summary_scoot.xml` and `tripinfo_scoot.xml`.*

## Benchmarking & Analysis

Once you have run the desired models, execute the benchmarking script to generate comparison plots:

```bash
python3 benchmark_analysis.py
```

This will parse the XML outputs and generate:
- `benchmark_waiting_time.png`: Line plot of mean waiting time over the simulation.
- `benchmark_halting_vehicles.png`: Line plot of the number of halted vehicles.
- `benchmark_trip_metrics.png`: Bar charts comparing average trip duration, time loss, and waiting time across models.

## Configuration
Modify `config.py` to adjust constants like `BOUND_TIME`, `MAX_WAIT_TIME`, and data sharing intervals for the fuzzy model.
