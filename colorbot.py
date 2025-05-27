import time, os, threading
from screen_capture import ScreenCapture
from mouse import PicoMouse

class Colorbot:
    def __init__(self, x, y, grabzone, color, aim_enabled, trigger_enabled):
        # Color definitions
        if color == "Purple":
            self.LOWER_COLOR = np.array([140, 110, 150])  # Lower bound for purple color
            self.UPPER_COLOR = np.array([150, 195, 255])  # Upper bound for purple color
        elif color == "Red":
            self.LOWER_COLOR = np.array([0, 100, 100])  # Lower bound for red color
            self.UPPER_COLOR = np.array([10, 255, 255])  # Upper bound for red color
        elif color == "Yellow":
            self.LOWER_COLOR = np.array([30, 125, 150])  # Lower bound for yellow color
            self.UPPER_COLOR = np.array([30, 255, 255])  # Upper bound for yellow color
        else:
            raise ValueError("Unsupported color specified. Choose from 'Purple', 'Red', 'Yellow'.")

        self.aim_enabled = aim_enabled
        self.trigger_enabled = trigger_enabled
        self.makcu_mouse = MakcuMouse()  # Instanciamos la clase MakcuMouse para control del ratón
        self.grabber = ScreenCapture(x, y, grabzone)  
        threading.Thread(target=self.run, daemon=True).start()
        self.toggled = False 

    def toggle(self):
        self.toggled = not self.toggled 
        time.sleep(0.2) 

    # Threaded keychecker
    def run(self):
        while True:
            if self.aim_enabled: 
                self.process("move") 

    def process(self, action):
        screen = self.grabber.get_screen()  
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)  
        mask = cv2.inRange(hsv, self.LOWER_COLOR, self.UPPER_COLOR) 
        dilated = cv2.dilate(mask, None, iterations=5)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:  # No enemies detected
            return

        # Find the topmost outline (head)
        contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(contour)  
        center = (x + w // 2, y + h // 2)  

        if action == "move":
            # Calculate differences for mouse movement based on contour center
            cX = x + w // 2
            cY = y + 9  
            x_diff = cX - self.grabber.grabzone // 2 
            y_diff = cY - self.grabber.grabzone // 2 
            self.makcu_mouse.move(x_diff * 0.2, y_diff * 0.2)  # Move mouse with scaling

    def close(self):
        if hasattr(self, 'makcu_mouse'):
            self.makcu_mouse.close()  
        self.toggled = False 

    def __del__(self):
        self.close()