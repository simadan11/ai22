"""
Local, real-time person tracking for the EDITH HUD.

The Gemini vision pass is accurate but slow (~1-2 s round trip), so on a live
camera feed the silhouette/skeleton always lags behind the person. This module
runs entirely on the local machine and produces per-frame detections at video
rate, so the aura and bones stick to the body while it moves.

Detection chain (first one that works wins):
  1. MediaPipe PoseLandmarker — real skeleton (33 landmarks) + segmentation
     mask, which we trace into a true silhouette polygon.
  2. OpenCV HOG people detector — bounding boxes only; the HUD then draws its
     procedural rig inside the box.
  3. Nothing (module reports unavailable and the HUD falls back to Gemini).

Everything is lazily initialised and fully exception-guarded: if a dependency
or the model file is missing, `track()` simply returns [] and the rest of the
app keeps working exactly as before.
"""

from __future__ import annotations

import math
import os
import threading
import time
import urllib.request
from pathlib import Path

# Landmark indices of the MediaPipe Pose (BlazePose GHUM) topology
_MP_IDX = {
    "nose": 0,
    "l_eye": 2, "r_eye": 5,
    "l_ear": 7, "r_ear": 8,
    "l_shoulder": 11, "r_shoulder": 12,
    "l_elbow": 13, "r_elbow": 14,
    "l_wrist": 15, "r_wrist": 16,
    "l_hip": 23, "r_hip": 24,
    "l_knee": 25, "r_knee": 26,
    "l_ankle": 27, "r_ankle": 28,
}

# Joint names the HUD understands (must match ui._BONES)
_HUD_JOINTS = (
    "head", "neck", "l_shoulder", "r_shoulder", "l_elbow", "r_elbow",
    "l_wrist", "r_wrist", "pelvis", "l_hip", "r_hip",
    "l_knee", "r_knee", "l_ankle", "r_ankle",
)

_MODEL_URLS = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
)


def _model_path() -> Path:
    base = Path(__file__).resolve().parent.parent / "config"
    base.mkdir(parents=True, exist_ok=True)
    return base / "pose_landmarker_lite.task"


def _ensure_model() -> Path | None:
    """Return the local model file, downloading it once if needed."""
    p = _model_path()
    if p.exists() and p.stat().st_size > 1000:
        return p
    for url in _MODEL_URLS:
        tmp = p.with_suffix(".part")
        try:
            print("[PoseTracker] Downloading pose model (one time, ~6 MB)…")
            # NB: a bare urlretrieve() has no timeout and can hang the app
            # forever on a dead network — always bound it.
            with urllib.request.urlopen(url, timeout=20) as r:   # noqa: S310
                data = r.read()
            if len(data) > 1000:
                tmp.write_bytes(data)
                tmp.replace(p)
                print(f"[PoseTracker] Model ready → {p.name}")
                return p
        except Exception as e:
            print(f"[PoseTracker] Model download failed: {e}")
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
    return None


