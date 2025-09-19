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
    detections: List[Tuple[int, int, int, int, str, float, bool, str]],
) -> Dict[str, Any]:
    h, w = frame.shape[:2]
    payload: Dict[str, Any] = {"frame_size": [int(w), int(h)], "detections": []}

    for (x, y, ww, hh, label, conf, is_match, category) in detections:
        # Color by category: citizen=yellow, official=green, criminal=red, unknown=red
        if is_match:
            if category == "official":
                color = (0, 255, 0)
            elif category == "citizen":
                color = (0, 255, 255)
            elif category == "criminal":
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)
        else:
            # Unknown: orange (BGR for OpenCV)
            color = (0, 165, 255)
        cv2.rectangle(frame, (x, y), (x + ww, y + hh), color, 2)

        # Compose readable tag
        if is_match:
            if category == "official":
                text = f"Official: {label} ({conf:.1f})"
            elif category == "citizen":
                text = f"Citizen: {label} ({conf:.1f})"
            elif category == "criminal":
                text = f"Criminal: {label} ({conf:.1f})"
            else:
                text = f"Known: {label} ({conf:.1f})"
        else:
            text = "Intruder"

        # Draw a filled background for text for visibility
        (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        text_x = x
        text_y = y - 10 if y - 10 > 10 else y + hh + th + 6
        cv2.rectangle(
            frame,
            (text_x - 2, text_y - th - 4),
            (text_x + tw + 2, text_y + baseline),
            (0, 0, 0),
            thickness=-1,
        )
        cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

        payload["detections"].append(
            {
                "label": label if is_match else "unknown",
                "confidence": float(conf),
                "bbox": [int(x), int(y), int(ww), int(hh)],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "face_match": bool(is_match),
                "category": category if is_match else "unknown",
                "alert": True if (is_match and category == "criminal") or (not is_match) else False,
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

            found: List[Tuple[int, int, int, int, str, float, bool, str]] = []

            if len(rects) > 0:
                # Within each person bbox, try finding faces
                for (px, py, pw, ph) in rects:
                    roi = frame[py : py + ph, px : px + pw]
                    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(
                        gray_roi, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50)
                    )

                    for (fx, fy, fw, fh) in faces:
                        # Coordinates relative to full frame
                        x, y, w, h = px + fx, py + fy, fw, fh
                        face_crop_gray = gray_full[y : y + h, x : x + w]

                        label, confidence, is_match, category = face_db.match_face(face_crop_gray)
                        found.append((x, y, w, h, label, confidence, is_match, category))
            else:
                # Fallback: detect faces on the whole frame if no persons detected
                faces = face_cascade.detectMultiScale(
                    gray_full, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50)
                )
                for (x, y, w, h) in faces:
                    face_crop_gray = gray_full[y : y + h, x : x + w]
                    label, confidence, is_match, category = face_db.match_face(face_crop_gray)
                    found.append((x, y, w, h, label, confidence, is_match, category))

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


