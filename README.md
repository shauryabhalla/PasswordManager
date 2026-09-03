# Password Manager

A tiny system-tray password manager I built for my own Windows laptop because I got tired of typing the same 20character passwords by hand every day. No browser extension, no cloud, no account just a tray icon, a mouse side-button, and an encrypted file that lives on your machine.

Click the side button on your mouse (the one that usually does "back" in a browser) and whatever password you've selected gets typed straight into the focused field.

## How it works

1. Run it, type your master password once.
2. Right-click the tray icon → **Select Password** → pick an entry.
3. Click into a login field somewhere.
4. Press the mouse side button. Password gets typed in, no clipboard involved.

There's a little "Entering password..." popup that flashes in the bottom-right corner so you know it actually fired — mostly there because I kept mashing the side button and not knowing if it registered.

Tray menu also has:
- **Copy Password** / **Copy Username** — if you'd rather paste than auto-type
- **Reload Passwords** — re-reads the encrypted file without restarting
- **Edit Passwords (VS Code)** — decrypts to a temp JSON, opens it in VS Code, re-encrypts when you close the editor
- **Change Master Password** — asks for your current password, then a new one twice, and re-encrypts everything under it
- **Quit**

## Adding / editing passwords

There's no fancy UI for adding entries — you edit a JSON file. Use the tray menu's edit option, it'll open the decrypted list in VS Code (falls back to Notepad if VS Code isn't on PATH). Each entry looks like:

```json
{
  "name": "GitHub",
  "username": "myuser@email.com",
  "password": "s3cretP@ss"
}
```

Save and close the editor and it re-encrypts automatically.

## Setup

1. Python 3.10+ (need the `int | None` type hints)
2. `pip install -r requirements.txt`
3. `python main.py` the first time — it'll ask you to set a master password and generate `passwords.enc` + `salt.bin` next to the code
4. After that, run it with `pythonw.exe main.py` so you don't get a console window sitting there. I just made a shortcut for this:
   ```
   pythonw.exe "C:\Users\<you>\Downloads\Password Manager\main.py"
   ```

## Under the hood

- Vault is a single JSON blob, encrypted with Fernet (`cryptography` lib)
- Key comes from your master password run through PBKDF2-SHA256, 600k iterations, random salt
- Nothing decrypted ever touches disk except briefly during the VS Code edit flow — and that temp file gets deleted right after
- Master password only lives in memory while the app is running, gone on quit
- Auto-type is real keystrokes (`pynput`), not clipboard, so nothing sensitive sits in your clipboard history

Mouse buttons: it's listening for `Button.x1`/`Button.x2` (the side thumb buttons). If your mouse maps those differently, that's the line to change in `main.py`.

Changing the master password (via the tray menu) also generates a brand new salt, not just a new key — so it's a real rotation, not just re-locking the same door.

## What it's not

Didn't want to build a full password manager, so on purpose this doesn't have:
- Auto-start on boot
- Browser/URL matching
- A password generator
- Idle auto-lock
- Any kind of sync 

Might add auto-lock at some point if I keep forgetting to quit it. For now this covers what I actually needed.
