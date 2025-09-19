from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pickle
import uuid

import cv2
import numpy as np


# Paths
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_DATA_DIR = _BACKEND_DIR / "data"
_FACES_DIR = _DATA_DIR / "faces"
_MODEL_PATH = _DATA_DIR / "lbph_model.yml"
_LABELS_PATH = _DATA_DIR / "labels.pkl"


_recognizer: Optional[cv2.face_LBPHFaceRecognizer] = None  # type: ignore[attr-defined]
_label_to_id: Dict[str, int] = {}
_id_to_label: Dict[int, str] = {}
_id_to_category: Dict[str, str] = {}

_VALID_CATEGORIES = {"citizen", "official", "criminal"}


def initialize() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _FACES_DIR.mkdir(parents=True, exist_ok=True)
    _load_model_if_exists()


def _create_recognizer():
    # Requires opencv-contrib-python
    return cv2.face.LBPHFaceRecognizer_create()


def _save_labels() -> None:
    with open(_LABELS_PATH, "wb") as f:
        pickle.dump({
            "label_to_id": _label_to_id,
            "id_to_label": _id_to_label,
            "id_to_category": _id_to_category,
        }, f)


def _load_labels() -> None:
    global _label_to_id, _id_to_label, _id_to_category
    if _LABELS_PATH.exists():
        with open(_LABELS_PATH, "rb") as f:
            data = pickle.load(f)
            _label_to_id = data.get("label_to_id", {})
            _id_to_label = data.get("id_to_label", {})
            _id_to_category = data.get("id_to_category", {})


def _load_model_if_exists() -> None:
    global _recognizer
    _load_labels()
    if _MODEL_PATH.exists():
        _recognizer = _create_recognizer()
        _recognizer.read(str(_MODEL_PATH))


def list_registered_ids() -> List[str]:
    initialize()
    ids: List[str] = []
    for p in _FACES_DIR.iterdir():
        if not p.is_dir():
            continue
        if p.name in _VALID_CATEGORIES:
            for sub in p.iterdir():
                if sub.is_dir():
                    ids.append(sub.name)
        else:
            ids.append(p.name)
    ids.sort()
    return ids


def _detect_faces(gray_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))
    return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]


def _prepare_face(gray_face: np.ndarray) -> np.ndarray:
    # Normalize face crop to a fixed size for recognizer
    face_resized = cv2.resize(gray_face, (100, 100))
    # Improve robustness across lighting by equalizing histogram
    face_eq = cv2.equalizeHist(face_resized)
    return face_eq


def register_face_from_bytes(person_id: str, image_bytes: bytes, category: str = "citizen") -> int:
    initialize()
    cat = (category or "citizen").strip().lower()
    if cat not in _VALID_CATEGORIES:
        cat = "citizen"
    np_buf = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(np_buf, cv2.IMREAD_COLOR)
    if img is None:
        return 0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    boxes = _detect_faces(gray)
    saved = 0

    # Save under faces/{category}/{id}
    person_dir = _FACES_DIR / cat / person_id
    person_dir.mkdir(parents=True, exist_ok=True)

    for (x, y, w, h) in boxes:
        crop = gray[y : y + h, x : x + w]
        crop = _prepare_face(crop)
        filename = person_dir / f"{uuid.uuid4().hex}.png"
        cv2.imwrite(str(filename), crop)
        saved += 1

    if saved > 0:
        train_from_disk()

    return saved


def train_from_disk() -> None:
    global _recognizer, _label_to_id, _id_to_label
    initialize()

    images: List[np.ndarray] = []
    labels: List[int] = []

    _label_to_id = {}
    _id_to_label = {}
    global _id_to_category
    _id_to_category = {}
    next_id = 0

    # Support both legacy faces/{id} and new faces/{category}/{id}
    for top in sorted(_FACES_DIR.iterdir()):
        if not top.is_dir():
            continue
        if top.name in _VALID_CATEGORIES:
            category = top.name
            for person_dir in sorted(top.iterdir()):
                if not person_dir.is_dir():
                    continue
                person_label = person_dir.name  # use ID as label
                _label_to_id[person_label] = next_id
                _id_to_label[next_id] = person_label
                _id_to_category[person_label] = category
                label_id = next_id
                next_id += 1

                for img_path in person_dir.glob("*.png"):
                    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        continue
                    img = _prepare_face(img)
                    images.append(img)
                    labels.append(label_id)
        else:
            # Legacy layout: treat as citizen by default
            person_dir = top
            person_label = person_dir.name
            _label_to_id[person_label] = next_id
            _id_to_label[next_id] = person_label
            _id_to_category[person_label] = "citizen"
            label_id = next_id
            next_id += 1

            for img_path in person_dir.glob("*.png"):
                img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                img = _prepare_face(img)
                images.append(img)
                labels.append(label_id)

    if len(images) == 0:
        # No data; reset recognizer
        _recognizer = None
        return

    _recognizer = _create_recognizer()
    _recognizer.train(images, np.array(labels))
    _recognizer.write(str(_MODEL_PATH))
    _save_labels()


def match_face(gray_face_crop: np.ndarray) -> Tuple[str, float, bool, str]:
    initialize()
    if gray_face_crop is None or gray_face_crop.size == 0:
        return ("unknown", 0.0, False, "unknown")

    face = _prepare_face(gray_face_crop)

    if _recognizer is None:
        _load_model_if_exists()
    if _recognizer is None or len(_id_to_label) == 0:
        return ("unknown", 0.0, False, "unknown")

    try:
        pred_label_id, confidence = _recognizer.predict(face)
    except cv2.error:
        return ("unknown", 0.0, False, "unknown")

    label = _id_to_label.get(int(pred_label_id), "unknown")
    # Lower confidence is better for LBPH. Relaxed threshold for better recall.
    threshold = 85.0
    is_match = float(confidence) < threshold
    category = _id_to_category.get(label, "citizen") if is_match else "unknown"
    return (label if is_match else "unknown", float(confidence), bool(is_match), category)


