import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

def setup_fuzzy_system():
    # Antecedents (Inputs)
    # We map flow and density to a 0-100 scale (percentages relative to capacity or max observed)
    flow = ctrl.Antecedent(np.arange(0, 101, 1), 'flow')
    density = ctrl.Antecedent(np.arange(0, 101, 1), 'density')
    historic_weight = ctrl.Antecedent(np.arange(0, 101, 1), 'historic_weight')
    
    # Consequent (Output)
    priority = ctrl.Consequent(np.arange(0, 101, 1), 'priority')
    
    # Automf generates 3 terms: poor, average, good (we rename them low, medium, high)
    flow.automf(3, names=['low', 'medium', 'high'])
    density.automf(3, names=['low', 'medium', 'high'])
    historic_weight.automf(3, names=['low', 'medium', 'high'])
    priority.automf(3, names=['low', 'medium', 'high'])
    
    # Rules
    # If flow is high OR density is high, priority is high
    rule1 = ctrl.Rule(flow['high'] | density['high'], priority['high'])
    # If historic weight is high and flow is medium, priority is high
    rule2 = ctrl.Rule(historic_weight['high'] & flow['medium'], priority['high'])
    # If flow is medium and density is medium, priority is medium
    rule3 = ctrl.Rule(flow['medium'] & density['medium'], priority['medium'])
    # If everything is low, priority is low
    rule4 = ctrl.Rule(flow['low'] & density['low'] & historic_weight['low'], priority['low'])
    # If historic is high but current flow is low, medium priority
    rule5 = ctrl.Rule(historic_weight['high'] & flow['low'], priority['medium'])
    
    priority_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5])
    priority_sim = ctrl.ControlSystemSimulation(priority_ctrl)
    return priority_sim

def calculate_priority(sim, flow_val, density_val, historic_val):
    sim.input['flow'] = max(0, min(100, flow_val))
    sim.input['density'] = max(0, min(100, density_val))
    sim.input['historic_weight'] = max(0, min(100, historic_val))
    
    try:
        sim.compute()
        return sim.output['priority']
    except (ValueError, KeyError):
        # Fallback if no rules fire and crisp value cannot be computed
        return 50.0
