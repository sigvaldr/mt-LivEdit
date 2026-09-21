# LivEdit

A small desktop GUI for batch-editing **MotorTown: Behind The Wheel**
livery decal exports, so you don't have to hand-edit the JSON.

## Requirements

- Python 3.9+ with **Tkinter** (included with the standard installers
  from python.org on Windows and macOS; on Linux, install it if it's
  missing — see below).
- Optional but recommended: `pyperclip`, for reliable clipboard
  support that survives closing the app.

### Linux note

Some Linux distros ship Python without Tkinter. If `python3 main.py`
complains about `tkinter`, install it:

```bash
# Debian/Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

For the clipboard to work reliably on Linux (both with and without
`pyperclip`), you'll also want `xclip` or `xsel` installed:

```bash
sudo apt install xclip
```

## Install & run

```bash
pip install -r requirements.txt   # optional, for pyperclip
python main.py
```

## How to use it

1. **Paste** — Export your livery's decal JSON from the game, paste it
   into the text box, and click **Load**.
2. **Decal list** — Your decals are shown in the same order they
   appear in the in-game list (top of this list = top of the in-game
   list). Select the ones you want to edit, or use **Select All** /
   **Select None**, then click **Continue**.
3. **Operation** — Pick **Move**, **Rotate**, or **Scale**.
4. **Parameters** — Fill in the direction and amount, then **Apply**.
   You're taken back to the decal list so you can select a different
   set of decals and apply another operation.
5. **Export** — Available from every screen via the **Export** button
   in the top-right. Choose **Copy to Clipboard** (to paste straight
   back into the game) or **Save to File** (writes a `.json` file).

## What each operation does

- **Move**: shifts the selected decals **Up / Right / Down / Left** by
  a number of game units.
- **Rotate**: spins the selected decals **Clockwise** /
  **Counter-clockwise** by a number of degrees.
- **Scale**: resizes the selected decals **Larger** / **Smaller** by a
  percentage (e.g. "Larger, 25%" makes a decal 1.25x its current
  size).

## Assumptions worth knowing about

These were figured out from a handful of real decal exports, not from
official documentation, so double check them in-game and adjust if
your game version behaves differently:

- **Y axis**: increasing `position.y` moves a decal **up**, so "Move
  Down" subtracts from `y` (and "Move Up" adds to it). "Move
  Right"/"Move Left" add/subtract from `x`.
- **Rotation axis**: in-plane rotation is applied to `rotation.roll`
  (not `pitch` or `yaw`), since those two appear to orient the decal
  projector onto the body panel while `roll` spins the decal image
  itself. If Clockwise/Counter-clockwise come out backwards in your
  game version, just use the opposite option — the *amount* will
  still be correct either way.
- **Scale**: only `decalScale` is multiplied; `stretch` (a separate
  width multiplier some decals use) is left untouched, so a
  proportional scale doesn't quietly change a decal's aspect ratio.

## Project layout

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
    theme.py               lightning-blue (#00B5FF) on black theme
    icons.py               loads/caches decal preview thumbnails
    widgets.py             scrollable icon+text multi-select list
    resources.py           locates bundled files, in dev or as a frozen exe
  tests/
    test_core.py           unit tests for parsing + operations (no GUI needed)
  requirements.txt
```

Run the tests any time with:

```bash
python tests/test_core.py
```

## Decal preview icons

Drop image files into `assets/decals/`, named to match each decal's
`decalKey` exactly (case-insensitive) — e.g. a decal with
`"decalKey": "sport_stripe_01"` needs a file named
`sport_stripe_01.png` (or `.jpg`, `.gif`, etc. — see below). The decal
list screen will automatically show that image next to the decal's
name. Decals with no matching file just show their name with no icon,
so it's fine to only have images for some of them.

- **Without Pillow**: only `.png`, `.gif`, `.ppm`, `.pgm` are readable,
  and thumbnails can only be *shrunk* (not cleanly enlarged).
- **With Pillow installed** (`pip install Pillow`, already in
  `requirements.txt`): any common format works (`.jpg`, `.bmp`,
  `.webp`, etc.) and thumbnails are resized cleanly regardless of the
  original image's dimensions. Recommended.

## Building a single executable

To ship LivEdit (and any decal preview images in `assets/`) as one
standalone `.exe`/binary with PyInstaller:

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

(Note the `;` vs `:` separator — that's the one difference between
platforms.) The result lands in `dist/` as a single file — no
`assets` folder needs to travel alongside it, since `--add-data`
packs everything into the exe and it's unpacked automatically at
runtime.

If you ever add images or other files outside of `assets/`, use
`livedit.resources.resource_path(...)` to load them rather than a
plain relative path — it already knows how to find bundled files both
when running from source and when running as the frozen exe.

