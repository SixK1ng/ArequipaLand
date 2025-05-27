import time
import threading
import json
import mouse  # Importa el módulo completo
from colorbot import Colorbot

with open('config.json') as config_file:
    config = json.load(config_file)

aim_enabled = True
x, y = 0, 0
grabzone = 500
color = config.get("ENEMY_COLOR", "Red")
fov = config.get("FOV", 90)
resolution = config.get("RESOLUTION", [1920, 1080])

def main():
    while True:
        port = mouse.find_com_port()
        if not port and mouse.fallback_com_port:
            mouse.log(f"Falling back to port: {mouse.fallback_com_port}")
            port = mouse.fallback_com_port

        if port:
            mouse.connect_to_com_port(port)
            mouse.log(f"main sees is_connected: {mouse.is_connected}")
            if mouse.is_connected:
                with mouse.makcu_lock:
                    mouse.log("Sending init command: km.buttons(1)")
                    mouse.makcu.write(b"km.buttons(1)\r")
                    mouse.makcu.flush()

                listener_thread = threading.Thread(target=mouse.listen_makcu, daemon=True)
                listener_thread.start()

                colorbot = Colorbot(x, y, grabzone, color, aim_enabled)

                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    mouse.log("KeyboardInterrupt: Closing COM Port.")
                    mouse.close_com_port()
                    if listener_thread:
                        listener_thread.join()
                    mouse.log("Program terminated gracefully.")
                    mouse.print_debug_output({i: False for i in mouse.button_map})
                    break
            else:
                mouse.log("Failed to connect to the device.")
                mouse.print_debug_output({i: False for i in mouse.button_map})
                input("Presiona Enter para reintentar o cerrar...")
        else:
            mouse.log("No COM port available. Cannot proceed.")
            mouse.print_debug_output({i: False for i in mouse.button_map})
            input("Presiona Enter para reintentar o cerrar...")

if __name__ == "__main__":
    main()