class PoseTracker:
    """Thread-safe, lazily-initialised local person tracker."""

    def __init__(self, max_people: int = 4):
        self._max_people = max_people
        self._lock = threading.Lock()
        self._mp = None            # MediaPipe PoseLandmarker instance
        self._hog = None           # OpenCV HOG fallback
        self._mode = "init"        # init | mediapipe | hog | off
        self._np = None
        self._cv2 = None
        self._last_err = ""
        self._smooth: dict = {}    # exponential smoothing state
        self._last_ts = 0          # strictly-increasing MediaPipe timestamp
        self._fails = 0            # consecutive backend failures

    # ── availability ────────────────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self._mode

    def available(self) -> bool:
        self._ensure()
        return self._mode in ("mediapipe", "hog")

    def _ensure(self) -> None:
        if self._mode != "init":
            return
        with self._lock:
            if self._mode != "init":
                return
            try:
                self._init_backend()
            except BaseException as e:       # absolutely never propagate
                self._mode = "off"
                print(f"[PoseTracker] Init crashed, disabled — {e}")

    def _init_backend(self) -> None:
        if True:  # keeps the original indentation of the init block
            # numpy + cv2 are needed by both backends
            try:
                import numpy as np
                import cv2
                self._np, self._cv2 = np, cv2
            except Exception as e:
                self._mode, self._last_err = "off", f"numpy/cv2 missing: {e}"
                return

            # 1) MediaPipe pose + segmentation
            try:
                from mediapipe.tasks import python as mp_python
                from mediapipe.tasks.python import vision as mp_vision

                model = _ensure_model()
                if model is None:
                    raise RuntimeError("pose model unavailable")
                opts = mp_vision.PoseLandmarkerOptions(
                    base_options=mp_python.BaseOptions(
                        model_asset_path=str(model)
                    ),
                    running_mode=mp_vision.RunningMode.VIDEO,
                    num_poses=self._max_people,
                    min_pose_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                    output_segmentation_masks=True,
                )
                self._mp = mp_vision.PoseLandmarker.create_from_options(opts)
                self._mode = "mediapipe"
                print("[PoseTracker] Backend: MediaPipe (skeleton + silhouette)")
                return
            except Exception as e:
                self._last_err = f"mediapipe: {e}"

            # 2) OpenCV HOG people detector
            try:
                hog = self._cv2.HOGDescriptor()
                hog.setSVMDetector(
                    self._cv2.HOGDescriptor_getDefaultPeopleDetector()
                )
                self._hog = hog
                self._mode = "hog"
                print("[PoseTracker] Backend: OpenCV HOG (boxes only)")
                return
            except Exception as e:
                self._last_err += f" | hog: {e}"

            self._mode = "off"
            print(f"[PoseTracker] Disabled — {self._last_err}")
            print("[PoseTracker] Tip: pip install mediapipe opencv-python "
                  "for real-time skeleton tracking.")

    # ── public API ──────────────────────────────────────────────────────
    def track(self, frame_bytes: bytes) -> list[dict]:
        """JPEG bytes → list of HUD detections (same schema as _edith_detect).

        Each person dict has: kind/label/box (+ outline & pose when the
        MediaPipe backend is active). Never raises.
        """
        self._ensure()
        if self._mode not in ("mediapipe", "hog"):
            return []
        try:
            if not frame_bytes:
                return []
            np, cv2 = self._np, self._cv2
            buf = np.frombuffer(frame_bytes, dtype=np.uint8)
            if buf.size == 0:
                return []
            bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if bgr is None or bgr.size == 0:
                return []
            # keep the analysis cheap — downscale wide frames
            h, w = bgr.shape[:2]
            if w > 640:
                sc = 640.0 / w
                bgr = cv2.resize(bgr, (640, max(1, int(h * sc))),
                                 interpolation=cv2.INTER_AREA)
            if self._mode == "mediapipe":
                out = self._track_mediapipe(bgr)
            else:
                out = self._track_hog(bgr)
            self._fails = 0
            return out
        except BaseException as e:      # never let a backend kill the app
            self._fails += 1
            print(f"[PoseTracker] track failed ({self._fails}): {e}")
            if self._fails >= 5:
                self._degrade()
            return []

    def _degrade(self) -> None:
        """A backend misbehaved repeatedly — drop to the next safest one."""
        with self._lock:
            if self._mode == "mediapipe":
                try:
                    if self._mp is not None:
                        self._mp.close()
                except Exception:
                    pass
                self._mp = None
                try:
                    hog = self._cv2.HOGDescriptor()
                    hog.setSVMDetector(
                        self._cv2.HOGDescriptor_getDefaultPeopleDetector()
                    )
                    self._hog = hog
                    self._mode = "hog"
                    print("[PoseTracker] MediaPipe unstable → switched to HOG")
                except Exception:
                    self._mode = "off"
                    print("[PoseTracker] Disabled after repeated failures")
            else:
                self._mode = "off"
                print("[PoseTracker] Disabled after repeated failures")
            self._fails = 0
            self._smooth.clear()

    def reset(self) -> None:
        """Clear smoothing state (call when the stream stops)."""
        self._smooth.clear()

    # ── MediaPipe backend ───────────────────────────────────────────────
    def _track_mediapipe(self, bgr) -> list[dict]:
        import mediapipe as mp
        np, cv2 = self._np, self._cv2

        h, w = bgr.shape[:2]
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        # MediaPipe keeps a reference to the buffer — hand it a private,
        # contiguous copy so nothing mutates underneath the native code.
        rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # CRITICAL: VIDEO mode aborts the *process* if timestamps are not
        # strictly increasing, and the landmarker is not thread-safe. Both are
        # guaranteed here by the lock + monotonic counter.
        with self._lock:
            ts = max(int(time.monotonic() * 1000), self._last_ts + 1)
            self._last_ts = ts
            res = self._mp.detect_for_video(image, ts)

        out: list[dict] = []
        lms = getattr(res, "pose_landmarks", None) or []
        masks = getattr(res, "segmentation_masks", None) or []

        for i, person in enumerate(lms[: self._max_people]):
            pts = {}
            xs, ys = [], []
            for name, idx in _MP_IDX.items():
                if idx >= len(person):
                    continue
                lm = person[idx]
                vis = getattr(lm, "visibility", 1.0)
                if vis is not None and vis < 0.35:
                    continue
                x, y = float(lm.x), float(lm.y)
                if not (math.isfinite(x) and math.isfinite(y)):
                    continue
                pts[name] = (y, x)
                xs.append(x); ys.append(y)
            if len(pts) < 4:
                continue

            pose = self._to_hud_joints(pts)
            box = self._box_from(xs, ys)
            outline = []
            if i < len(masks):
                outline = self._mask_outline(masks[i], w, h)
            if not outline:
                outline = self._pose_outline(pose)

            key = f"p{i}"
            pose, outline, box = self._smooth_person(key, pose, outline, box)

            out.append({
                "kind":    "person",
                "label":   "PERSON — TRACKED",
                "detail":  "live local tracking",
                "box":     box,
                "pose":    pose,
                "outline": outline,
                "source":  "local",
            })
        if not out:
            self._smooth.clear()
        return out

    @staticmethod
    def _to_hud_joints(pts: dict) -> dict:
        """MediaPipe landmark set → the joint names the HUD draws."""

        def mid(a, b):
            pa, pb = pts.get(a), pts.get(b)
            if pa and pb:
                return [(pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2]
            return None

        j: dict = {}
        # head: prefer the eye/ear midpoint, else the nose
        head = mid("l_ear", "r_ear") or mid("l_eye", "r_eye")
        if head is None and "nose" in pts:
            head = [pts["nose"][0], pts["nose"][1]]
        neck = mid("l_shoulder", "r_shoulder")
        pelvis = mid("l_hip", "r_hip")
        if head and neck:
            # nudge the head marker up a little so it sits on the skull
            head = [head[0] - abs(neck[0] - head[0]) * 0.35, head[1]]
        if head:
            j["head"] = head
        if neck:
            j["neck"] = neck
        if pelvis:
            j["pelvis"] = pelvis
        for name in ("l_shoulder", "r_shoulder", "l_elbow", "r_elbow",
                     "l_wrist", "r_wrist", "l_hip", "r_hip",
                     "l_knee", "r_knee", "l_ankle", "r_ankle"):
            if name in pts:
                j[name] = [pts[name][0], pts[name][1]]
        # scale 0-1 → 0-1000 for the HUD
        return {k: [round(v[0] * 1000, 1), round(v[1] * 1000, 1)]
                for k, v in j.items() if k in _HUD_JOINTS}

    @staticmethod
    def _box_from(xs, ys) -> list:
        pad_x = (max(xs) - min(xs)) * 0.12 + 0.02
        pad_y = (max(ys) - min(ys)) * 0.10 + 0.03
        cl = lambda v: max(0.0, min(1000.0, v * 1000))   # noqa: E731
        return [round(cl(min(ys) - pad_y), 1), round(cl(min(xs) - pad_x), 1),
                round(cl(max(ys) + pad_y), 1), round(cl(max(xs) + pad_x), 1)]

    def _mask_outline(self, mask, w: int, h: int) -> list:
        """Segmentation mask → simplified silhouette polygon ([y, x] 0-1000)."""
        try:
            np, cv2 = self._np, self._cv2
            arr = mask.numpy_view() if hasattr(mask, "numpy_view") else np.asarray(mask)
            if arr is None or arr.size == 0:
                return []
            binary = (arr > 0.5).astype(np.uint8) * 255
            if binary.ndim == 3:
                binary = binary[:, :, 0]
            mh, mw = binary.shape[:2]
            binary = cv2.morphologyEx(
                binary, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)
            )
            cnts, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if not cnts:
                return []
            c = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(c) < (mw * mh) * 0.01:
                return []
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.006 * peri, True)
            pts = approx.reshape(-1, 2)
            if len(pts) < 5:
                return []
            # keep the polygon light: at most 36 points
            if len(pts) > 36:
                step = len(pts) / 36.0
                pts = [pts[int(i * step)] for i in range(36)]
            return [[round(float(p[1]) / mh * 1000, 1),
                     round(float(p[0]) / mw * 1000, 1)] for p in pts]
        except Exception:
            return []

    @staticmethod
    def _pose_outline(pose: dict) -> list:
        """Rough body-hull polygon built from joints when no mask is available."""
        need = ("head", "l_shoulder", "r_shoulder", "l_hip", "r_hip")
        if not all(k in pose for k in need):
            return []

        def g(k, dy=0.0, dx=0.0):
            p = pose.get(k)
            return None if p is None else [p[0] + dy, p[1] + dx]

        span = abs(pose["l_shoulder"][1] - pose["r_shoulder"][1]) or 60.0
        pad = span * 0.30
        chain = [
            g("head", -pad * 1.1),
            g("r_shoulder", -pad * 0.3, pad * 0.6),
            g("r_elbow", 0, pad * 0.6) or g("r_shoulder", 0, pad),
            g("r_wrist", 0, pad * 0.5) or g("r_elbow", 0, pad),
            g("r_hip", 0, pad * 0.5),
            g("r_knee", 0, pad * 0.45) or g("r_hip", pad, pad * 0.4),
            g("r_ankle", pad * 0.4, pad * 0.4) or g("r_knee", pad, 0),
            g("l_ankle", pad * 0.4, -pad * 0.4) or g("l_knee", pad, 0),
            g("l_knee", 0, -pad * 0.45) or g("l_hip", pad, -pad * 0.4),
            g("l_hip", 0, -pad * 0.5),
            g("l_wrist", 0, -pad * 0.5) or g("l_elbow", 0, -pad),
            g("l_elbow", 0, -pad * 0.6) or g("l_shoulder", 0, -pad),
            g("l_shoulder", -pad * 0.3, -pad * 0.6),
        ]
        pts = [[max(0.0, min(1000.0, p[0])), max(0.0, min(1000.0, p[1]))]
               for p in chain if p]
        return pts if len(pts) >= 6 else []

    # ── temporal smoothing (kills jitter without adding lag) ────────────
    def _smooth_person(self, key: str, pose: dict, outline: list, box: list):
        a = 0.55                                  # weight of the new frame
        prev = self._smooth.get(key)
        if prev:
            pp, pb = prev.get("pose", {}), prev.get("box")
            pose = {
                k: ([v[0] * a + pp[k][0] * (1 - a), v[1] * a + pp[k][1] * (1 - a)]
                    if k in pp else v)
                for k, v in pose.items()
            }
            if pb and len(pb) == 4:
                box = [v * a + pb[i] * (1 - a) for i, v in enumerate(box)]
            po = prev.get("outline")
            if po and len(po) == len(outline):
                outline = [[p[0] * a + po[i][0] * (1 - a),
                            p[1] * a + po[i][1] * (1 - a)]
                           for i, p in enumerate(outline)]
        self._smooth[key] = {"pose": pose, "outline": outline, "box": box}
        rnd = lambda p: [round(p[0], 1), round(p[1], 1)]        # noqa: E731
        return ({k: rnd(v) for k, v in pose.items()},
                [rnd(p) for p in outline],
                [round(v, 1) for v in box])

    # ── OpenCV HOG fallback ─────────────────────────────────────────────
    def _track_hog(self, bgr) -> list:
        cv2 = self._cv2
        h, w = bgr.shape[:2]
        small = cv2.resize(bgr, (min(w, 480), int(h * min(w, 480) / w)))
        sh, sw = small.shape[:2]
        rects, weights = self._hog.detectMultiScale(
            small, winStride=(8, 8), padding=(8, 8), scale=1.06
        )
        out = []
        for (x, y, bw, bh), score in zip(rects, weights):
            if float(score) < 0.4:
                continue
            out.append({
                "kind":   "person",
                "label":  "PERSON — TRACKED",
                "detail": "live local tracking",
                "box": [round(y / sh * 1000, 1), round(x / sw * 1000, 1),
                        round((y + bh) / sh * 1000, 1),
                        round((x + bw) / sw * 1000, 1)],
                "source": "local",
            })
            if len(out) >= self._max_people:
                break
        return out


# Process-wide singleton — the HUD and the relay share one tracker
_tracker: PoseTracker | None = None
_tracker_lock = threading.Lock()


def get_tracker() -> PoseTracker:
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = PoseTracker()
    return _tracker


def track_people(frame_bytes: bytes) -> list[dict]:
    """Convenience wrapper — local person detections for one JPEG frame."""
    return get_tracker().track(frame_bytes)
