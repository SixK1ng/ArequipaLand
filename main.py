import time
import threading
import serial
from mouse import connect_to_com_port, find_com_port, listen_makcu, close_com_port, log
from colorbot import Colorbot
from screen_capture import ScreenCapture
import json

# Configuración del archivo JSON
with open('config.json') as config_file:
    config = json.load(config_file)

# Variables globales
aim_enabled = True  # Habilitar el aim del colorbot
trigger_enabled = True  # Habilitar el trigger
x, y = 0, 0  # Coordenadas para la captura de pantalla
grabzone = 500  # Tamaño de la zona de captura
color = config["ENEMY_COLOR"]  # Color para el bot, por ejemplo "Purple", "Red", "Yellow"
fov = config["FOV"]
resolution = config["RESOLUTION"]

# Mapa de botones para visualizar en consola
button_map = {
    0: 'Left Mouse Button',
    1: 'Right Mouse Button',
    2: 'Middle Mouse Button',
    3: 'Side Mouse 4 Button',
    4: 'Side Mouse 5 Button'
}
RED, GREEN, RESET = "\033[91m", "\033[92m", "\033[0m"

log_messages = []
LOG_LIMIT = 20

# Función para mostrar el log
def log(message):
    global log_messages
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    log_messages.append(entry)
    if len(log_messages) > LOG_LIMIT:
        log_messages.pop(0)
    print(entry, flush=True)

# Función para imprimir la salida en consola con estado de los botones
def print_debug_output(button_states):
    print("\033[H\033[J", end="")  # Clear screen
    debug_output = f"Port: {current_com_port or 'None'} | Baud Rate: {current_baud_rate or 'None'} | Connected: {is_connected}\n\n"
    debug_output += "---== Log ==---\n"
    debug_output += "\n".join(log_messages) + "\n"
    debug_output += "---== Button States ==---\n"
    for bit, name in button_map.items():
        state = button_states.get(bit, False)
        color = GREEN if state else RED
        state_str = "Pressed" if state else "Unpressed"
        debug_output += f"{name}: {color}{state_str}{RESET}\n"
    debug_output += "---== Button States ==---"
    print(debug_output)

# Función para conectar al puerto COM
def connect_to_com_port(port):
    global makcu, is_connected, current_com_port, current_baud_rate
    if not is_connected:
        makcu = open_serial_port(port, 115200)
        if makcu:
            current_com_port, current_baud_rate = port, 115200
            log(f"Connected to {port} at 115200.")
            change_baud_rate_to_4M()
        else:
            log(f"Initial connection to {port} at 115200 failed.")

# Función para cambiar la tasa de baudios a 4M
def change_baud_rate_to_4M():
    global makcu, current_baud_rate, is_connected
    if makcu and makcu.is_open:
        log("Sending baud rate switch command to 4M.")
        makcu.write(baud_change_command)
        makcu.flush()
        makcu.close()
        time.sleep(0.1)
        makcu = open_serial_port(makcu.name, 4000000)
        if makcu:
            current_baud_rate = 4000000
            is_connected = True
            log("Switched to 4M baud successfully.")
        else:
            is_connected = False
            log("Failed to reopen port at 4M baud.")

# Función para encontrar el puerto COM
def find_com_port():
    log("Searching for CH343 device...")
    for port in serial.tools.list_ports.comports():
        if "USB-Enhanced-SERIAL CH343" in port.description:
            log(f"Device found: {port.device}")
            return port.device
    log("Device not found.")
    return None

# Función principal
def main():
    global current_com_port
    current_com_port = find_com_port()
    
    if not current_com_port and fallback_com_port:
        log(f"Falling back to port: {fallback_com_port}")
        current_com_port = fallback_com_port

    if current_com_port:
        connect_to_com_port(current_com_port)
        if is_connected:
            with makcu_lock:
                log("Sending init command: km.buttons(1)")
                makcu.write(b"km.buttons(1)\r")
                makcu.flush()

            global listener_thread
            listener_thread = threading.Thread(target=listen_makcu)
            listener_thread.daemon = True
            listener_thread.start()

            # Iniciamos el Colorbot
            colorbot = Colorbot(x, y, grabzone, color, aim_enabled, trigger_enabled)

            while True:
                # Simulación de salida en consola
                print(f"Port: {current_com_port} | Baud Rate: 4000000 | Connected: True")
                print("\n---== Log ==---")
                time.sleep(1)
                log(f"[{time.strftime('%H:%M:%S')}] Searching for CH343 device...")
                log(f"[{time.strftime('%H:%M:%S')}] Device found: {current_com_port}")
                log(f"[{time.strftime('%H:%M:%S')}] Trying to open {current_com_port} at 115200 baud.")
                log(f"[{time.strftime('%H:%M:%S')}] Connected to {current_com_port} at 115200.")
                log(f"[{time.strftime('%H:%M:%S')}] Sending baud rate switch command to 4M.")
                log(f"[{time.strftime('%H:%M:%S')}] Trying to open {current_com_port} at 4000000 baud.")
                log(f"[{time.strftime('%H:%M:%S')}] Switched to 4M baud successfully.")
                log(f"[{time.strftime('%H:%M:%S')}] Sending init command: km.buttons(1)")
                log(f"[{time.strftime('%H:%M:%S')}] Started listening thread for button states.")
                time.sleep(5)

        else:
            log("Failed to connect to the device.")
            print_debug_output({i: False for i in button_map})
    else:
        log("No COM port available. Cannot proceed.")
        print_debug_output({i: False for i in button_map})

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("KeyboardInterrupt: Closing COM Port.")
        close_com_port()
        if listener_thread:
            listener_thread.join()
        log("Program terminated gracefully.")
        print_debug_output({i: False for i in button_map})
