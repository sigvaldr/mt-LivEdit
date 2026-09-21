# LivEdit ✨🚗

**A small desktop GUI for batch-editing *MotorTown: Behind The Wheel* livery decal exports — so you don't have to hand-edit JSON.**

Export a livery from the game, tweak dozens of decals at once (move, rotate, scale), and paste the result straight back in.

---

## Table of Contents

- [Requirements](#requirements)
- [Install & Run](#install--run)
- [How to Use It](#how-to-use-it)
- [What Each Operation Does](#what-each-operation-does)
- [Assumptions Worth Knowing About](#assumptions-worth-knowing-about)
- [Decal Preview Icons](#decal-preview-icons)
- [Project Layout](#project-layout)
- [Building a Single Executable](#building-a-single-executable)

---

## Requirements

- **Python 3.9+** with **Tkinter**
  - Included by default with the official installers from python.org on Windows and macOS.
  - On Linux, you may need to install it separately (see below).
- *Optional but recommended:* [`pyperclip`](https://pypi.org/project/pyperclip/), for reliable clipboard support that survives closing the app.

### Linux note

Some distros ship Python without Tkinter. If `python3 main.py` complains about `tkinter`, install it:

```bash
# Debian/Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

For reliable clipboard support on Linux (with or without `pyperclip`), also install:

```bash
sudo apt install xclip
```

---

## Install & Run

```bash
pip install -r requirements.txt   # optional, enables pyperclip
python main.py
```

---

## How to Use It

1. **Paste** — Export your livery's decal JSON from the game, paste it into the text box, and click **Load**.
2. **Decal list** — Your decals appear in the same order as the in-game list (top of this list = top of the in-game list). Select the ones you want to edit — or use **Select All** / **Select None** — then click **Continue**.
3. **Operation** — Pick **Move**, **Rotate**, or **Scale**.
4. **Parameters** — Fill in the direction and amount, then hit **Apply**. You'll be taken back to the decal list to select a different set and apply another operation.
5. **Export** — Available from every screen via the **Export** button in the top-right. Choose **Copy to Clipboard** (paste straight back into the game) or **Save to File** (writes a `.json` file).

---

## What Each Operation Does

| Operation | Description |
|---|---|
| **Move** | Shifts the selected decals **Up / Right / Down / Left** by a number of game units. |
| **Rotate** | Spins the selected decals **Clockwise** / **Counter-clockwise** by a number of degrees. |
| **Scale** | Resizes the selected decals **Larger** / **Smaller** by a percentage (e.g. "Larger, 25%" makes a decal 1.25× its current size). |

---

## Assumptions Worth Knowing About

These were reverse-engineered from real decal exports, not from official documentation — so double-check them in-game and adjust if your game version behaves differently:

- **Y axis** — Increasing `position.y` moves a decal **up**, so "Move Down" subtracts from `y` (and "Move Up" adds to it). "Move Right" / "Move Left" add/subtract from `x`.
- **Rotation axis** — In-plane rotation is applied to `rotation.roll` (not `pitch` or `yaw`), since those two appear to orient the decal projector onto the body panel, while `roll` spins the decal image itself. If Clockwise/Counter-clockwise come out backwards in your game version, just use the opposite option — the *amount* will still be correct either way.
- **Scale** — Only `decalScale` is multiplied; `stretch` (a separate width multiplier some decals use) is left untouched, so a proportional scale won't quietly change a decal's aspect ratio.

---

## Decal Preview Icons

Drop image files into `assets/decals/`, named to match each decal's `decalKey` exactly (case-insensitive). For example, a decal with `"decalKey": "sport_stripe_01"` needs a file named `sport_stripe_01.png` (or `.jpg`, `.gif`, etc.). The decal list screen will automatically show that image next to the decal's name — decals with no matching file just show their name with no icon, so it's fine to only have images for some of them.

- **Without Pillow**: only `.png`, `.gif`, `.ppm`, `.pgm` are readable, and thumbnails can only be *shrunk* (not cleanly enlarged).
- **With Pillow installed** (`pip install Pillow`, already in `requirements.txt`): any common format works (`.jpg`, `.bmp`, `.webp`, etc.) and thumbnails are resized cleanly regardless of the original image's dimensions. **Recommended.**

---

## Project Layout

```
livedit/
  main.py                  entry point (python main.py)
  assets/
    decals/                decal preview images, named to match decalKey
  livedit/
    app.py                 all GUI screens + navigation
    decal_model.py         JSON parsing + in-game display ordering
    operations.py          move / rotate / scale math
    clipboard_util.py      cross-platform clipboard (pyperclip + Tk fallback)
    theme.py                lightning-blue (#00B5FF) on black theme
    icons.py                loads/caches decal preview thumbnails
    widgets.py              scrollable icon+text multi-select list
    resources.py            locates bundled files, in dev or as a frozen exe
  tests/
    test_core.py            unit tests for parsing + operations (no GUI needed)
  requirements.txt
```

Run the tests any time with:

```bash
python tests/test_core.py
```

---

## Building a Single Executable

To ship LivEdit (and any decal preview images in `assets/`) as one standalone `.exe`/binary with [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
```

**Windows:**

```bash
pyinstaller --onefile --windowed --add-data "assets;assets" main.py
```

**Linux/macOS:**

```bash
pyinstaller --onefile --windowed --add-data "assets:assets" main.py
```

*(Note the `;` vs `:` separator — that's the one difference between platforms.)*

The result lands in `dist/` as a single file — no `assets` folder needs to travel alongside it, since `--add-data` packs everything into the exe and it's unpacked automatically at runtime.

> **Tip:** If you ever add images or other files outside of `assets/`, use `livedit.resources.resource_path(...)` to load them rather than a plain relative path — it already knows how to find bundled files both when running from source and when running as the frozen exe.

---

## About

External Livery/Decal editor for **MotorTown: Behind The Wheel**.
