import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import os
import signal
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
    data = []
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
            data.append(values)
        output_table.update_idletasks()
    for line in proc.stderr:
        if process is None:
            break
        output_table.insert("", "end", values=("ERROR:", line.strip()), tags=("error",))
    if process is not None:
        plot_graph(data)

def stop_bcctool():
    global process
    if process:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Terminate the process group
        process = None
        output_table.insert("", "end", values=("Process stopped.",))
        output_table.update_idletasks()

def clear_output():
    output_table.delete(*output_table.get_children())

def plot_graph(data):
    if not data:
        return
    try:
        fig, ax = plt.subplots()
        numeric_data = [[float(x) for x in row if x.replace('.', '', 1).isdigit()] for row in data]
        if numeric_data:
            for i, col in enumerate(zip(*numeric_data)):
                ax.plot(col, label=f"Column {i}")
            ax.legend()
            ax.set_title("Monitoring Data Graph")
            ax.set_xlabel("Entries")
            ax.set_ylabel("Values")
        
        for widget in graph_frame.winfo_children():
            widget.destroy()
        
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    except Exception as e:
        output_table.insert("", "end", values=("Graph Error:", str(e)), tags=("error",))

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
run_button = tk.Button(button_frame, text="Start Monitoring", command=run_bcctool, bg="lightgray", fg="black", font=("Arial", 10, "bold"))
run_button.grid(row=0, column=0, padx=5)
run_button.bind("<Enter>", lambda e: on_hover(e, run_button, "green"))
run_button.bind("<Leave>", lambda e: on_leave(e, run_button, "lightgray"))

# Stop button
stop_button = tk.Button(button_frame, text="Stop Monitoring", command=stop_bcctool, bg="lightgray", fg="black", font=("Arial", 10, "bold"))
stop_button.grid(row=0, column=1, padx=5)
stop_button.bind("<Enter>", lambda e: on_hover(e, stop_button, "red"))
stop_button.bind("<Leave>", lambda e: on_leave(e, stop_button, "lightgray"))

# Clear output button
clear_button = tk.Button(button_frame, text="Clear Output", command=clear_output, bg="lightgray", fg="black", font=("Arial", 10, "bold"))
clear_button.grid(row=0, column=2, padx=5)
clear_button.bind("<Enter>", lambda e: on_hover(e, clear_button, "blue"))
clear_button.bind("<Leave>", lambda e: on_leave(e, clear_button, "lightgray"))

# Table output with a scrollbar
frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, pady=5)

scrollbar = ttk.Scrollbar(frame, orient="vertical")
output_table = ttk.Treeview(frame, show="headings", yscrollcommand=scrollbar.set)
scrollbar.config(command=output_table.yview)
scrollbar.pack(side="right", fill="y")
output_table.pack(side="left", fill=tk.BOTH, expand=True)

# Graph Frame
graph_frame = ttk.Frame(root)
graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)

# Graph button
graph_button = tk.Button(button_frame, text="Generate Graph", command=lambda: plot_graph([]), bg="lightgray", fg="black", font=("Arial", 10, "bold"))
graph_button.grid(row=0, column=3, padx=5)
graph_button.bind("<Enter>", lambda e: on_hover(e, graph_button, "purple"))
graph_button.bind("<Leave>", lambda e: on_leave(e, graph_button, "lightgray"))

root.mainloop()
