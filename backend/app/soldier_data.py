import random
import threading
import time
from typing import List, Dict, Optional


_thread: Optional[threading.Thread] = None
_stop_event: Optional[threading.Event] = None
_soldiers: List[Dict] = []


def _init_soldiers() -> None:
    global _soldiers
    # Simple initial positions and vitals
    _soldiers = [
        {"id": "S1", "name": "Alpha", "status": "ok", "heart_rate": 72, "gps": [28.6129, 77.2295]},
        {"id": "S2", "name": "Bravo", "status": "ok", "heart_rate": 75, "gps": [28.6130, 77.2296]},
        {"id": "S3", "name": "Charlie", "status": "ok", "heart_rate": 70, "gps": [28.6131, 77.2297]},
        {"id": "S4", "name": "Delta", "status": "ok", "heart_rate": 73, "gps": [28.6132, 77.2298]},
    ]


def _simulate_loop() -> None:
    statuses = ["ok", "ok", "ok", "warn", "ok", "ok", "ok", "critical"]
    try:
        while _stop_event and not _stop_event.is_set():
            for s in _soldiers:
                # Random walk for GPS
                lat, lon = s["gps"]
                lat += random.uniform(-0.0002, 0.0002)
                lon += random.uniform(-0.0002, 0.0002)
                s["gps"] = [round(lat, 6), round(lon, 6)]

                # Heart rate jitter
                s["heart_rate"] = max(55, min(160, int(random.gauss(s["heart_rate"], 1.5))))

                # Occasionally change status
                if random.random() < 0.2:
                    s["status"] = random.choice(statuses)

            time.sleep(3.0)
    finally:
        return


def start_simulator() -> None:
    global _thread, _stop_event
    if _thread and _thread.is_alive():
        return
    _init_soldiers()
    _stop_event = threading.Event()
    _thread = threading.Thread(target=_simulate_loop, daemon=True)
    _thread.start()


def stop_simulator() -> None:
    global _thread, _stop_event
    if _stop_event:
        _stop_event.set()
    if _thread and _thread.is_alive():
        _thread.join(timeout=1.0)
    _thread = None
    _stop_event = None


def get_soldiers() -> List[Dict]:
    return _soldiers


