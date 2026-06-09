import base64
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
from bson import ObjectId
from flask import jsonify, request, session

from backend.Repositories.AuthRepository import AuthRepository
from backend.auth.middleware import admin_login_required

_FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
_auth_repo_for_faces = AuthRepository()

def _require_image_b64(payload: dict) -> str:
    if not payload:
        raise ValueError("Missing JSON body")
    b64 = payload.get("image_b64")
    if not b64 or not isinstance(b64, str):
        raise ValueError("Missing image_b64")
    return b64

def _decode_b64_image(image_b64: str) -> np.ndarray:

    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    raw = base64.b64decode(image_b64)
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return img

def _detect_and_crop_face(img_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if faces is None or len(faces) == 0:
        raise ValueError("No face detected")

    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])

    x0 = max(0, int(x - 0.15 * w))
    y0 = max(0, int(y - 0.15 * h))
    x1 = min(gray.shape[1], int(x + w + 0.15 * w))
    y1 = min(gray.shape[0], int(y + h + 0.15 * h))

    face = gray[y0:y1, x0:x1]
    if face.size == 0:
        raise ValueError("Invalid face crop")

    face_resized = cv2.resize(face, (160, 160))
    return face_resized

def _normalize_face(face_gray_160: np.ndarray) -> np.ndarray:

    blur = cv2.GaussianBlur(face_gray_160, (5, 5), 0)
    normalized = cv2.resize(blur, (160, 160))
    return normalized.astype(np.uint8)

def _encode_crop_to_b64(face_gray_160: np.ndarray) -> str:

    ok, png = cv2.imencode(".png", face_gray_160)
    if not ok:
        raise ValueError("Could not encode face crop")
    return base64.b64encode(png.tobytes()).decode("utf-8")

def _face_l1_distance(a_gray_160: np.ndarray, b_gray_160: np.ndarray) -> float:

    a = a_gray_160.astype(np.float32)
    b = b_gray_160.astype(np.float32)
    return float(np.mean(np.abs(a - b)))

def _b64_png_to_gray_160(face_crop_b64: str) -> np.ndarray:
    if not face_crop_b64 or not isinstance(face_crop_b64, str):
        raise ValueError("Missing stored face reference")
    raw = base64.b64decode(face_crop_b64)
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode stored face reference")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if gray.shape != (160, 160):
        gray = cv2.resize(gray, (160, 160))
    return gray.astype(np.uint8)

def admin_face_register_route():

    try:
        payload = request.get_json(silent=True) or {}

        image_b64_list = payload.get("image_b64_list")
        if isinstance(image_b64_list, list) and len(image_b64_list) > 0:
            b64_list = [x for x in image_b64_list if isinstance(x, str)]
        else:
            b64_list = [_require_image_b64(payload)]

        if not b64_list:
            return jsonify({"ok": False, "message": "Missing image captures"}), 400

        crops = []
        for image_b64 in b64_list:
            img = _decode_b64_image(image_b64)
            face_crop = _detect_and_crop_face(img)
            face_crop_norm = _normalize_face(face_crop)
            crops.append(face_crop_norm)

        if not crops:
            return jsonify({"ok": False, "message": "No valid face crops captured"}), 400

        reference_gray_160 = np.median(np.stack(crops, axis=0), axis=0).astype(np.uint8)
        face_crop_b64 = _encode_crop_to_b64(reference_gray_160)

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        _auth_repo_for_faces.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "face_reference_crop_b64": face_crop_b64,

                    "face_reference_hash": "",
                    "face_last_registered_at": datetime.utcnow().isoformat() + "Z",
                }
            },
            upsert=False,
        )

        return jsonify({"ok": True, "message": "Face reference registered"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

def admin_face_records_route():

    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        user_doc = _auth_repo_for_faces.collection.find_one({"_id": ObjectId(user_id)}) or {}

        registered_at = user_doc.get("face_last_registered_at")
        verified_at = user_doc.get("face_last_verified_at")
        distance = user_doc.get("face_last_verify_distance")

        rows = []
        if registered_at:
            rows.append(
                {
                    "status": "Registered",
                    "distance": None,
                    "timestamp": registered_at,
                }
            )
        if verified_at:
            rows.append(
                {
                    "status": "Verified",
                    "distance": distance,
                    "timestamp": verified_at,
                }
            )

        return jsonify({"ok": True, "rows": rows})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

def admin_face_verify_route():

    try:
        payload = request.get_json(silent=True) or {}

        image_b64_list = payload.get("image_b64_list")
        if isinstance(image_b64_list, list) and len(image_b64_list) > 0:
            b64_list = [x for x in image_b64_list if isinstance(x, str)]
        else:
            b64_list = [_require_image_b64(payload)]

        if not b64_list:
            return jsonify({"ok": False, "message": "Missing image captures"}), 400

        crops = []
        for image_b64 in b64_list:
            img = _decode_b64_image(image_b64)
            face_crop = _detect_and_crop_face(img)
            face_crop_norm = _normalize_face(face_crop)
            crops.append(face_crop_norm)

        if not crops:
            return jsonify({"ok": False, "message": "No valid face crops captured"}), 400

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "message": "Not authenticated"}), 401

        user_doc = _auth_repo_for_faces.collection.find_one({"_id": ObjectId(user_id)})
        ref_crop_b64 = (user_doc or {}).get("face_reference_crop_b64")
        if not ref_crop_b64:
            return jsonify({"ok": False, "message": "No registered face found. Please register first."}), 400

        ref_gray_160 = _b64_png_to_gray_160(ref_crop_b64)

        distances = [_face_l1_distance(crop, ref_gray_160) for crop in crops]
        dist = float(min(distances))

        THRESHOLD_L1 = 22.0
        if dist > THRESHOLD_L1:
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "Face does not match. Please try again.",
                        "distance": dist,
                    }
                ),
                403,
            )

        _auth_repo_for_faces.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "face_last_verified_at": datetime.utcnow().isoformat() + "Z",
                    "face_last_verify_distance": dist,
                }
            },
            upsert=False,
        )

        session["face_verified"] = True
        return jsonify({"ok": True, "message": "Face verified", "distance": dist})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

