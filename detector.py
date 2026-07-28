"""
detector.py — AI Detection Engine
══════════════════════════════════
Loads YOLOv8, opens the webcam, runs inference on each frame,
and classifies detected objects as Recyclable or Non-Recyclable.
"""

import cv2
import time
from ultralytics import YOLO
import datetime


# ─────────────────────────────────────────
#  CATEGORY DEFINITIONS
#  Add / remove items here to expand the
#  classification vocabulary.
# ─────────────────────────────────────────

RECYCLABLE_ITEMS = {
    "bottle", "wine glass", "cup", "fork", "knife", "spoon",
    "bowl", "book", "vase", "scissors", "cardboard", "paper",
    "newspaper", "magazine", "can", "tin", "jar", "box",
    "carton", "envelope", "folder", "notebook", "binder",
}

NON_RECYCLABLE_ITEMS = {
    "banana", "apple", "orange", "broccoli", "carrot",
    "hot dog", "pizza", "donut", "cake", "sandwich",
    "food", "chips", "wrapper", "diaper", "styrofoam",
    "cigarette", "tissue", "straw", "rubber", "leather",
    "mouse",   # computer mouse — mixed materials
    "remote",  # electronics
    "cell phone",
    "keyboard",
}

# Colour coding for webcam overlay text
COLOR_RECYCLABLE     = (0, 220, 80)    # green
COLOR_NON_RECYCLABLE = (0, 60, 220)    # red  (BGR)
COLOR_UNKNOWN        = (0, 165, 255)   # orange


