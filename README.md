# ♻️ Recycle Detection System

> **AI-powered waste classification using YOLOv8 + OpenCV + Tkinter**

---

## 📁 Project Structure

```
recycle_detection/
│
├── main.py          ← Entry point — run this file
├── detector.py      ← YOLOv8 model + classification logic
├── ui.py            ← Tkinter GUI (window, buttons, history log)
├── requirements.txt ← Python dependencies
├── snapshots/       ← Created automatically when you take snapshots
└── README.md        ← This file
```

---

## ⚡ Quick Start

### 1 — Install Python dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install opencv-python ultralytics numpy
# Optional sound effects:
pip install pygame
```

> **Note:** `yolov8n.pt` (the AI model) is downloaded automatically  
> on first run from the Ultralytics CDN (~6 MB).

### 2 — Run the app

```bash
python main.py
```

---

## 🖥️ How to Use

| Step | Action |
|------|--------|
| 1 | Launch the app with `python main.py` |
| 2 | Click **▶ SCAN ITEM** to open the webcam |
| 3 | Hold an object in front of the camera |
| 4 | Watch the result appear in the GUI *and* on the webcam feed |
| 5 | Click **📷 SNAPSHOT** to save the current frame |
| 6 | Press **Q** in the webcam window *or* **■ STOP** to close |

---

## 🔍 Classification Categories

### ♻️ Recyclable
`bottle` · `cup` · `cardboard` · `paper` · `book` · `bowl`  
`can` · `jar` · `box` · `wine glass` · `fork` · `knife` · `spoon`  
`vase` · `scissors` · `notebook` · `binder` · `envelope` …

### ❌ Non-Recyclable
`banana` · `apple` · `orange` · `pizza` · `hot dog` · `sandwich`  
`donut` · `cake` · `chips` · `tissue` · `rubber` · `cell phone`  
`remote` · `keyboard` · `mouse` …

### ⚠️ Unknown
Anything not in either list above.

---

## 🎛️ Features

| Feature | Details |
|---------|---------|
| Live webcam feed | OpenCV window with bounding boxes |
| Colour-coded boxes | Green = Recyclable, Red = Non-Recyclable, Orange = Unknown |
| Confidence % | Displayed on each bounding box |
| GUI result display | Large colour-coded label in Tkinter window |
| Counter badges | Running totals for recyclable / non-recyclable scans |
| Scan history log | Scrollable timestamped log inside the app |
| Snapshot capture | Saves annotated JPEG to `snapshots/` folder |
| Sound effect | Beep on recyclable detection (requires `pygame` + `numpy`) |
| Hotkey Q | Quit webcam without touching the mouse |

---

## 🔧 Configuration

Open `detector.py` to customise:

```python
# Add items to expand the vocabulary
RECYCLABLE_ITEMS = { "bottle", "cup", ... }
NON_RECYCLABLE_ITEMS = { "banana", "food", ... }

# In RecycleDetector.scan():
confidence_threshold = 0.45   # lower = more detections, higher = more accurate
detection_interval   = 0.5    # seconds between GUI updates
```

---

## 🚀 Future Improvements

### 1 — Train a Custom Recycling Dataset

YOLOv8 is pretrained on COCO (80 general categories). For much
better accuracy on real recyclables, train your own model:

```bash
# Step 1: Collect images of your specific waste items
#         (bottles, cans, wrappers, food scraps, etc.)

# Step 2: Annotate with a free tool
#   → https://roboflow.com  (recommended — exports in YOLO format)
#   → https://labelimg.readthedocs.io

# Step 3: Create dataset.yaml
#   nc: 5
#   names: ['bottle', 'can', 'cardboard', 'food_waste', 'plastic_bag']

# Step 4: Fine-tune YOLOv8 on your data
pip install ultralytics
python -c "
from ultralytics import YOLO
model = YOLO('yolov8n.pt')               # start from pretrained
model.train(data='dataset.yaml', epochs=50, imgsz=640)
"

# Step 5: Use your trained weights in detector.py
# detector = RecycleDetector('runs/detect/train/weights/best.pt')
```

Public recycling datasets to get you started:
- [TACO (Trash Annotations in Context)](http://tacodataset.org)
- [Waste Classification Dataset on Kaggle](https://www.kaggle.com/datasets/techsash/waste-classification-data)
- [Roboflow Universe — Recycling](https://universe.roboflow.com/browse/recycling)

---

### 2 — Improve Detection Accuracy

| Technique | How |
|-----------|-----|
| Larger model | Switch `yolov8n.pt` → `yolov8s.pt` / `yolov8m.pt` (slower but smarter) |
| Higher resolution | Pass `imgsz=1280` to `model()` |
| Better lighting | Ensure the scanning area is well-lit |
| Object distance | Keep items 30–60 cm from the camera |
| Data augmentation | Use Albumentations or Roboflow auto-augmentation when training |
| Ensemble | Run two YOLOv8 sizes and average their confidence scores |
| Custom categories | Train on real trash data (see section above) |

---

### 3 — Convert to a Mobile App

#### Option A — Kivy (Python → Android / iOS)
```bash
pip install kivy buildozer
# Replace Tkinter UI with Kivy layout
# Use buildozer to compile to APK
```

#### Option B — React Native + FastAPI backend
```
Mobile App (React Native)
       │  HTTP / WebSocket
       ▼
FastAPI Server (Python)
  ├── loads YOLOv8 model
  ├── POST /detect  ← receives JPEG from phone camera
  └── returns JSON { label, category, confidence }
```

```bash
pip install fastapi uvicorn python-multipart pillow ultralytics
# Run: uvicorn server:app --host 0.0.0.0 --port 8000
```

#### Option C — TensorFlow Lite (on-device, no server)
```bash
# Export YOLOv8 to TFLite
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
model.export(format="tflite")
# Use the .tflite file with TensorFlow Lite runtime on Android/iOS
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `No webcam found` | Check that no other app has the camera open; try `VideoCapture(1)` |
| Model download fails | Run with internet; or manually download `yolov8n.pt` from [Ultralytics releases](https://github.com/ultralytics/assets/releases) |
| App crashes on macOS | Add `cv2.waitKey(1)` timing; Tkinter + OpenCV can conflict — run detector in a separate process |
| Slow detection | Use `yolov8n.pt` (nano model) and lower `imgsz` to 320 |
| No sound | `pip install pygame numpy` and restart |

---

## 📜 Licence

MIT — free for personal, educational, and commercial use.

---

*Built with ❤️ using [Ultralytics YOLOv8](https://ultralytics.com), [OpenCV](https://opencv.org), and Python Tkinter.*
