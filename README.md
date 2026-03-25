## Tech Stack

- **Language:** Python 3.x
- **OS:** Windows 10/11
- **IDE:** VS Code
- **Key Libraries:**
  - `pynput` — global mouse button listener (side button: Button.x1 or Button.x2)
  - `pystray` + `Pillow` — system tray icon and menu
  - `cryptography` (Fernet) — encrypt/decrypt the password store file
  - `tkinter` — small notification popup (bundled with Python, no extra install)
  - `pyautogui` or `pynput.keyboard` — simulate keystrokes to type passwords
  - `pyperclip` — copy-to-clipboard functionality

---

## Core Features

### 1. Encrypted Password Store
- Passwords are stored in a single JSON file (`passwords.json`), encrypted at rest using Fernet symmetric encryption.
- On launch, the user enters a **master password** once. This derives the encryption key (use PBKDF2 or similar KDF with a random salt stored alongside the file).
- The decrypted password data is held **only in memory** while the app runs.
- The JSON structure is a **flat list**, each entry containing:
  ```json
  {
    "name": "GitHub",
    "username": "myuser@email.com",
    "password": "s3cretP@ss"
  }
  ```
- Users **add/edit/delete** passwords by editing the JSON file directly in VS Code. The app should provide a tray menu option to:
  - **Reload passwords** — re-reads and re-decrypts the file without restarting the app.
  - **Open passwords file** — opens the decrypted JSON in VS Code for editing, then re-encrypts on save/close. *(Or: provide a CLI/tray option to decrypt → edit → re-encrypt.)*

### 2. System Tray App
- On launch (after master password entry), the app minimizes to the **Windows system tray** (notification area near the clock).
- **No console window** should be visible (run via `pythonw.exe`).
- Right-click tray menu options:
  - **Select Password** — shows the list of saved entry names; clicking one sets it as the "active" password ready to type.
  - **Reload Passwords** — re-reads the encrypted file.
  - **Copy Password** — copies the currently selected password to clipboard.
  - **Copy Username** — copies the currently selected username to clipboard.
  - **Quit** — exits the app cleanly.

### 3. Mouse Side-Button Trigger
- The app listens globally for **mouse side button click** (Button.x1 or Button.x2 — typically the "back" thumb button).
- When triggered:
  - The app **auto-types the currently selected password** into whatever field/window has focus.
  - It types the **password only** (no username, no Tab key).
  - A **small popup notification** appears briefly in the **bottom-right corner** of the screen saying "Entering password..." (or similar), then auto-dismisses after ~1 second.
- **Important:** Add a clear `# COMMENT` in the code around the popup logic so it can be easily commented out in the future if the user no longer wants the notification.

### 4. Copy to Clipboard
- As an alternative to auto-type, the user can right-click the tray icon and choose **Copy Password** or **Copy Username** to copy the selected entry's credentials to the clipboard.
- Use `pyperclip` for clipboard operations.

---

## Password Selection Flow

Since the UI is minimal (no searchable popup window), the flow is:

1. **Right-click tray icon → Select Password → pick an entry name** from the submenu.
2. That entry becomes the **"active" password**.
3. Navigate to the login page, click on the password field.
4. **Press mouse side button** → password is auto-typed.

The tray icon tooltip or menu should show which entry is currently selected (e.g., `✓ GitHub`).

---

## What This App Does NOT Do

- No auto-start with Windows (user launches manually).
- No auto-URL matching or browser integration.
- No password generator.
- No auto-lock / idle timeout.
- No multi-user support.
- No cloud sync.

---

## Security Requirements

- Master password is **never stored** anywhere — it is entered at runtime and used to derive the key.
- Use **PBKDF2** (or Argon2 if available) with a random salt for key derivation. Store the salt in a separate small file or as a header in the encrypted file.
- Decrypted passwords exist **only in memory**.
- Auto-type simulates keystrokes (does not use clipboard), reducing clipboard exposure.
- When the app quits, all in-memory password data should be cleared.

---

## File/Folder Structure (Suggested)

```
password-manager/
├── main.py              # Entry point — master password prompt, tray app, mouse listener
├── crypto.py            # Encryption/decryption helpers (Fernet + PBKDF2)
├── autotype.py          # Keystroke simulation logic
├── popup.py             # Bottom-right notification popup (tkinter)  ← commentable
├── passwords.enc        # Encrypted password store (generated on first run)
├── salt.bin             # Random salt for key derivation (generated on first run)
├── requirements.txt     # pip dependencies
└── README.md            # Setup & usage instructions
```

---

## Setup & Run Instructions (Include in README)

1. Install Python 3.x from python.org (check "Add to PATH").
2. `pip install pynput pystray Pillow cryptography pyautogui pyperclip`
3. First run: `python main.py` — prompts for a master password, creates `passwords.enc` and `salt.bin`.
4. To add passwords: use the tray menu to decrypt/open the JSON, edit in VS Code, save, then reload from tray.
5. Daily use: `pythonw.exe main.py` (no console window) or create a shortcut.         
For me personally this works - pythonw.exe `C:\Users\REDACTED\Downloads\Password Manager\main.py`

---

## Nice-to-Have / Future Enhancements (Out of Scope for Now)

- Searchable popup window on side-button click.
- Auto-match passwords to active window/URL.
- Password strength checker / generator.
- Auto-lock after idle.
- Auto-start with Windows (Task Scheduler or Startup folder).
- Backup/export of password store.
