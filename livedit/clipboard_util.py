
from __future__ import annotations

try:
    import pyperclip  # type: ignore

    _HAS_PYPERCLIP = True
except ImportError:
    _HAS_PYPERCLIP = False


class ClipboardError(Exception):
    pass


def copy_text(text: str, tk_widget=None) -> str:

    if _HAS_PYPERCLIP:
        try:
            pyperclip.copy(text)
            return "Copied to clipboard."
        except Exception as exc:  # pyperclip raises its own PyperclipException
            if tk_widget is None:
                raise ClipboardError(
                    f"Could not copy to clipboard: {exc}") from exc
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
