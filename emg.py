import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from tkinter import Tk, Label, Button, Entry, messagebox, StringVar, OptionMenu
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

# Function to generate realistic EMG data between 20 µV and 500 µV
def generate_emg_data(frame, noise_level=30):
    amplitude = 240  # Adjust amplitude for realistic values (500 - 20)/2 = 240
    bias = 260       # Bias adjusted to center the signal (20 + 500)/2 = 260
    noise = np.random.normal(0, noise_level, 1)  # Adjust noise based on the phase
    signal = amplitude * np.sin(2 * np.pi * (frame / 50.0)) + bias + noise
    signal = np.clip(signal, 20, 500)  # Ensure signal stays within 20 and 500 µV
    return signal

# Initialize data
emg_data = np.zeros(10)  # Store the last 10 data points (sliding window)
index = 0
running = False  # Variable to start and stop animation
max_emg_value = 0  # To record maximum EMG value
all_emg_data = []  # List to store all EMG data across frames
threshold_line_data = np.full_like(emg_data, np.nan)  # Initially, the threshold line data is empty (NaN)
endurance_threshold = 0  # Threshold value for endurance
threshold_line_visible = False  # Track visibility of the threshold line

# Phases
phase = "noise_detection"
test_type = None
test_duration = 0
start_time = None
total_usage_start = None  # To track total usage time

# Create a figure and axis for the plot
fig, ax = plt.subplots()
x_vals = np.arange(10)  # X-axis values (0 to 9)
line, = ax.plot(x_vals, emg_data, color='blue', label='EMG Data')
threshold_line_plot, = ax.plot(x_vals, threshold_line_data, color='red', linestyle='--', label='Threshold')  # Threshold line

# Set the limits and labels
ax.set_ylim(0, 600)  # Adjust the Y-axis limits based on expected data
ax.set_xlim(0, 9)    # X-axis limit for the last 10 points
ax.set_xlabel('Time')
ax.set_ylabel('EMG (µV)')
ax.set_title('Dynamic EMG Data Plot (Arm Fist Movement)')

# Update function for animation
def update(frame):
    global index, max_emg_value, all_emg_data, threshold_line_data, phase, start_time, running  # Declare global

    if not running:
        return line, threshold_line_plot  # Do nothing if the animation is paused

    # Determine noise level based on phase
    noise_level = 80 if phase == "noise_detection" else 30  # High noise in noise detection phase

    # Generate new EMG data for the current frame
    new_value = generate_emg_data(frame, noise_level=noise_level)  # Generate one new data point
    emg_data[:-1] = emg_data[1:]  # Shift data left (simulate sliding window)
    emg_data[-1] = new_value  # Insert new value at the end
    all_emg_data.append(new_value)  # Accumulate all EMG data over time

    # Check if the current data exceeds the max EMG value
    max_emg_value = max(max_emg_value, np.max(emg_data))  # Update max EMG value if needed

    # Update line data with the latest 10 data points (scrolling effect)
    line.set_ydata(emg_data)  # Update the y-data dynamically

    # Update threshold line if it's visible
    if threshold_line_visible:
        threshold_line_data[:] = endurance_threshold  # Update all threshold line points to the threshold value
    else:
        threshold_line_data[:] = np.nan  # Set to NaN if the line is not visible
    threshold_line_plot.set_ydata(threshold_line_data)  # Update the threshold line data

    # Handle phase transitions
    if phase == "noise_detection" and time.time() - start_time > 15:  # Noise detection phase for 15 seconds
        phase = "noise_removal"
        messagebox.showinfo("Phase Transition", "Noise detected. Removing noise...")
        transition_to_test_ui()  # Transition to the test UI after noise detection

    return line, threshold_line_plot

# Function to toggle the animation (start/stop)
def toggle_animation():
    global running, phase, start_time, total_usage_start
    if phase == "noise_detection":
        running = True
        btn_start.config(text="Pause")
        start_time = time.time()  # Start time for noise detection phase
        if total_usage_start is None:
            total_usage_start = time.time()  # Start total usage timer
    else:
        running = not running
        if running:
            btn_start.config(text="Pause")
        else:
            btn_start.config(text="Start")

# Function to show or hide the endurance threshold line
def toggle_threshold():
    global threshold_line_visible, endurance_threshold
    threshold = float(entry_threshold.get())
    endurance_threshold = threshold

    # Toggle the visibility of the threshold line
    threshold_line_visible = not threshold_line_visible
    if threshold_line_visible:
        btn_threshold.config(text="Hide Threshold")
    else:
        btn_threshold.config(text="Show Threshold")

# Endurance function to calculate average time above the endurance threshold
def endurance(threshold):
    above_threshold = np.array(all_emg_data)[np.array(all_emg_data) > threshold]  # Get data above the threshold
    if len(above_threshold) > 0:
        avg_time = len(above_threshold) / 100.0  # Assuming 100 frames per second
        return avg_time, len(above_threshold)
    return 0, 0  # No data above the threshold

