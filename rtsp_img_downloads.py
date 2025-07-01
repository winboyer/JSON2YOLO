import os
import requests
from datetime import datetime
import cv2
import time
import re

def capture_rtsp_image(rtsp_url, save_dir):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise Exception(f"Cannot open RTSP stream: {rtsp_url}")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise Exception("Failed to capture image from RTSP stream.")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_dir, f"snapshot_{timestamp}.jpg")
    cv2.imwrite(filename, frame)
    return filename

if __name__ == "__main__":
    # 支持多个RTSP流
    rtsp_urls = [
        "rtsp://admin:a1234567@192.168.1.182:554",
        "rtsp://admin:a1234567@192.168.1.154:554",
        # 可以在这里添加更多的RTSP流地址
        # "rtsp://user:password@ip:port",
    ]
    save_dir = './snapshots'
    while True:
        for idx, rtsp_url in enumerate(rtsp_urls):
            try:
                # 解析rtsp_url中的ip，并取最后一段
                device_id = rtsp_url.split('.')[-1].split(":")[0]
                print(device_id)
            except Exception as e:
                print(f"Error capturing from camera {idx+1}: {e}")
        time.sleep(10)
