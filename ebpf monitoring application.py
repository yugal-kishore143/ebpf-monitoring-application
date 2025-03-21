import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import os
import signal
import threading

global process
process = None

def run_bcctool():
    global process
    selected_tool_description = tool_var.get()
    tool = [key for key, value in tools.items() if value == selected_tool_description][0]
    output_table.delete(*output_table.get_children())  # Clear previous entries
    
    if tool:
        command = f"sudo /usr/sbin/{tool}-bpfcc"  # Adjusted for bpfcc tools
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
            threading.Thread(target=read_output, args=(process,), daemon=True).start()
        except Exception as e:
            output_table.insert("", "end", values=("Execution failed:", str(e)), tags=("error",))
            
def read_output(proc):
    header_set = False
    for line in proc.stdout:
        if process is None:  # Stop reading if process is terminated
            break
        values = line.strip().split()
        if not header_set:  # Set columns dynamically
            output_table["columns"] = tuple(range(len(values)))
            for i, col in enumerate(values):
                output_table.heading(i, text=col)
                output_table.column(i, width=150)
            header_set = True
        else:
            output_table.insert("", "end", values=values)
        output_table.update_idletasks()
    for line in proc.stderr:
        if process is None:
            break
        output_table.insert("", "end", values=("ERROR:", line.strip()), tags=("error",))

def stop_bcctool():
    global process
    if process:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Terminate the process group
        process = None
        output_table.insert("", "end", values=("Process stopped.",))
        output_table.update_idletasks()

def clear_output():
    output_table.delete(*output_table.get_children())


def generate_graph():
    # Extract data from the table
    data = []
    for child in output_table.get_children():
        values = output_table.item(child)["values"]
        data.append(values)
    
    if len(data) < 2:
        output_table.insert("", "end", values=("Not enough data to generate graph.",), tags=("error",))
        return
    
    # Convert data to numeric, ignoring non-numeric values
    x_data = []
    y_data = []
    for row in data:
        try:
            x = float(row[0])
            y = float(row[1])
            x_data.append(x)
            y_data.append(y)
        except ValueError:
            continue
    
    if not x_data or not y_data:
        output_table.insert("", "end", values=("No numeric data found for graph generation.",), tags=("error",))
        return
    
    # Generate the graph
    plt.figure(figsize=(10, 6))
    plt.plot(x_data, y_data, marker='o')
    plt.xlabel("Column 1")
    plt.ylabel("Column 2")
    plt.title("Graph of Column 1 vs Column 2")
    plt.grid(True)
    plt.show()

def on_closing():
    stop_bcctool()
    root.destroy()

def on_hover(event, widget, color):
    widget.config(bg=color)

def on_leave(event, widget, original_color):
    widget.config(bg=original_color)

root = tk.Tk()
root.title("Soft-ROCe Monitoring GUI")
root.geometry("900x600")
root.protocol("WM_DELETE_WINDOW", on_closing)

tk.Label(root, text="Select Monitoring Tool:", font=("Arial", 12, "bold")).pack(pady=5)

# Relevant BCC tools for Soft-ROCe implementation monitoring
tools = {
    "tcpconnect": "TCP Connection Statistics",
    "tcpretrans": "TCP Retransmission Statistics",
    "sockstat": "Socket Statistics",
    "biolatency": "Block I/O Latency Statistics",
    "cachestat": "Cache Statistics"
}
tool_var = tk.StringVar()
tool_dropdown = ttk.Combobox(root, textvariable=tool_var, values=list(tools.values()), state="readonly")
tool_dropdown.pack(pady=5)
tool_dropdown.set(list(tools.values())[0])

button_frame = ttk.Frame(root)
button_frame.pack(pady=5)

# Run button
run_button = tk.Button(button_frame, text="Start Monitoring", command=run_bcctool, bg="green", fg="black", font=("Arial", 10, "bold"))
run_button.grid(row=0, column=0, padx=5)
run_button.bind("<Enter>", lambda e: on_hover(e, run_button, "green"))
run_button.bind("<Leave>", lambda e: on_leave(e, run_button, "lightgray"))

# Stop button
stop_button = tk.Button(button_frame, text="Stop Monitoring", command=stop_bcctool, bg="red", fg="black", font=("Arial", 10, "bold"))
stop_button.grid(row=0, column=1, padx=5)
stop_button.bind("<Enter>", lambda e: on_hover(e, stop_button, "red"))
stop_button.bind("<Leave>", lambda e: on_leave(e, stop_button, "lightgray"))

# Clear output button
clear_button = tk.Button(button_frame, text="Clear Output", command=clear_output, bg="blue", fg="black", font=("Arial", 10, "bold"))
clear_button.grid(row=0, column=2, padx=5)
clear_button.bind("<Enter>", lambda e: on_hover(e, clear_button, "blue"))
clear_button.bind("<Leave>", lambda e: on_leave(e, clear_button, "lightgray"))

# Generate graph button
graph_button = tk.Button(button_frame, text="Generate Graph", command=generate_graph, bg="purple", fg="black", font=("Arial", 10, "bold"))
graph_button.grid(row=0, column=3, padx=5)
graph_button.bind("<Enter>", lambda e: on_hover(e, graph_button, "purple"))
graph_button.bind("<Leave>", lambda e: on_leave(e, graph_button, "lightgray"))

# Table output with a scrollbar
frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, pady=5)

scrollbar = ttk.Scrollbar(frame, orient="vertical")
output_table = ttk.Treeview(frame, show="headings", yscrollcommand=scrollbar.set)
scrollbar.config(command=output_table.yview)
scrollbar.pack(side="right", fill="y")
output_table.pack(side="left", fill=tk.BOTH, expand=True)

root.mainloop()