"""
Clipboard access that works on both Windows and Linux.

Preferred path: `pyperclip`, which wraps the native clipboard API on
Windows and shells out to xclip/xsel/wl-clipboard on Linux, and keeps
working after our window closes.

Fallback path: Tk's own clipboard (`clipboard_clear`/`clipboard_append`),
which needs no extra dependency but only reliably holds the content
while the app window is still open (a known X11/Tk limitation on
Linux) - so we ask Tk to keep the window's clipboard ownership alive
briefly via `update()` and warn the user in the UI when this path is
used.
"""
from __future__ import annotations

try:
    import pyperclip  # type: ignore

    _HAS_PYPERCLIP = True
except ImportError:
    _HAS_PYPERCLIP = False


class ClipboardError(Exception):
    pass


def copy_text(text: str, tk_widget=None) -> str:
    """
    Copies `text` to the system clipboard.

    Returns a short status string describing which method was used, so
    the caller can inform the user (e.g. warn about the Tk fallback's
    limitation).

    `tk_widget` is only used for the fallback path and should be any
    live Tk widget (e.g. the root window).
    """
    if _HAS_PYPERCLIP:
        try:
            pyperclip.copy(text)
            return "Copied to clipboard."
        except Exception as exc:  # pyperclip raises its own PyperclipException
            if tk_widget is None:
                raise ClipboardError(f"Could not copy to clipboard: {exc}") from exc
            # fall through to Tk fallback below

    if tk_widget is None:
        raise ClipboardError(
            "Clipboard support isn't available. Install pyperclip "
            "(pip install pyperclip) and, on Linux, also install "
            "xclip or xsel."
        )

    tk_widget.clipboard_clear()
    tk_widget.clipboard_append(text)
    tk_widget.update()  # required on some platforms for the clipboard to actually update
    return (
        "Copied to clipboard (basic mode). Note: on Linux this clipboard "
        "content may be lost once you close LivEdit - paste it elsewhere "
        "before closing, or install pyperclip + xclip for reliable "
        "clipboard support."
    )
