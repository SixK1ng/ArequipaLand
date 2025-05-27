import time
import numpy as np
import NDIlib as ndi
import cv2

# Initialize NDI
if not ndi.initialize():
    print("Failed to initialize NDI")
    exit(1)

# Create an NDI source finder
finder = ndi.find_create_v2()
# Wait up to 5 seconds to find available NDI sources
ndi.find_wait_for_sources(finder, 5000)
# Get the list of found NDI sources
sources = ndi.find_get_current_sources(finder)

# If no sources were found, exit
if not sources:
    print("No NDI sources found.")
    exit(1)

# Select the first available NDI source
source = sources[0]
# Configure NDI receiver settings
recv_settings = ndi.RecvCreateV3()
# Use the fastest color format
recv_settings.color_format = ndi.RECV_COLOR_FORMAT_FASTEST
# Use the lowest bandwidth to minimize latency
recv_settings.bandwidth = ndi.RECV_BANDWIDTH_LOWEST
# Create the NDI receiver
recv = ndi.recv_create_v3(recv_settings)

# Connect the receiver to the selected source
ndi.recv_connect(recv, source)
print(f"Connected to: {source.ndi_name}")

# Variables to track FPS
frame_count = 0
start_time = time.time()

while True:
    # Capture a video frame from the NDI source
    frame_type, video_frame, _, _ = ndi.recv_capture_v2(recv, 1000)

    if frame_type != ndi.FRAME_TYPE_VIDEO or video_frame is None:
        continue

    # Increment the frame count
    frame_count += 1

    # Calculate the FPS every second
    elapsed_time = time.time() - start_time
    if elapsed_time >= 1:
        fps = frame_count / elapsed_time
        print(f"[NDI] FPS: {fps:.0f}")
        frame_count = 0
        start_time = time.time()

    # Convert the frame data from bytes to a numpy array
    frame_yuv = np.frombuffer(video_frame.data, dtype=np.uint8).reshape(
        (video_frame.yres, video_frame.xres, 2)
    )
    # Convert YUV to BGR (OpenCV format)
    frame_bgr_fullres = cv2.cvtColor(frame_yuv, cv2.COLOR_YUV2BGR_UYVY)

    # Make a copy for processing (optional)
    frame_resized = frame_bgr_fullres.copy()

# Cleanup on close
ndi.recv_destroy(recv)
ndi.find_destroy(finder)
ndi.destroy()