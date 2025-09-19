import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from . import face_db


# Shared state for serving endpoints
_latest_frame_jpeg: Optional[bytes] = None
_latest_detections: Optional[Dict[str, Any]] = None

_thread: Optional[threading.Thread] = None
_stop_event: Optional[threading.Event] = None


def _get_haar_cascade() -> cv2.CascadeClassifier:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    return cv2.CascadeClassifier(cascade_path)


def _annotate_and_build_payload(
    frame: np.ndarray,
    detections: List[Tuple[int, int, int, int, str, float, bool]],
) -> Dict[str, Any]:
    h, w = frame.shape[:2]
    payload: Dict[str, Any] = {"frame_size": [int(w), int(h)], "detections": []}

    for (x, y, ww, hh, label, conf, is_match) in detections:
        color = (0, 255, 0) if is_match else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x + ww, y + hh), color, 2)
        text = f"{label} ({conf:.1f})" if is_match else "unknown"
        cv2.putText(frame, text, (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        payload["detections"].append(
            {
                "label": label if is_match else "unknown",
                "confidence": float(conf),
                "bbox": [int(x), int(y), int(ww), int(hh)],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "face_match": bool(is_match),
            }
        )

    return payload


def _inference_loop(camera_index: int) -> None:
    global _latest_frame_jpeg, _latest_detections

    # Initialize detectors
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    face_cascade = _get_haar_cascade()

    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    try:
        while _stop_event and not _stop_event.is_set():
            ok, frame = cap.read()
            if not ok or frame is None:
                time.sleep(0.2)
                continue

            # Person detection (full frame)
            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects, _ = hog.detectMultiScale(gray_full, winStride=(8, 8))

            found: List[Tuple[int, int, int, int, str, float, bool]] = []

            # Within each person bbox, try finding faces
            for (px, py, pw, ph) in rects:
                roi = frame[py : py + ph, px : px + pw]
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray_roi, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))

                for (fx, fy, fw, fh) in faces:
                    # Coordinates relative to full frame
                    x, y, w, h = px + fx, py + fy, fw, fh
                    face_crop_gray = gray_full[y : y + h, x : x + w]

                    label, confidence, is_match = face_db.match_face(face_crop_gray)
                    found.append((x, y, w, h, label, confidence, is_match))

            # Draw and package payload
            payload = _annotate_and_build_payload(frame, found)

            # Encode to JPEG for serving
            ok, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
                _latest_frame_jpeg = jpeg.tobytes()
            _latest_detections = payload

            # Run ~1 FPS
            time.sleep(1.0)
    finally:
        cap.release()


def start_inference(camera_index: int = 0) -> None:
    global _thread, _stop_event
    if _thread and _thread.is_alive():
        return
    _stop_event = threading.Event()
    _thread = threading.Thread(target=_inference_loop, args=(camera_index,), daemon=True)
    _thread.start()


def stop_inference() -> None:
    global _thread, _stop_event
    if _stop_event:
        _stop_event.set()
    if _thread and _thread.is_alive():
        _thread.join(timeout=2.0)
    _thread = None
    _stop_event = None


def get_latest_frame_jpeg() -> Optional[bytes]:
    return _latest_frame_jpeg


def get_latest_detections() -> Optional[Dict[str, Any]]:
    return _latest_detections


