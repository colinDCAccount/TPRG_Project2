# Colin Innes - TPRG2131 Project 2
# Receives JSON data from ClientCI.py and shows it in a GUI.
# Can run on a Pi or on a regular PC.

import json
import socket
import tkinter as tk

HOST = "127.0.0.1"
PORT = 50007
BUF_SIZE = 1024


# Build the GUI once and keep references to the important widgets
def create_server_gui():
    root = tk.Tk()
    root.title("ServerCI")

    # Text labels on the left
    tk.Label(root, text="Temperature (°C):").grid(row=0, column=0, sticky="e", padx=5, pady=3)
    tk.Label(root, text="Core volts (V):").grid(row=1, column=0, sticky="e", padx=5, pady=3)
    tk.Label(root, text="ARM clock (MHz):").grid(row=2, column=0, sticky="e", padx=5, pady=3)
    tk.Label(root, text="Core clock (MHz):").grid(row=3, column=0, sticky="e", padx=5, pady=3)
    tk.Label(root, text="ARM mem (MB):").grid(row=4, column=0, sticky="e", padx=5, pady=3)
    tk.Label(root, text="Iteration:").grid(row=5, column=0, sticky="e", padx=5, pady=3)

    # Value labels on the right
    temp_val = tk.Label(root, text="---")
    volt_val = tk.Label(root, text="---")
    arm_val = tk.Label(root, text="---")
    core_val = tk.Label(root, text="---")
    mem_val = tk.Label(root, text="---")
    iter_val = tk.Label(root, text="---")

    temp_val.grid(row=0, column=1, sticky="w", padx=5, pady=3)
    volt_val.grid(row=1, column=1, sticky="w", padx=5, pady=3)
    arm_val.grid(row=2, column=1, sticky="w", padx=5, pady=3)
    core_val.grid(row=3, column=1, sticky="w", padx=5, pady=3)
    mem_val.grid(row=4, column=1, sticky="w", padx=5, pady=3)
    iter_val.grid(row=5, column=1, sticky="w", padx=5, pady=3)

    # LED and status line
    led_label = tk.Label(root, text="●", font=("Arial", 24), fg="grey")
    led_label.grid(row=0, column=2, rowspan=3, padx=15, pady=5)

    status_label = tk.Label(root, text="Server: Waiting for client...")
    status_label.grid(row=6, column=0, columnspan=3, pady=(5, 5))

    # Exit button
    stop_flag = {"stop": False}

    def on_exit():
        stop_flag["stop"] = True

    exit_button = tk.Button(root, text="Exit", command=on_exit)
    exit_button.grid(row=7, column=0, columnspan=3, pady=(5, 10))

    widgets = {
        "root": root,
        "temp_val": temp_val,
        "volt_val": volt_val,
        "arm_val": arm_val,
        "core_val": core_val,
        "mem_val": mem_val,
        "iter_val": iter_val,
        "led": led_label,
        "status": status_label,
        "stop_flag": stop_flag
    }
    return widgets


def main():
    # Set up GUI
    ui = create_server_gui()
    root = ui["root"]
    temp_val = ui["temp_val"]
    volt_val = ui["volt_val"]
    arm_val = ui["arm_val"]
    core_val = ui["core_val"]
    mem_val = ui["mem_val"]
    iter_val = ui["iter_val"]
    led_label = ui["led"]
    status_label = ui["status"]
    stop_flag = ui["stop_flag"]

    led_on = False

    try:
        # Basic TCP server on localhost
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        server_socket.settimeout(1.0)

        print("Server listening on", (HOST, PORT))

        conn = None
        addr = None
        buffer = ""

        # Wait for a client
        while not stop_flag["stop"] and conn is None:
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                try:
                    root.update_idletasks()
                    root.update()
                except tk.TclError:
                    stop_flag["stop"] = True

        if conn is None:
            # User closed window before a connection
            server_socket.close()
            return

        print("Client connected from", addr)
        status_label.config(text=f"Server: Connected to {addr}")
        conn.settimeout(1.0)

        # Read loop (newline-delimited JSON)
        while not stop_flag["stop"]:
            try:
                chunk = conn.recv(BUF_SIZE)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    data = json.loads(line)

                    temp_val.config(text=data.get("temperature_c", "---"))
                    volt_val.config(text=data.get("core_volts", "---"))
                    arm_val.config(text=data.get("arm_clock_mhz", "---"))
                    core_val.config(text=data.get("core_clock_mhz", "---"))
                    mem_val.config(text=data.get("arm_mem_mb", "---"))
                    iter_val.config(text=str(data.get("iteration", "---")))

                    # Flip LED so user sees updates
                    led_on = not led_on
                    led_label.config(fg="green" if led_on else "grey")

                    root.update_idletasks()
                    root.update()

            except socket.timeout:
                # No data, just keep GUI alive
                try:
                    root.update_idletasks()
                    root.update()
                except tk.TclError:
                    stop_flag["stop"] = True

        print("Server: connection closed")
        status_label.config(text="Server: Connection closed")
        led_label.config(fg="grey")

        try:
            root.update_idletasks()
            root.update()
            root.after(1000, root.destroy)
            root.mainloop()
        except tk.TclError:
            pass

    except Exception as e:
        # Simple error print for marking
        print("Server error:", e)


if __name__ == "__main__":
    main()
