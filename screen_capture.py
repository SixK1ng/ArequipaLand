import time
import numpy as np
import NDIlib as ndi
import cv2

def initialize_ndi_receiver():
    if not ndi.initialize():
        raise RuntimeError("Failed to initialize NDI")

    finder = ndi.find_create_v2()
    ndi.find_wait_for_sources(finder, 5000)
    sources = ndi.find_get_current_sources(finder)
    if not sources:
        raise RuntimeError("No NDI sources found.")

    source = sources[0]
    recv_settings = ndi.RecvCreateV3()
    recv_settings.color_format = ndi.RECV_COLOR_FORMAT_FASTEST
    recv_settings.bandwidth = ndi.RECV_BANDWIDTH_LOWEST
    recv = ndi.recv_create_v3(recv_settings)
    ndi.recv_connect(recv, source)
    print(f"Connected to: {source.ndi_name}")
    return recv, finder

def get_ndi_frame(recv, timeout=1000):
    frame_type, video_frame, _, _ = ndi.recv_capture_v2(recv, timeout)
    if frame_type != ndi.FRAME_TYPE_VIDEO or video_frame is None:
        return None
    frame_yuv = np.frombuffer(video_frame.data, dtype=np.uint8).reshape(
        (video_frame.yres, video_frame.xres, 2)
    )
    frame_bgr = cv2.cvtColor(frame_yuv, cv2.COLOR_YUV2BGR_UYVY)
    return frame_bgr

def cleanup_ndi(recv, finder):
    ndi.recv_destroy(recv)
    ndi.find_destroy(finder)
    ndi.destroy()

def show_ndi_fps():
    recv, finder = initialize_ndi_receiver()
    frame_count = 0
    start_time = time.time()
    try:
        while True:
            frame = get_ndi_frame(recv)
            if frame is not None:
                frame_count += 1
                elapsed_time = time.time() - start_time
                if elapsed_time >= 1:
                    fps = frame_count / elapsed_time
                    print(f"[NDI] FPS: {fps:.0f}")
                    frame_count = 0
                    start_time = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_ndi(recv, finder)

if __name__ == "__main__":
    show_ndi_fps()
