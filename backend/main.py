# main.py
import io
import os
import zipfile
import pickle
import shutil
from datetime import datetime
from typing import List, Tuple, Optional

import cv2
import numpy as np
import face_recognition

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# ----------------- Paths -----------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")                # .pickle per user (list of encodings)
SNAP_DIR = os.path.join(BASE_DIR, "snapshots")       # saved images
LOGS_DIR = os.path.join(BASE_DIR, "logs")            # csv logs

for p in (DB_DIR, SNAP_DIR, LOGS_DIR):
    os.makedirs(p, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, "attendance.csv")
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("timestamp,event,user,match,extra\n")

# ----------------- App -----------------
app = FastAPI(title="Face Attendance API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# ----------------- Pydantic Models -----------------
class SearchIn(BaseModel):
    embedding: List[float]
    threshold: float = 0.6


# ----------------- Helpers -----------------
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_log(event: str, user: str, match: bool, extra: str = ""):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now_str()},{event},{user},{int(match)},{extra}\n")

def read_image_from_upload(file: UploadFile) -> np.ndarray:
    """Read UploadFile -> OpenCV BGR image."""
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    return img

def get_face_encodings_bgr(img_bgr: np.ndarray) -> List[np.ndarray]:
    """Return list of face encodings using proper RGB conversion, with a fallback model."""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb, model="hog")
    if not boxes:
        boxes = face_recognition.face_locations(rgb, model="cnn")

    if not boxes:
        return []
    encs = face_recognition.face_encodings(rgb, known_face_locations=boxes)
    return encs or []

def list_users() -> List[str]:
    return [os.path.splitext(fn)[0] for fn in os.listdir(DB_DIR) if fn.endswith(".pickle")]

def load_user_encodings(name: str) -> List[np.ndarray]:
    p = os.path.join(DB_DIR, f"{name}.pickle")
    if not os.path.exists(p):
        return []
    with open(p, "rb") as f:
        data = pickle.load(f)
    return [np.asarray(v, dtype=np.float64) for v in data]

def save_user_encodings(name: str, encs: List[np.ndarray]):
    p = os.path.join(DB_DIR, f"{name}.pickle")
    with open(p, "wb") as f:
        pickle.dump([np.asarray(v, dtype=np.float64) for v in encs], f, protocol=pickle.HIGHEST_PROTOCOL)

def best_match(enc: np.ndarray, user_names: List[str], tolerance: float = 0.6) -> Tuple[str, bool, float]:
    """Return (name, matched?, distance)."""
    best_name, best_dist = "unknown_person", 1.0
    matched = False
    for name in user_names:
        refs = load_user_encodings(name)
        if not refs:
            continue
        dists = face_recognition.face_distance(refs, enc)
        d = float(np.min(dists))
        if d < best_dist:
            best_dist = d
            best_name = name
    if best_dist <= tolerance:
        matched = True
    return best_name, matched, best_dist

