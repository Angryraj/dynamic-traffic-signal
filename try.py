import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import tkinter as tk

# Function to simulate FASTag count retrieval for each lane
def get_fastag_count(lane_id):
    return np.random.randint(1, 6)  # Simulate a vehicle count between 1 and 5

# Function to simulate emergency vehicle detection
def detect_emergency_vehicle(lane_id):
    return np.random.randint(0, 2)  # Simulate 0 or 1 emergency vehicle

# Paths to the video files and output paths for the four lanes
lane_ids = [1, 2, 3, 4]

# Calculate traffic densities, FASTag counts, and detect emergency vehicles for each lane
traffic_densities = []
fastag_counts = []
emergency_vehicle_counts = []

for lane_id in lane_ids:
    fastag_count = get_fastag_count(lane_id)
    density = fastag_count / 100.0
    traffic_densities.append(density)
    fastag_counts.append(fastag_count)
    emergency_vehicle_counts.append(detect_emergency_vehicle(lane_id))

# Define fuzzy variables
traffic_density_var = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'traffic_density')
traffic_severity_var = ctrl.Antecedent(np.arange(0, 11, 1), 'traffic_severity')
emergency_intensity_var = ctrl.Antecedent(np.arange(0, 2.1, 1), 'emergency_intensity')
signal_timing_adjustment = ctrl.Consequent(np.arange(10, 61, 1), 'signal_timing_adjustment')  # Updated range

# Define fuzzy membership functions
traffic_density_var['low'] = fuzz.trimf(traffic_density_var.universe, [0, 0, 0.3])
traffic_density_var['medium'] = fuzz.trimf(traffic_density_var.universe, [0.2, 0.5, 0.8])
traffic_density_var['high'] = fuzz.trimf(traffic_density_var.universe, [0.7, 1.0, 1.0])

traffic_severity_var['low'] = fuzz.trimf(traffic_severity_var.universe, [0, 0, 3])
traffic_severity_var['medium'] = fuzz.trimf(traffic_severity_var.universe, [2, 5, 8])
traffic_severity_var['high'] = fuzz.trimf(traffic_severity_var.universe, [7, 10, 10])

emergency_intensity_var['none'] = fuzz.trimf(emergency_intensity_var.universe, [0, 0, 0.5])
emergency_intensity_var['low'] = fuzz.trimf(emergency_intensity_var.universe, [0.5, 1, 1.5])
emergency_intensity_var['high'] = fuzz.trimf(emergency_intensity_var.universe, [1.5, 2, 2])

signal_timing_adjustment['short'] = fuzz.trimf(signal_timing_adjustment.universe, [10, 10, 25])
signal_timing_adjustment['medium'] = fuzz.trimf(signal_timing_adjustment.universe, [20, 35, 50])
signal_timing_adjustment['long'] = fuzz.trimf(signal_timing_adjustment.universe, [40, 60, 60])

# Define fuzzy rules using density, severity, and emergency intensity
rule1 = ctrl.Rule(traffic_density_var['high'] & traffic_severity_var['high'] & emergency_intensity_var['high'], signal_timing_adjustment['long'])
rule2 = ctrl.Rule(traffic_density_var['medium'] & traffic_severity_var['medium'] & emergency_intensity_var['low'], signal_timing_adjustment['medium'])
rule3 = ctrl.Rule(traffic_density_var['low'] & traffic_severity_var['low'] & emergency_intensity_var['none'], signal_timing_adjustment['short'])
rule4 = ctrl.Rule(traffic_density_var['high'] | emergency_intensity_var['high'], signal_timing_adjustment['long'])  # Prioritize high density or emergency
rule5 = ctrl.Rule(traffic_severity_var['high'] | emergency_intensity_var['high'], signal_timing_adjustment['long'])  # Prioritize high severity or emergency
rule6 = ctrl.Rule(emergency_intensity_var['high'], signal_timing_adjustment['long'])  # Emergency vehicle priority

# Create a control system and simulation
signal_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6])
signal_sim = ctrl.ControlSystemSimulation(signal_ctrl)

