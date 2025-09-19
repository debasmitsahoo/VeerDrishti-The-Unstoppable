from fastapi import FastAPI, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from typing import Optional

from . import inference
from . import face_db
from . import soldier_data


# Create FastAPI app with permissive CORS for local development
app = FastAPI(title="VeerDrishti Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # Ensure data directories exist and try to load any existing model
    face_db.initialize()

    # Start background camera inference thread
    camera_index_str: str = os.getenv("CAMERA_INDEX", "0")
    try:
        camera_index: int = int(camera_index_str)
    except ValueError:
        camera_index = 0
    inference.start_inference(camera_index=camera_index)

    # Start background soldier simulator
    soldier_data.start_simulator()


@app.on_event("shutdown")
def on_shutdown() -> None:
    inference.stop_inference()
    soldier_data.stop_simulator()


@app.get("/api/frame.jpg", summary="Latest annotated camera frame as JPEG")
def get_frame_jpeg() -> Response:
    frame_bytes: Optional[bytes] = inference.get_latest_frame_jpeg()
    if not frame_bytes:
        return Response(status_code=204)
    return Response(content=frame_bytes, media_type="image/jpeg")


@app.get("/api/detections", summary="Latest detection results")
def get_detections() -> JSONResponse:
    payload = inference.get_latest_detections()
    if payload is None:
        payload = {"frame_size": [0, 0], "detections": []}
    return JSONResponse(payload)


@app.post("/api/register-face", summary="Register a face for a given ID")
async def register_face(id: str = Form(...), file: UploadFile = File(...)) -> JSONResponse:
    # Read uploaded image bytes
    content: bytes = await file.read()
    saved_count: int = face_db.register_face_from_bytes(person_id=id, image_bytes=content)
    return JSONResponse({"id": id, "faces_saved": saved_count})


@app.get("/api/faces", summary="List registered face IDs")
def list_faces() -> JSONResponse:
    ids = face_db.list_registered_ids()
    return JSONResponse({"ids": ids})


@app.get("/api/soldiers", summary="Get simulated soldier telemetry")
def get_soldiers() -> JSONResponse:
    data = soldier_data.get_soldiers()
    return JSONResponse({"soldiers": data})


# Health endpoint (optional)
@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


