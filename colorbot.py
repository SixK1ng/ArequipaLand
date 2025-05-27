import time
import threading
import numpy as np
import cv2
from screen_capture import initialize_ndi_receiver, get_ndi_frame, cleanup_ndi
from mouse import MakcuMouse

class Colorbot:
    def __init__(self, x, y, grabzone, color, aim_enabled):
        if color == "Purple":
            self.LOWER_COLOR = np.array([140, 110, 150])
            self.UPPER_COLOR = np.array([150, 195, 255])
        elif color == "Red":
            self.LOWER_COLOR = np.array([0, 100, 100])
            self.UPPER_COLOR = np.array([10, 255, 255])
        elif color == "Yellow":
            self.LOWER_COLOR = np.array([30, 125, 150])
            self.UPPER_COLOR = np.array([30, 255, 255])
        else:
            raise ValueError("Unsupported color specified. Choose from 'Purple', 'Red', 'Yellow'.")

        self.aim_enabled = aim_enabled
        self.makcu_mouse = MakcuMouse()
        self.recv, self.finder = initialize_ndi_receiver()
        self.grabzone = grabzone
        threading.Thread(target=self.run, daemon=True).start()
        self.toggled = False

    def toggle(self):
        self.toggled = not self.toggled
        time.sleep(0.2)

    def run(self):
        while True:
            if self.aim_enabled:
                self.process("move")

    def process(self, action):
        frame = get_ndi_frame(self.recv)
        if frame is None:
            return
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.LOWER_COLOR, self.UPPER_COLOR)
        dilated = cv2.dilate(mask, None, iterations=5)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:
            return

        contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(contour)

        if action == "move":
            cX = x + w // 2
            cY = y + 9
            x_diff = cX - self.grabzone // 2
            y_diff = cY - self.grabzone // 2
            self.makcu_mouse.move(x_diff * 0.2, y_diff * 0.2)

    def close(self):
        cleanup_ndi(self.recv, self.finder)
        self.toggled = False

    def __del__(self):
        self.close()
