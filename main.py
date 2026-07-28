"""
╔══════════════════════════════════════════════════════╗
║         RECYCLE DETECTION SYSTEM - main.py           ║
║  AI-powered object detection using YOLOv8 + OpenCV   ║
╚══════════════════════════════════════════════════════╝

How it works:
  1. Tkinter creates the main GUI window
  2. "Scan Item" button opens webcam via OpenCV
  3. YOLOv8 detects objects in each frame
  4. Detected objects are classified as Recyclable / Non-Recyclable
  5. Result is shown in the GUI and live on the webcam window
"""

import tkinter as tk
from tkinter import font as tkFont
import threading
import datetime
import os

# Import our helper modules
from detector import RecycleDetector
from ui import RecycleUI


# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────
def main():
    """Launch the Recycle Detection application."""
    root = tk.Tk()

    # Create the detector (loads YOLOv8 model)
    detector = RecycleDetector()

    # Create the UI, passing the detector so buttons can trigger scanning
    app = RecycleUI(root, detector)

    # Start the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main()
