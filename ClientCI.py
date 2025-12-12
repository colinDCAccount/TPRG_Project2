# Colin Innes - TPRG2131 Project 2
# Sends 5 vcgencmd readings + iteration count to the server.
# Runs on Raspberry Pi only.

import json
import socket
import subprocess
import sys
import time
import platform
import tkinter as tk

HOST = "127.0.0.1"
PORT = 50007
ITERATIONS = 50
INTERVAL_SEC = 2


# Just checks if this is a Pi (Linux)
def running_on_pi():
    return platform.system() == "Linux"


# Run a vcgencmd command and return its text
def get_vcgencmd_output(command):
    return subprocess.check_output(command, shell=True, text=True).strip()


# Read all 5 Pi stats + iteration number
def collate_readings(iteration):
    temp_raw = get_vcgencmd_output("vcgencmd measure_temp")
    volts_raw = get_vcgencmd_output("vcgencmd measure_volts core")
    arm_raw = get_vcgencmd_output("vcgencmd measure_clock arm")
    core_raw = get_vcgencmd_output("vcgencmd measure_clock core")
    mem_raw = get_vcgencmd_output("vcgencmd get_mem arm")

    temp_c = float(temp_raw.split("=")[1].split("'")[0])
    volts = float(volts_raw.split("=")[1].split("V")[0])
    arm_mhz = int(arm_raw.split("=")[1]) // 1_000_000
    core_mhz = int(core_raw.split("=")[1]) // 1_000_000
    mem_mb = int(mem_raw.split("=")[1].split("M")[0])

    return {
        "temperature_c": f"{temp_c:.1f}",
        "core_volts": f"{volts:.1f}",
        "arm_clock_mhz": str(arm_mhz),
        "core_clock_mhz": str(core_mhz),
        "arm_mem_mb": str(mem_mb),
        "iteration": iteration
    }


# Simple GUI (LED + status + exit)
def create_client_gui():
    root = tk.Tk()
    root.title("ClientCI")

    status_label = tk.Label(root, text="Client: Not connected")
    status_label.pack(padx=10, pady=(10, 5))

    led_label = tk.Label(root, text="●", font=("Arial", 24), fg="grey")
    led_label.pack(padx=10, pady=5)

    exit_button = tk.Button(root, text="Exit")
    exit_button.pack(padx=10, pady=(5, 10))

    return root, status_label, led_label, exit_button


def main():
    # Don’t run on a PC
    if not running_on_pi():
        print("This client is intended to run on a Raspberry Pi. Exiting.")
        sys.exit(0)

    root, status_label, led_label, exit_button = create_client_gui()

    user_exit = {"stop": False}

    def on_exit():
        user_exit["stop"] = True

    exit_button.config(command=on_exit)

    sock = None
    led_on = False

    try:
        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        status_label.config(text="Client: Connected")

        print("Client connected, starting sends...")

        for i in range(1, ITERATIONS + 1):
            if user_exit["stop"]:
                break

            data = collate_readings(i)
            msg = json.dumps(data) + "\n"
            sock.sendall(msg.encode("utf-8"))

            # Blink LED so user sees activity
            led_on = not led_on
            led_label.config(fg="green" if led_on else "grey")

            root.update_idletasks()
            root.update()

            time.sleep(INTERVAL_SEC)

        print("Done sending. Closing client.")

    except Exception as e:
        print("Client error:", e)

    finally:
        # Close socket cleanly
        if sock:
            try:
                sock.close()
            except:
                pass

        led_label.config(fg="grey")
        status_label.config(text="Finished")

        try:
            root.update_idletasks()
            root.update()
            time.sleep(1)
            root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    main()
