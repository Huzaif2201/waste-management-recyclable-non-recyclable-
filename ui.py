"""
ui.py — Tkinter GUI
════════════════════
Builds the main application window:
  • Heading
  • Live result label (colour-coded)
  • Recyclable counter badge
  • Scan / Stop / Snapshot buttons
  • Scrollable history log
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os

# Try to import pygame for sound (optional — app works without it)
try:
    import pygame
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False


# ─────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────
BG          = "#0f172a"   # deep navy
CARD        = "#1e293b"   # slightly lighter card
ACCENT      = "#22d3ee"   # cyan accent
GREEN       = "#4ade80"
RED         = "#f87171"
ORANGE      = "#fb923c"
TEXT_LIGHT  = "#f1f5f9"
TEXT_DIM    = "#94a3b8"
BUTTON_SCAN = "#06b6d4"
BUTTON_STOP = "#ef4444"
BUTTON_SNAP = "#8b5cf6"


class RecycleUI:
    """Main application GUI controller."""

    def __init__(self, root: tk.Tk, detector):
        self.root     = root
        self.detector = detector

        # Thread management
        self._scan_thread  = None
        self._stop_event   = threading.Event()
        self._scanning     = False

        # Latest snapshot path (shown in log)
        self._last_snapshot = None

        self._build_window()
        self._build_widgets()

    # ──────────────────────────────────────
    #  WINDOW SETUP
    # ──────────────────────────────────────
    def _build_window(self):
        self.root.title("Recycle Detection")
        self.root.geometry("520x700")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # Try to set a window icon (silently skip if file missing)
        try:
            self.root.iconbitmap("icon.ico")
        except Exception:
            pass

    # ──────────────────────────────────────
    #  WIDGET CONSTRUCTION
    # ──────────────────────────────────────
    def _build_widgets(self):
        root = self.root

        # ── Top banner ──────────────────────────────────────────────
        banner = tk.Frame(root, bg=CARD, height=90)
        banner.pack(fill="x")

        tk.Label(
            banner,
            text="♻  RECYCLE DETECTION",
            font=("Courier New", 20, "bold"),
            bg=CARD, fg=ACCENT,
        ).pack(pady=10)

        tk.Label(
            banner,
            text="AI-powered waste classification · YOLOv8",
            font=("Courier New", 9),
            bg=CARD, fg=TEXT_DIM,
        ).pack()

        # ── Divider ─────────────────────────────────────────────────
        tk.Frame(root, bg=ACCENT, height=2).pack(fill="x")

        # ── Result card ─────────────────────────────────────────────
        result_card = tk.Frame(root, bg=CARD, bd=0)
        result_card.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(
            result_card,
            text="DETECTION RESULT",
            font=("Courier New", 8, "bold"),
            bg=CARD, fg=TEXT_DIM,
        ).pack(anchor="w", padx=14, pady=(10, 0))

        self.result_label = tk.Label(
            result_card,
            text="Press  SCAN  to begin",
            font=("Courier New", 16, "bold"),
            bg=CARD, fg=TEXT_DIM,
            wraplength=440,
            justify="center",
            height=3,
        )
        self.result_label.pack(padx=14, pady=(4, 10))

        # ── Counter badges ───────────────────────────────────────────
        badge_row = tk.Frame(root, bg=BG)
        badge_row.pack(fill="x", padx=20, pady=(12, 0))

        self._build_badge(badge_row, "♻  Recyclable",  GREEN,  "recyclable_var").pack(
            side="left", expand=True, padx=(0, 6))
        self._build_badge(badge_row, "✖  Non-Recyclable", RED, "non_recyclable_var").pack(
            side="left", expand=True, padx=(6, 0))

        # ── Buttons ─────────────────────────────────────────────────
        btn_row = tk.Frame(root, bg=BG)
        btn_row.pack(pady=18)

        self.scan_btn = self._make_button(
            btn_row, "▶  SCAN ITEM", BUTTON_SCAN, self._start_scan)
        self.scan_btn.pack(side="left", padx=6)

        self.stop_btn = self._make_button(
            btn_row, "■  STOP", BUTTON_STOP, self._stop_scan, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

        self.snap_btn = self._make_button(
            btn_row, "📷  SNAPSHOT", BUTTON_SNAP, self._take_snapshot, state="disabled")
        self.snap_btn.pack(side="left", padx=6)

        # ── Status bar ───────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            root,
            textvariable=self.status_var,
            font=("Courier New", 8),
            bg=BG, fg=TEXT_DIM,
        ).pack()

        # ── History log ─────────────────────────────────────────────
        log_frame = tk.Frame(root, bg=CARD, bd=0)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 16))

        tk.Label(
            log_frame,
            text="SCAN HISTORY",
            font=("Courier New", 8, "bold"),
            bg=CARD, fg=TEXT_DIM,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        # Scrollable text widget
        self.log_text = tk.Text(
            log_frame,
            height=10,
            bg="#0d1b2a",
            fg=TEXT_LIGHT,
            font=("Courier New", 9),
            relief="flat",
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Colour tags for the log
        self.log_text.tag_config("recyclable",     foreground=GREEN)
        self.log_text.tag_config("non_recyclable", foreground=RED)
        self.log_text.tag_config("unknown",        foreground=ORANGE)
        self.log_text.tag_config("dim",            foreground=TEXT_DIM)
        self.log_text.tag_config("snapshot",       foreground=BUTTON_SNAP)

    # ──────────────────────────────────────
    #  WIDGET HELPERS
    # ──────────────────────────────────────
    def _build_badge(self, parent, label_text: str, colour: str, var_attr: str):
        """Create a small counter badge frame."""
        var = tk.IntVar(value=0)
        setattr(self, var_attr, var)

        frame = tk.Frame(parent, bg=CARD, bd=0)
        tk.Label(frame, text=label_text,
                 font=("Courier New", 8), bg=CARD, fg=colour).pack(anchor="w", padx=10, pady=(6,0))
        tk.Label(frame, textvariable=var,
                 font=("Courier New", 28, "bold"), bg=CARD, fg=colour).pack(padx=10, pady=(0,6))
        return frame

    def _make_button(self, parent, text: str, colour: str, command, state="normal"):
        """Create a styled flat button."""
        return tk.Button(
            parent,
            text=text,
            command=command,
            state=state,
            font=("Courier New", 10, "bold"),
            bg=colour, fg="white",
            activebackground=colour,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=14, pady=8,
        )

    # ──────────────────────────────────────
    #  SCANNING LOGIC
    # ──────────────────────────────────────
    def _start_scan(self):
        """Start a background thread that runs the webcam detector."""
        if self._scanning:
            return

        self._scanning = True
        self._stop_event.clear()

        # Update button states
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.snap_btn.config(state="normal")
        self.status_var.set("Scanning … (press Q in webcam window or STOP here)")
        self.result_label.config(text="Waiting for object …", fg=TEXT_DIM)

        # Run detector in a daemon thread so it doesn't block the GUI
        self._scan_thread = threading.Thread(
            target=self._run_detector, daemon=True)
        self._scan_thread.start()

    def _stop_scan(self):
        """Signal the detector thread to stop."""
        self._stop_event.set()
        self._scanning = False
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.snap_btn.config(state="disabled")
        self.status_var.set("Stopped. Press SCAN to start again.")

    def _run_detector(self):
        """Called in background thread — runs the detector."""
        self.detector.scan(
            on_result=self._on_result,
            stop_event=self._stop_event,
        )
        # When scan() returns (user pressed Q), update UI from main thread
        self.root.after(0, self._stop_scan)

    # ──────────────────────────────────────
    #  RESULT CALLBACK  (called from bg thread)
    # ──────────────────────────────────────
    def _on_result(self, label: str, category: str, confidence: float):
        """Update the GUI with a new detection result (thread-safe via after())."""
        self.root.after(0, self._update_ui, label, category, confidence)

    def _update_ui(self, label: str, category: str, confidence: float):
        """Must be called from the main Tkinter thread."""

        conf_pct = f"{confidence:.0%}"

        if category == "recyclable":
            emoji   = "♻️"
            colour  = GREEN
            heading = "RECYCLABLE"
            self.recyclable_var.set(self.detector.recyclable_count)
            self._play_sound("recycle")

        elif category == "non_recyclable":
            emoji   = "❌"
            colour  = RED
            heading = "NON-RECYCLABLE"
            self.non_recyclable_var.set(self.detector.non_recyclable_count)

        else:
            emoji   = "⚠️"
            colour  = ORANGE
            heading = "UNKNOWN ITEM"

        display_text = f"{emoji}  {label.upper()}\n{heading} · {conf_pct}"
        self.result_label.config(text=display_text, fg=colour)

        # Append to history log
        self._log_entry(label, category, conf_pct)

    # ──────────────────────────────────────
    #  HISTORY LOG
    # ──────────────────────────────────────
    def _log_entry(self, label: str, category: str, conf_pct: str):
        """Append one line to the scrollable history log."""
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")

        if category == "recyclable":
            symbol = "♻"
            tag = "recyclable"
        elif category == "non_recyclable":
            symbol = "✖"
            tag = "non_recyclable"
        else:
            symbol = "⚠"
            tag = "unknown"

        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}]  ", "dim")
        self.log_text.insert("end", f"{symbol} {label:<18} {conf_pct:>5}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ──────────────────────────────────────
    #  SNAPSHOT
    # ──────────────────────────────────────
    def _take_snapshot(self):
        """Save the current webcam frame to disk."""
        path = self.detector.take_snapshot()
        if path:
            self._last_snapshot = path
            self.log_text.config(state="normal")
            self.log_text.insert("end", f"📷  Snapshot saved → {path}\n", "snapshot")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
            self.status_var.set(f"Snapshot saved: {path}")
        else:
            self.status_var.set("No frame available for snapshot yet.")

    # ──────────────────────────────────────
    #  SOUND (optional)
    # ──────────────────────────────────────
    def _play_sound(self, sound_type: str):
        """Play a short beep if pygame is available."""
        if not SOUND_AVAILABLE:
            return
        try:
            # Generate a simple sine-wave beep programmatically
            # (no external audio file needed)
            import numpy as np
            sample_rate = 22050
            freq = 880 if sound_type == "recycle" else 440
            duration = 0.18   # seconds
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave = (np.sin(2 * np.pi * freq * t) * 20000).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
        except Exception:
            pass   # Sound is a bonus feature; never crash because of it