# Fatigue function to count the number of "up and down" cycles above and below the threshold
def fatigue(threshold):
    above_threshold = np.array(all_emg_data) > threshold
    fatigue_count = 0
    above = False  # Flag to check if we're above the threshold

    for value in above_threshold:
        if value and not above:
            # We've just crossed above the threshold
            above = True
        elif not value and above:
            # We've just crossed back below the threshold
            above = False
            fatigue_count += 1  # Count this as a fatigue cycle

    return fatigue_count

# Function to calculate and display endurance and fatigue
def calculate_endurance_fatigue():
    threshold = endurance_threshold
    avg_time, above_threshold = endurance(threshold)
    total_cycles = fatigue(threshold)
    lbl_results.config(text=f"Endurance: {above_threshold / 100.0:.2f} sec\n"
                            f"Fatigue Cycles: {total_cycles}")

# Function to generate and display a final report
def generate_report():
    avg_value = np.mean(all_emg_data) if len(all_emg_data) > 0 else 0
    total_endurance_time, above_threshold_count = endurance(endurance_threshold)
    total_fatigue_cycles = fatigue(endurance_threshold)

    report = (f"Final Report:\n"
              f"Max EMG Value: {max_emg_value:.2f} µV\n"
              f"Average EMG Value: {avg_value:.2f} µV\n"
              f"Endurance Threshold: {endurance_threshold:.2f} µV\n"
              f"Total Endurance Time: {total_endurance_time:.2f} seconds\n"
              f"Total Fatigue Cycles: {total_fatigue_cycles}")
    
    # Show report
    messagebox.showinfo("Report", report)

# Function to transition to test UI
def transition_to_test_ui():
    global phase
    phase = "test_ui"  # Set phase to test UI
    btn_start.config(text="Start Test")
    btn_start.config(command=start_test)  # Change button action to start the test
    lbl_info.config(text="Noise removal complete. Please start the test.")

# Function to start the test (endurance or fatigue)
def start_test():
    global phase, test_type, test_duration, start_time, running
    if phase != "test_ui":
        messagebox.showwarning("Warning", "You cannot start the test yet.")
        return
    
    test_type = test_var.get()
    test_duration = int(entry_duration.get())  # Get test duration
    phase = "test_running"
    running = True
    start_time = time.time()  # Start the test timer

# Function to update and display timers
def update_timers():
    if total_usage_start:
        elapsed_total_time = time.time() - total_usage_start
        lbl_total_time.config(text=f"Total Usage Time: {elapsed_total_time:.2f} sec")

    if running and start_time:
        elapsed_test_time = time.time() - start_time
        lbl_test_time.config(text=f"Test Time: {elapsed_test_time:.2f} sec")

    root.after(100, update_timers)  # Update timers every 100 ms

# Tkinter GUI setup
root = Tk()
root.title("EMG Data Visualization")

# Canvas to embed the matplotlib figure
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=0, column=0, columnspan=3)

# Button to toggle animation (start/pause)
btn_start = Button(root, text="Start", command=toggle_animation)
btn_start.grid(row=1, column=0)

# Label for info messages
lbl_info = Label(root, text="Starting noise detection...")
lbl_info.grid(row=1, column=1, columnspan=2)

# Entry for endurance threshold
Label(root, text="Threshold (µV):").grid(row=2, column=0)
entry_threshold = Entry(root)
entry_threshold.grid(row=2, column=1)
entry_threshold.insert(0, '300')  # Default threshold

# Button to toggle the threshold line visibility
btn_threshold = Button(root, text="Show Threshold", command=toggle_threshold)
btn_threshold.grid(row=1, column=2)

# Dropdown menu to select test type (endurance or fatigue)
test_var = StringVar(root)
test_var.set("Endurance")  # Default value
test_menu = OptionMenu(root, test_var, "Endurance", "Fatigue")
test_menu.grid(row=2, column=2)

# Entry for test duration
Label(root, text="Test Duration (seconds):").grid(row=3, column=0)
entry_duration = Entry(root)
entry_duration.grid(row=3, column=1)
entry_duration.insert(0, '10')  # Default test duration

# Button to start the selected test
btn_test = Button(root, text="Start Test", command=start_test)
btn_test.grid(row=3, column=2)

# Button to calculate endurance and fatigue
btn_calculate = Button(root, text="Calculate Endurance/Fatigue", command=calculate_endurance_fatigue)
btn_calculate.grid(row=4, column=0)

# Button to generate the report
btn_report = Button(root, text="Generate Report", command=generate_report)
btn_report.grid(row=4, column=2)

# Label to display results (endurance and fatigue)
lbl_results = Label(root, text="Results:\nEndurance: \nFatigue Cycles: ")
lbl_results.grid(row=5, column=0, columnspan=3)

# Timer labels for total usage time and test time
lbl_total_time = Label(root, text="Total Usage Time: 0.00 sec")
lbl_total_time.grid(row=6, column=0, columnspan=2)

lbl_test_time = Label(root, text="Test Time: 0.00 sec")
lbl_test_time.grid(row=6, column=2)

# Set up the animation
ani = animation.FuncAnimation(fig, update, frames=100, interval=100, blit=False)

# Start updating timers
update_timers()

# Start the Tkinter event loop
root.mainloop()
