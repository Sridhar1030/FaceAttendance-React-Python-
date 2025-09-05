# main.py
import io
import os
import zipfile
import pickle
import shutil
from datetime import datetime
from typing import List, Tuple

import cv2
import numpy as np
import face_recognition

from fastapi import FastAPI, File, UploadFile, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

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
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

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
    """Return list of face encodings using proper RGB conversion."""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    # detect @ 1x (fast). If your faces are small, consider model='cnn' or upsample via locations
    boxes = face_recognition.face_locations(rgb, model="hog")
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
    # ensure np arrays
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

def save_snapshot(img_bgr: np.ndarray, user: str):
    user_dir = os.path.join(SNAP_DIR, user)
    os.makedirs(user_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out = os.path.join(user_dir, f"{ts}.jpg")
    cv2.imwrite(out, img_bgr)

# ----------------- Endpoints -----------------
@app.get("/health")
def health():
    return {"ok": True, "users": list_users()}

@app.post("/register_new_user")
def register_new_user(text: str = Query(..., min_length=1), file: UploadFile = File(...)):
    """
    Register a new user:
      - Query: ?text=<name>
      - Body:  multipart/form-data, field 'file' with an image
    """
    name = text.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is empty")

    img = read_image_from_upload(file)
    encs = get_face_encodings_bgr(img)

    if len(encs) == 0:
        save_log("register_fail", name, False, "no_face")
        return {"registration_status": 400, "error": "No face found. Try again."}
    if len(encs) > 1:
        save_log("register_fail", name, False, "multiple_faces")
        return {"registration_status": 400, "error": "Multiple faces found. Use a single-face image."}

    enc = encs[0]

    # Append to existing encodings if user exists (multi-sample enrollment helps robustness)
    existing = load_user_encodings(name)
    existing.append(enc)
    save_user_encodings(name, existing)

    # Save snapshot for record
    save_snapshot(img, name)

    save_log("register", name, True, f"encodings={len(existing)}")
    return {"registration_status": 200, "message": f"Registered/updated '{name}' with {len(existing)} sample(s)."}

@app.post("/login")
def login(file: UploadFile = File(...)):
    """
    Login with a face image:
      - Body: multipart/form-data, field 'file'
    """
    img = read_image_from_upload(file)
    encs = get_face_encodings_bgr(img)
    if len(encs) == 0:
        save_log("login_fail", "unknown_person", False, "no_face")
        return {"match_status": False, "user": "unknown_person", "distance": None, "message": "No face found."}
    if len(encs) > 1:
        # Choose the largest face (more stable)
        # Recompute boxes to pick largest
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        # sort by area
        boxes = sorted(boxes, key=lambda b: (b[2]-b[0])*(b[1]-b[3]), reverse=True)
        encs = face_recognition.face_encodings(rgb, known_face_locations=[boxes[0]])

    enc = encs[0]
    users = list_users()
    if not users:
        save_log("login_fail", "unknown_person", False, "no_users_in_db")
        return {"match_status": False, "user": "unknown_person", "distance": None, "message": "No users enrolled."}

    name, matched, dist = best_match(enc, users, tolerance=0.6)
    if matched:
        save_snapshot(img, name)
        save_log("login", name, True, f"dist={dist:.3f}")
        return {"match_status": True, "user": name, "distance": dist, "message": f"Welcome back {name}!"}
    else:
        save_log("login_fail", "unknown_person", False, f"best={name}, dist={dist:.3f}")
        return {"match_status": False, "user": "unknown_person", "distance": dist, "message": "Unknown user."}

@app.post("/logout")
def logout(file: UploadFile = File(...)):
    """
    Logout with a face image:
      - Body: multipart/form-data, field 'file'
    """
    img = read_image_from_upload(file)
    encs = get_face_encodings_bgr(img)
    if len(encs) == 0:
        save_log("logout_fail", "unknown_person", False, "no_face")
        return {"match_status": False, "user": "unknown_person", "distance": None, "message": "No face found."}
    enc = encs[0]

    users = list_users()
    if not users:
        save_log("logout_fail", "unknown_person", False, "no_users_in_db")
        return {"match_status": False, "user": "unknown_person", "distance": None, "message": "No users enrolled."}

    name, matched, dist = best_match(enc, users, tolerance=0.6)
    if matched:
        save_snapshot(img, name)
        save_log("logout", name, True, f"dist={dist:.3f}")
        return {"match_status": True, "user": name, "distance": dist, "message": f"Goodbye {name}!"}
    else:
        save_log("logout_fail", "unknown_person", False, f"best={name}, dist={dist:.3f}")
        return {"match_status": False, "user": "unknown_person", "distance": dist, "message": "Unknown user."}

@app.get("/get_attendance_logs")
def get_attendance_logs():
    """
    Return a ZIP containing:
      - logs/attendance.csv
      - snapshots/<user>/*.jpg
    """
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # add logs
        if os.path.exists(LOG_FILE):
            zf.write(LOG_FILE, arcname="logs/attendance.csv")
        # add snapshots
        if os.path.exists(SNAP_DIR):
            for root, _, files in os.walk(SNAP_DIR):
                for f in files:
                    if f.lower().endswith((".jpg", ".jpeg", ".png")):
                        full = os.path.join(root, f)
                        arc = os.path.relpath(full, BASE_DIR)
                        zf.write(full, arcname=arc)
    mem.seek(0)
    headers = {"Content-Disposition": "attachment; filename=logs.zip"}
    return StreamingResponse(mem, media_type="application/zip", headers=headers)

# ----------------- Optional utilities -----------------
@app.delete("/admin/clear_all")
def admin_clear_all():
    """Danger: wipe database & snapshots & logs (for testing)."""
    for d in (DB_DIR, SNAP_DIR, LOGS_DIR):
        if os.path.exists(d):
            shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("timestamp,event,user,match,extra\n")
    return {"ok": True, "message": "All cleared."}