# Calculate signal timing adjustments for each lane
signal_timings = []
for density, fastag_count, emergency_count in zip(traffic_densities, fastag_counts, emergency_vehicle_counts):
    severity = fastag_count / 10  # Simplified severity calculation
    emergency_intensity = emergency_count  # Directly use the detected emergency vehicle count
    
    signal_sim.input['traffic_density'] = density
    signal_sim.input['traffic_severity'] = severity
    signal_sim.input['emergency_intensity'] = emergency_intensity
    
    try:
        signal_sim.compute()
        # Check if the output variable is available
        if 'signal_timing_adjustment' in signal_sim.output:
            signal_timing = signal_sim.output['signal_timing_adjustment']
            # Halve the calculated signal timing
            signal_timing = signal_timing / 2.0
        else:
            raise ValueError("Output variable 'signal_timing_adjustment' not found in the control system simulation.")
        
        signal_timings.append(signal_timing)
    except Exception as e:
        print(f"Error calculating signal timing: {e}")
        signal_timings.append(30)  # Default value on error

# Tkinter setup for the traffic signal display
class TrafficSignalApp:
    def __init__(self, master, signal_timings, fastag_counts, emergency_vehicle_counts):
        self.master = master
        self.signal_timings = signal_timings
        self.fastag_counts = fastag_counts
        self.emergency_vehicle_counts = emergency_vehicle_counts
        self.current_lane = 0
        self.countdown = int(signal_timings[0])  # Start with the first lane's timing
        self.canvas = tk.Canvas(master, width=800, height=400)
        self.canvas.pack()

        # Create lanes, signals, timing labels, vehicle count labels, and emergency vehicle labels
        self.signals = []
        self.lane_labels = []
        self.timing_labels = []
        self.vehicle_count_labels = []
        self.emergency_vehicle_labels = []

        for i in range(4):
            # Create label for lane
            self.lane_labels.append(self.canvas.create_text(100 + i*200, 50, text=f"Lane {i+1}", font=("Helvetica", 16)))
            # Create signal (red by default)
            self.signals.append(self.canvas.create_oval(90 + i*200, 80, 110 + i*200, 100, fill="red"))
            # Create label for displaying signal timing
            self.timing_labels.append(self.canvas.create_text(100 + i*200, 150, text=f"Timing: {int(signal_timings[i])} s", font=("Helvetica", 14)))
            # Create label for displaying vehicle count
            self.vehicle_count_labels.append(self.canvas.create_text(100 + i*200, 200, text=f"Vehicles: {fastag_counts[i]}", font=("Helvetica", 14)))
            # Create label for displaying emergency vehicle count
            self.emergency_vehicle_labels.append(self.canvas.create_text(100 + i*200, 250, text=f"Emergency: {emergency_vehicle_counts[i]}", font=("Helvetica", 14)))

        self.update_signals()

    def update_signals(self):
        # Reset all signals to red
        for i in range(4):
            self.canvas.itemconfig(self.signals[i], fill="red")

        # Set the current signal to green
        self.canvas.itemconfig(self.signals[self.current_lane], fill="green")
        # Start the countdown for the current lane
        self.countdown = int(self.signal_timings[self.current_lane])
        self.update_countdown()

    def update_countdown(self):
        # Update the timing label with the current countdown value
        self.canvas.itemconfig(self.timing_labels[self.current_lane], text=f"Timing: {self.countdown} s")
        if self.countdown > 0:
            self.countdown -= 1
            self.master.after(1000, self.update_countdown)  # Update countdown every second
        else:
            self.next_lane()

    def next_lane(self):
        self.current_lane = (self.current_lane + 1) % 4
        self.update_signals()

# Create the Tkinter window
root = tk.Tk()
root.title("Traffic Signal System")

# Initialize the traffic signal application
app = TrafficSignalApp(root, signal_timings, fastag_counts, emergency_vehicle_counts)

# Start the Tkinter event loop
root.mainloop()
