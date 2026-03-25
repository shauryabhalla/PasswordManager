"""
popup.py — Small bottom-right notification popup using tkinter.

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POPUP NOTIFICATION — Comment out the call to show_popup() in
# main.py if you no longer want the notification to appear.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import threading
import tkinter as tk


def show_popup(message: str = "Entering password…", duration_ms: int = 1000) -> None:
    """
    Show a small notification in the bottom-right corner of the screen.
    Auto-dismisses after `duration_ms` milliseconds.
    Runs in its own thread so it doesn't block the main loop.
    """
    def _run():
        root = tk.Tk()
        root.overrideredirect(True)          # No title bar / borders
        root.attributes("-topmost", True)    # Always on top
        root.attributes("-alpha", 0.90)      # Slight transparency

        # Styling
        bg_color = "#1e1e2e"
        fg_color = "#cdd6f4"
        font = ("Segoe UI", 11)

        label = tk.Label(
            root,
            text=f"  🔑  {message}  ",
            bg=bg_color,
            fg=fg_color,
            font=font,
            padx=16,
            pady=10,
        )
        label.pack()

        # Position: bottom-right corner with a small margin
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = screen_w - w - 20
        y = screen_h - h - 60  # above the taskbar
        root.geometry(f"+{x}+{y}")

        root.after(duration_ms, root.destroy)
        root.mainloop()

    # Fire-and-forget in a daemon thread
    t = threading.Thread(target=_run, daemon=True)
    t.start()
