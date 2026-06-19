import os

# Configuration variables
SUMO_CMD = ["sumo", "-c", "dua.static.sumocfg", "--no-warnings", "--threads", "8"]

SLOT_DURATION = 900 # 15 minutes in seconds
BOUND_TIME = 60 # max green time for highest priority lane if others are waiting
MAX_WAIT_TIME = 120 # maximum wait time before forcefully getting a green light
COMMUNICATION_INTERVAL = 30 # share data between intersections every 30 seconds
MINIMUM_GREEN_TIME = 15 # Minimum green time for fuzzy logic
TELEPORT_WARNING_TIME = 500 # Wait time at which vehicle is tracked

# Only look at signalized intersections
SIGNALIZED_ONLY = True

# Data files
HISTORIC_DATA_FILE = "historic_data.json"
