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
        {"id": "S1", "name": "Alpha", "status": "ok", "heart_rate": 78, "gps": [28.6129, 77.2295], "activity": "patrol", "_hr_history": []},
        {"id": "S2", "name": "Bravo", "status": "ok", "heart_rate": 82, "gps": [28.6130, 77.2296], "activity": "rest", "_hr_history": []},
        {"id": "S3", "name": "Charlie", "status": "ok", "heart_rate": 76, "gps": [28.6131, 77.2297], "activity": "jog", "_hr_history": []},
        {"id": "S4", "name": "Delta", "status": "ok", "heart_rate": 80, "gps": [28.6132, 77.2298], "activity": "patrol", "_hr_history": []},
    ]


def _simulate_loop() -> None:
    # Activity model: drives heart rate and movement
    activity_targets = {
        "rest": {"hr": 72, "speed": 0.0},
        "patrol": {"hr": 88, "speed": 0.00015},
        "jog": {"hr": 110, "speed": 0.00035},
        "sprint": {"hr": 150, "speed": 0.0007},
        "engaged": {"hr": 140, "speed": 0.00025},
        "injured": {"hr": 135, "speed": 0.00005},
    }
    try:
        while _stop_event and not _stop_event.is_set():
            for s in _soldiers:
                # Possibly change activity with small probabilities
                act = s.get("activity", "patrol")
                r = random.random()
                if act in ("rest", "patrol") and r < 0.08:
                    act = random.choices(["patrol", "jog"], [0.6, 0.4])[0]
                elif act == "jog" and r < 0.10:
                    act = random.choices(["patrol", "sprint"], [0.7, 0.3])[0]
                elif act == "sprint" and r < 0.25:
                    act = "jog"
                # Engagement event
                if r < 0.03:
                    act = "engaged"
                # Injury event (rare)
                if r < 0.01:
                    act = "injured"
                # Recovery from injured
                if act == "injured" and random.random() < 0.08:
                    act = "rest"
                s["activity"] = act

                # Movement based on activity speed
                speed = activity_targets[act]["speed"]
                lat, lon = s["gps"]
                lat += random.uniform(-speed, speed)
                lon += random.uniform(-speed, speed)
                s["gps"] = [round(lat, 6), round(lon, 6)]

                # Heart rate dynamics towards activity target with noise
                hr = s.get("heart_rate", 80)
                target = activity_targets[act]["hr"]
                # Move 15% towards target + noise
                hr = hr + (target - hr) * 0.15 + random.gauss(0.0, 2.0)
                hr = int(max(50, min(190, hr)))
                s["heart_rate"] = hr
                # Track short HR history for status smoothing
                hist = s.get("_hr_history", [])
                hist.append(hr)
                if len(hist) > 8:
                    hist.pop(0)
                s["_hr_history"] = hist

                # Derive status from activity and sustained HR
                avg8 = sum(hist) / len(hist)
                status = s.get("status", "ok")
                if act == "injured" or avg8 >= 150:
                    status = "critical"
                elif act in ("sprint", "engaged") or avg8 >= 120:
                    status = "warn"
                elif avg8 < 110 and act in ("rest", "patrol"):
                    status = "ok"
                s["status"] = status

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


