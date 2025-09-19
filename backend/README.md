## VeerDrishti Backend (FastAPI + OpenCV)

Minimal backend that:
- Serves live annotated camera frames at `/api/frame.jpg`
- Serves detection JSON at `/api/detections`
- Registers faces via `/api/register-face` (multipart: `id`, `file`)
- Lists registered IDs at `/api/faces`
- Simulates soldier telemetry at `/api/soldiers`

### Prerequisites
- Python 3.9+ recommended
- A working webcam (default camera index is 0). Override with env var `CAMERA_INDEX`.

### Setup and Run
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the API (host 0.0.0.0 for LAN access)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open these in the browser once running:
- Frame: `http://localhost:8000/api/frame.jpg`
- Detections: `http://localhost:8000/api/detections`
- Soldiers: `http://localhost:8000/api/soldiers`

### Notes
- Face recognizer uses LBPH (opencv-contrib). Images are stored under `backend/data/faces/{id}/`.
- Trained model is persisted at `backend/data/lbph_model.yml` with labels in `backend/data/labels.pkl`.

