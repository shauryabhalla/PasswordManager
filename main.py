"""
main.py — Password Manager entry point.

Flow:
  1. Prompt for master password (tkinter dialog).
  2. Decrypt the password store into memory.
  3. Start the system-tray icon with right-click menu.
  4. Listen globally for mouse side-button click to auto-type.
"""

import sys
import os
import threading
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox

import pyperclip
from pynput import mouse
from PIL import Image, ImageDraw
import pystray

from crypto import load_passwords, decrypt_to_temp, encrypt_from_temp
from autotype import type_string

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POPUP NOTIFICATION — Comment out the next import AND the
# show_popup() call inside on_side_button() to disable popups.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from popup import show_popup


# ── Global state ──────────────────────────────────────────────
master_password: str = ""
passwords: list[dict] = []
selected_index: int | None = None   # index into `passwords`
tray_icon: pystray.Icon | None = None
mouse_listener: mouse.Listener | None = None


# ── Helper: create a simple tray icon image ──────────────────
def _create_icon_image() -> Image.Image:
    """Generate a small 64×64 key icon."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Simple padlock-ish shape
    draw.ellipse([16, 8, 48, 36], outline="#89b4fa", width=3)
    draw.rectangle([12, 30, 52, 56], fill="#89b4fa")
    draw.rectangle([28, 38, 36, 50], fill="#1e1e2e")
    return img


# ── Password selection ────────────────────────────────────────
def _select_password(index: int):
    """Set the active password by index and refresh the tray menu."""
    global selected_index
    selected_index = index
    _rebuild_menu()


def _get_selected_entry() -> dict | None:
    if selected_index is not None and 0 <= selected_index < len(passwords):
        return passwords[selected_index]
    return None


# ── Tray menu actions ────────────────────────────────────────
def _on_copy_password(icon, item):
    entry = _get_selected_entry()
    if entry:
        pyperclip.copy(entry.get("password", ""))


def _on_copy_username(icon, item):
    entry = _get_selected_entry()
    if entry:
        pyperclip.copy(entry.get("username", ""))


def _on_reload(icon, item):
    global passwords, selected_index
    try:
        passwords = load_passwords(master_password)
        selected_index = None
        _rebuild_menu()
    except Exception as e:
        _show_error(f"Reload failed: {e}")


def _on_edit_passwords(icon, item):
    """Decrypt to a temp JSON, open in VS Code, wait, re-encrypt."""
    global passwords, selected_index
    try:
        temp_path = decrypt_to_temp(master_password)

        # Try VS Code first, fall back to notepad
        try:
            proc = subprocess.Popen(["code", "--wait", temp_path])
        except FileNotFoundError:
            proc = subprocess.Popen(["notepad.exe", temp_path])

        # Wait in a background thread so the tray stays responsive
        def _wait_and_encrypt():
            global passwords, selected_index
            proc.wait()
            try:
                passwords = encrypt_from_temp(master_password)
                selected_index = None
                _rebuild_menu()
            except Exception as e:
                _show_error(f"Re-encryption failed: {e}")

        threading.Thread(target=_wait_and_encrypt, daemon=True).start()

    except Exception as e:
        _show_error(f"Edit failed: {e}")


def _on_quit(icon, item):
    global passwords, master_password
    # Clear sensitive data from memory
    passwords = []
    master_password = ""
    if mouse_listener:
        mouse_listener.stop()
    icon.stop()


# ── Tray menu builder ────────────────────────────────────────
def _rebuild_menu():
    if tray_icon is None:
        return

    # Build the "Select Password" submenu
# Build the "Select Password" submenu
    pw_items = []

    def _make_select_callback(idx):
        """Factory to create a proper 2-arg callback capturing idx."""
        def _callback(icon, item):
            _select_password(idx)
        return _callback

    for i, entry in enumerate(passwords):
        name = entry.get("name", f"Entry {i}")
        prefix = "✓ " if i == selected_index else "   "
        pw_items.append(
            pystray.MenuItem(
                f"{prefix}{name}",
                _make_select_callback(i),
            )
        )

    if not pw_items:
        pw_items.append(pystray.MenuItem("(no passwords)", None, enabled=False))

    selected_label = ""
    entry = _get_selected_entry()
    if entry:
        selected_label = f"  [{entry.get('name', '')}]"

    menu = pystray.Menu(
        pystray.MenuItem(f"Select Password{selected_label}", pystray.Menu(*pw_items)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Copy Password", _on_copy_password, enabled=selected_index is not None),
        pystray.MenuItem("Copy Username", _on_copy_username, enabled=selected_index is not None),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Reload Passwords", _on_reload),
        pystray.MenuItem("Edit Passwords (VS Code)", _on_edit_passwords),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", _on_quit),
    )
    tray_icon.menu = menu
    tray_icon.update_menu()


# ── Mouse listener ────────────────────────────────────────────
def _on_click(x, y, button, pressed):
    """Global mouse callback — triggers auto-type on side button press."""
    # React on button-down only
    if not pressed:
        return

    # Side buttons: Button.x1 (back) or Button.x2 (forward)
    # Change it to whichever button you want Ex. "mouse.Button.middle" — middle click (scroll wheel click)
    if button in (mouse.Button.x1, mouse.Button.x2):
        entry = _get_selected_entry()
        if entry is None:
            return

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # POPUP — Comment out the next line to disable the popup
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        show_popup(f"Typing: {entry.get('name', '?')}")

        # Small delay to let the popup render and focus return
        import time
        time.sleep(0.15)

        type_string(entry.get("password", ""))


# ── Error helper ──────────────────────────────────────────────
def _show_error(msg: str):
    """Show a quick error messagebox (in its own thread to avoid blocking)."""
    def _run():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Password Manager", msg)
        root.destroy()
    threading.Thread(target=_run, daemon=True).start()


# ── Master password prompt ────────────────────────────────────
def _prompt_master_password() -> str | None:
    """Show a tkinter dialog to collect the master password."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    pwd = simpledialog.askstring(
        "Password Manager",
        "Enter master password:",
        show="*",
        parent=root,
    )
    root.destroy()
    return pwd


# ── Main ──────────────────────────────────────────────────────
def main():
    global master_password, passwords, tray_icon, mouse_listener

    # 1. Prompt for master password
    master_password = _prompt_master_password()
    if not master_password:
        sys.exit(0)

    # 2. Decrypt password store
    try:
        passwords = load_passwords(master_password)
    except ValueError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Password Manager", str(e))
        root.destroy()
        sys.exit(1)

    # 3. Start mouse listener (runs in its own thread)
    mouse_listener = mouse.Listener(on_click=_on_click)
    mouse_listener.start()

    # 4. Build & run system tray icon (blocks on this thread)
    tray_icon = pystray.Icon(
        "password-manager",
        icon=_create_icon_image(),
        title="Password Manager",
    )
    _rebuild_menu()
    tray_icon.run()


if __name__ == "__main__":
    main()