class RecycleDetector:
    """Wraps YOLOv8 inference and recycle-classification logic."""

    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Load the YOLOv8 model.

        Args:
            model_path: Path to the .pt weights file.
                        'yolov8n.pt' is downloaded automatically
                        the first time if not present locally.
        """
        print("[RecycleDetector] Loading YOLOv8 model …")
        self.model = YOLO(model_path)
        print("[RecycleDetector] Model ready ✓")

        # Scan history: list of dicts {time, label, category, confidence}
        self.history: list[dict] = []

        # Running counters
        self.recyclable_count = 0
        self.non_recyclable_count = 0

    # ──────────────────────────────────────
    #  CLASSIFICATION
    # ──────────────────────────────────────
    def classify(self, label: str) -> str:
        """
        Return 'recyclable', 'non_recyclable', or 'unknown'
        based on the detected object label.
        """
        label_lower = label.lower()

        # Check recyclable first
        for item in RECYCLABLE_ITEMS:
            if item in label_lower or label_lower in item:
                return "recyclable"

        # Then non-recyclable
        for item in NON_RECYCLABLE_ITEMS:
            if item in label_lower or label_lower in item:
                return "non_recyclable"

        return "unknown"

    # ──────────────────────────────────────
    #  WEBCAM SCANNING SESSION
    # ──────────────────────────────────────
    def scan(
        self,
        on_result,          # callback(label, category, confidence)
        on_snapshot=None,   # callback(frame) — optional snapshot hook
        stop_event=None,    # threading.Event to stop externally
        confidence_threshold: float = 0.45,
    ):
        """
        Open the webcam, run YOLOv8 on every frame, and call
        `on_result` whenever a detection crosses the confidence
        threshold.

        Press  Q  in the webcam window to quit.

        Args:
            on_result:             Callback fired with (label, category, confidence).
            on_snapshot:           Optional callback fired with the raw BGR frame.
            stop_event:            threading.Event; set it to stop the loop externally.
            confidence_threshold:  Minimum YOLO confidence (0–1) to report.
        """
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("[RecycleDetector] ERROR: Cannot open webcam.")
            on_result("No webcam found", "unknown", 0.0)
            return

        print("[RecycleDetector] Webcam opened. Press Q to quit.")

        # Store the latest snapshot frame for the GUI button
        self._latest_frame = None

        # Expose snapshot hook so the UI can trigger a save
        if on_snapshot is not None:
            self._snapshot_callback = on_snapshot

        last_detection_time = 0
        detection_interval = 0.5   # seconds between result callbacks (avoid spam)

        while True:
            # ── Read frame ──────────────────────────────────────────
            ret, frame = cap.read()
            if not ret:
                print("[RecycleDetector] Frame read failed — retrying …")
                continue

            self._latest_frame = frame.copy()

            # ── Run YOLOv8 inference ─────────────────────────────────
            results = self.model(frame, verbose=False)

            best_label      = None
            best_conf       = 0.0
            best_category   = "unknown"

            for result in results:
                for box in result.boxes:
                    conf  = float(box.conf[0])
                    if conf < confidence_threshold:
                        continue

                    cls_id = int(box.cls[0])
                    label  = self.model.names[cls_id]
                    category = self.classify(label)

                    # ── Draw bounding box on frame ───────────────────
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    if category == "recyclable":
                        box_color = COLOR_RECYCLABLE
                        tag = "♻ RECYCLABLE"
                    elif category == "non_recyclable":
                        box_color = COLOR_NON_RECYCLABLE
                        tag = "✖ NON-RECYCLABLE"
                    else:
                        box_color = COLOR_UNKNOWN
                        tag = "? UNKNOWN"

                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

                    # Label background
                    text = f"{label}  {conf:.0%}  {tag}"
                    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                    cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), box_color, -1)
                    cv2.putText(
                        frame, text,
                        (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (255, 255, 255), 2,
                    )

                    # Track the most-confident detection this frame
                    if conf > best_conf:
                        best_conf     = conf
                        best_label    = label
                        best_category = category

            # ── HUD overlay (top-left) ───────────────────────────────
            self._draw_hud(frame)

            # ── Show the annotated frame ─────────────────────────────
            cv2.imshow("Recycle Detection — Press Q to quit", frame)

            # ── Fire result callback (rate-limited) ─────────────────
            now = time.time()
            if best_label and (now - last_detection_time) > detection_interval:
                last_detection_time = now
                self._record(best_label, best_category, best_conf)
                on_result(best_label, best_category, best_conf)

            # ── Exit conditions ──────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q"):
                break
            if stop_event and stop_event.is_set():
                break

        cap.release()
        cv2.destroyAllWindows()
        print("[RecycleDetector] Webcam closed.")

    # ──────────────────────────────────────
    #  SNAPSHOT
    # ──────────────────────────────────────
    def take_snapshot(self, save_dir: str = "snapshots") -> str | None:
        """
        Save the most-recent webcam frame as a JPEG.

        Returns:
            Path of saved file, or None if no frame is available.
        """
        if self._latest_frame is None:
            return None

        os.makedirs(save_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(save_dir, f"snapshot_{timestamp}.jpg")
        cv2.imwrite(path, self._latest_frame)
        print(f"[RecycleDetector] Snapshot saved → {path}")
        return path

    # ──────────────────────────────────────
    #  INTERNAL HELPERS
    # ──────────────────────────────────────
    def _record(self, label: str, category: str, conf: float):
        """Append a detection to history and update counters."""
        self.history.append({
            "time":       datetime.datetime.now().strftime("%H:%M:%S"),
            "label":      label,
            "category":   category,
            "confidence": conf,
        })
        if category == "recyclable":
            self.recyclable_count += 1
        elif category == "non_recyclable":
            self.non_recyclable_count += 1

    def _draw_hud(self, frame):
        """Draw a small HUD on the top-left of the frame."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (280, 70), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        cv2.putText(frame,
                    f"Recyclable  : {self.recyclable_count}",
                    (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    COLOR_RECYCLABLE, 2)
        cv2.putText(frame,
                    f"Non-Recycl. : {self.non_recyclable_count}",
                    (8, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    COLOR_NON_RECYCLABLE, 2)


import os   # (needed for take_snapshot — hoisted here for clarity)
