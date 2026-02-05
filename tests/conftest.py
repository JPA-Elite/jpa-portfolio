import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# `backend.utils` imports cv2 at module import time, but CI/container may not have libGL.
if "cv2" not in sys.modules:
    fake_cv2 = types.ModuleType("cv2")
    fake_cv2.VideoCapture = lambda *_args, **_kwargs: None
    fake_cv2.imwrite = lambda *_args, **_kwargs: True
    sys.modules["cv2"] = fake_cv2


os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB", "test")