def preprocess_image(img_bgr: np.ndarray) -> np.ndarray:
    """Enhances image for better face detection using CLAHE."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    return cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)

def _best_user_for_embedding(enc_vec: np.ndarray, user_names: List[str], tol: float) -> Tuple[str, bool, float]:
    """Helper to match a single embedding vector against DB."""
    best_name, matched, best_dist = "unknown_person", False, 1.0
    for name in user_names:
        refs = load_user_encodings(name)
        if not refs:
            continue
        d = float(np.min(face_recognition.face_distance(refs, enc_vec)))
        if d < best_dist:
            best_name, best_dist = name, d
    matched = best_dist <= tol
    return best_name, matched, best_dist


# ----------------- Endpoints -----------------
@app.get("/health")
def health():
    return {"ok": True, "users": list_users()}


# ---- New: return a 128-D embedding for an uploaded face image
@app.post("/embed")
def embed(file: UploadFile = File(...)):
    """
    Body: multipart/form-data with 'file' (image)
    Response: { "embedding": [ ...128 floats... ] }
    """
    img = read_image_from_upload(file)
    enhanced_img = preprocess_image(img)
    encs = get_face_encodings_bgr(enhanced_img)

    if len(encs) == 0:
        raise HTTPException(status_code=400, detail="No face found")
    if len(encs) > 1:
        raise HTTPException(status_code=400, detail="Multiple faces found")

    return {"embedding": encs[0].astype(float).tolist()}


@app.post("/enroll")
def enroll(
    userName: str = Form(...),
    file: UploadFile = File(...),
    # Optional additional fields (accepted but not required)
    fullName: Optional[str] = Form(None),
    age: Optional[str] = Form(None),
    condition: Optional[str] = Form(None),
    contact: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None)
):
    """
    Register (or add a new sample for) a user's face.
      - Body: multipart/form-data with 'file' (image) and 'userName' (string)
      - Extra fields are accepted and ignored by the face store (Node handles Mongo).
    """
    name = userName.strip()
    if not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "Username is empty."})

    img = read_image_from_upload(file)
    enhanced_img = preprocess_image(img)
    encs = get_face_encodings_bgr(enhanced_img)

    if len(encs) == 0:
        save_log("enroll_fail", name, False, "no_face")
        return JSONResponse(status_code=400, content={"success": False, "error": "No face found in the image."})
    if len(encs) > 1:
        save_log("enroll_fail", name, False, "multiple_faces")
        return JSONResponse(status_code=400, content={"success": False, "error": "Multiple faces found. Please use a single-face image."})

    enc = encs[0]
    existing = load_user_encodings(name)
    existing.append(enc)
    save_user_encodings(name, existing)

    save_log("enroll", name, True, f"encodings={len(existing)}")
    # Return a lightweight "patient" object (userName + optional fullName)
    return JSONResponse(content={
        "success": True,
        "patient": {"userName": name, "fullName": fullName or name},
        "message": f"Registered/updated '{name}'. Total samples: {len(existing)}."
    })


# ---- Upgraded: one /search endpoint that supports BOTH JSON and multipart modes
@app.post("/search")
async def search(request: Request, file: UploadFile = File(None)):
    """
    Authenticate a user via face recognition.

    Supports two modes:
    1) JSON body:
       { "embedding": [...128 floats...], "threshold": 0.6 }
    2) multipart/form-data with 'file' (image)
    """
    ct = request.headers.get("content-type", "")

    # ---- JSON mode: {embedding, threshold}
    if "application/json" in ct:
        data = await request.json()
        try:
            payload = SearchIn(**data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON for search")

        if not payload.embedding or len(payload.embedding) != 128:
            raise HTTPException(status_code=400, detail="Invalid embedding")

        users = list_users()
        if not users:
            save_log("search_fail", "unknown_person", False, "no_users_in_db")
            return {"match": False, "patient": None, "distance": None, "message": "No users enrolled in the system."}

        enc_vec = np.asarray(payload.embedding, dtype=np.float64)
        name, matched, dist = _best_user_for_embedding(enc_vec, users, payload.threshold)
        if matched:
            save_log("search", name, True, f"dist={dist:.3f}")
            return {"match": True, "patient": {"userName": name}, "distance": dist, "message": f"Welcome back {name}!"}
        else:
            save_log("search_fail", "unknown_person", False, f"best={name}, dist={dist:.3f}")
            return {"match": False, "patient": {"userName": "unknown_person"}, "distance": dist, "message": "Unknown user."}

    # ---- multipart/form-data mode: 'file'
    elif "multipart/form-data" in ct:
        if file is None:
            raise HTTPException(status_code=400, detail="No file part in form-data")

        img = read_image_from_upload(file)
        enhanced_img = preprocess_image(img)
        encs = get_face_encodings_bgr(enhanced_img)

        if len(encs) == 0:
            save_log("search_fail", "unknown_person", False, "no_face")
            return {"match": False, "patient": None, "message": "No face found."}

        if len(encs) > 1:
            # take largest face
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")
            if boxes:
                boxes = sorted(boxes, key=lambda b: (b[2]-b[0])*(b[1]-b[3]), reverse=True)
                encs = face_recognition.face_encodings(rgb, known_face_locations=[boxes[0]])

        enc = encs[0]
        users = list_users()
        if not users:
            save_log("search_fail", "unknown_person", False, "no_users_in_db")
            return {"match": False, "patient": None, "message": "No users enrolled in the system."}

        name, matched, dist = best_match(enc, users, tolerance=0.6)

        if matched:
            save_log("search", name, True, f"dist={dist:.3f}")
            return {"match": True, "patient": {"userName": name}, "distance": dist, "message": f"Welcome back {name}!"}
        else:
            save_log("search_fail", "unknown_person", False, f"best={name}, dist={dist:.3f}")
            return {"match": False, "patient": {"userName": "unknown_person"}, "distance": dist, "message": "Unknown user."}

    # ---- Unsupported content-type
    else:
        raise HTTPException(status_code=415, detail="Unsupported Content-Type for /search")


@app.get("/get_attendance_logs")
def get_attendance_logs():
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(LOG_FILE):
            zf.write(LOG_FILE, arcname="logs/attendance.csv")
    mem.seek(0)
    headers = {"Content-Disposition": "attachment; filename=logs.zip"}
    return StreamingResponse(mem, media_type="application/zip", headers=headers)


@app.delete("/admin/clear_all")
def admin_clear_all():
    """Danger: wipe database & snapshots & logs (for testing)."""
    for d in (DB_DIR, SNAP_DIR, LOGS_DIR):
        if os.path.exists(d):
            shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("timestamp,event,user,match,extra\n")
    return {"ok": True, "message": "All data cleared."}
