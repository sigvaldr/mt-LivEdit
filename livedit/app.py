"""
LivEdit - a small GUI to batch move/rotate/scale MotorTown: Behind The
Wheel livery decals, without hand-editing the exported JSON.

Flow:
    Paste screen -> Decal list -> Operation select -> Operation params
    -> (back to) Decal list
An Export button is always available and opens the Export screen from
wherever you are.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .decal_model import LiveryDocument, DecalParseError
from . import operations
from .clipboard_util import copy_text, ClipboardError
from . import theme

APP_TITLE = "LivEdit"
PAD = 10


class LivEditApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("800x800")
        self.minsize(600, 650)
        theme.apply_theme(self)

        # ---- app state ----
        self.document: LiveryDocument | None = None
        self.selected_storage_indices: set[int] = set()
        self.pending_operation: str | None = None  # "move" | "rotate" | "scale"

        # ---- persistent chrome ----
        header = ttk.Frame(self, padding=(PAD, PAD, PAD, 0))
        header.pack(fill="x")
        self.title_label = ttk.Label(
            header, text=APP_TITLE, font=("TkDefaultFont", 14, "bold"))
        self.title_label.pack(side="left")
        self.export_button = ttk.Button(
            header, text="Export", command=self.go_to_export)
        self.export_button.pack(side="right")
        self.import_button = ttk.Button(
            header, text="Import", command=self.show_paste_screen)
        self.import_button.pack(side="right", padx=(0, PAD))

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(PAD, 0))

        # ---- swappable body ----
        self.body = ttk.Frame(self, padding=PAD)
        self.body.pack(fill="both", expand=True)

        self._current_screen: ttk.Frame | None = None
        self._update_export_availability()
        self.show_paste_screen()

    # ------------------------------------------------------------------
    # navigation helpers
    # ------------------------------------------------------------------
    def _set_screen(self, screen_cls) -> None:
        if self._current_screen is not None:
            self._current_screen.destroy()
        self._current_screen = screen_cls(self.body, self)
        self._current_screen.pack(fill="both", expand=True)
        self._update_export_availability()

    def _update_export_availability(self) -> None:
        self.export_button.state(
            ["!disabled"] if self.document is not None else ["disabled"])

    def show_paste_screen(self) -> None:
        self._set_screen(PasteScreen)

    def show_decal_list_screen(self) -> None:
        self._set_screen(DecalListScreen)

    def show_operation_select_screen(self) -> None:
        if not self.selected_storage_indices:
            messagebox.showinfo(APP_TITLE, "Select at least one decal first.")
            return
        self._set_screen(OperationSelectScreen)

    def show_operation_params_screen(self, operation: str) -> None:
        self.pending_operation = operation
        self._set_screen({
            "move": MoveParamsScreen,
            "rotate": RotateParamsScreen,
            "scale": ScaleParamsScreen,
        }[operation])

    def go_to_export(self) -> None:
        if self.document is None:
            messagebox.showinfo(APP_TITLE, "Load a decal export first.")
            return
        self._set_screen(ExportScreen)

    # ------------------------------------------------------------------
    # data helpers
    # ------------------------------------------------------------------
    def load_document(self, text: str) -> None:
        self.document = LiveryDocument.from_text(text)
        self.selected_storage_indices = set()

    def selected_layers(self) -> list[dict]:
        assert self.document is not None
        layers = self.document.layers
        return [layers[i] for i in self.selected_storage_indices]

    def apply_operation_and_return(self, apply_fn) -> None:
        """Runs apply_fn() (which mutates the selected layers), then goes
        back to the decal list screen."""
        try:
            apply_fn()
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            return
        self.show_decal_list_screen()


# ==========================================================================
# Screens
# ==========================================================================


class PasteScreen(ttk.Frame):
    """First screen: paste the raw decal export JSON from the game."""

    def __init__(self, parent: tk.Widget, app: LivEditApp) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(
            self,
            text="Paste your decal export from MotorTown below, then click Load.",
            wraplength=560,
        ).pack(anchor="w", pady=(0, PAD))

        # A single-line entry rather than a tall text box: it holds the
        # whole pasted export (scrolling horizontally as needed) without
        # pushing the Load button out of view.
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.entry_var)
        self.entry.pack(fill="x", pady=(0, PAD))
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda _event: self._on_load())

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(PAD, 0))
        ttk.Button(button_row, text="Load",
                   command=self._on_load).pack(side="right")

    def _on_load(self) -> None:
        raw_text = self.entry_var.get()
        try:
            self.app.load_document(raw_text)
        except DecalParseError as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            return
        self.app.show_decal_list_screen()


class DecalListScreen(ttk.Frame):
    """Shows decals in in-game order with multi-select, Select All/None."""

    def __init__(self, parent: tk.Widget, app: LivEditApp) -> None:
        super().__init__(parent)
        self.app = app
        assert app.document is not None
        # [(storage_index, label), ...]
        self.rows = app.document.display_rows()

        ttk.Label(
            self,
            text="Your decals (top of this list = top of the in-game list). "
                 "Select one or more, then Continue.",
            wraplength=560,
        ).pack(anchor="w", pady=(0, PAD))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(
            list_frame, selectmode="extended", activestyle="dotbox")
        theme.style_listbox(self.listbox)
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for _, label in self.rows:
            self.listbox.insert("end", label)

        # restore previous selection, if any (e.g. coming back after Apply)
        for display_pos, (storage_index, _) in enumerate(self.rows):
            if storage_index in app.selected_storage_indices:
                self.listbox.selection_set(display_pos)

        select_row = ttk.Frame(self)
        select_row.pack(fill="x", pady=(PAD, 0))
        ttk.Button(select_row, text="Select All",
                   command=self._select_all).pack(side="left")
        ttk.Button(select_row, text="Select None", command=self._select_none).pack(
            side="left", padx=(PAD, 0))

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(PAD, 0))
        ttk.Button(button_row, text="Continue",
                   command=self._on_continue).pack(side="right")

    def _select_all(self) -> None:
        self.listbox.selection_set(0, "end")

    def _select_none(self) -> None:
        self.listbox.selection_clear(0, "end")

    def _sync_selection_to_app(self) -> None:
        selected_positions = self.listbox.curselection()
        self.app.selected_storage_indices = {
            self.rows[pos][0] for pos in selected_positions
        }

    def _on_continue(self) -> None:
        self._sync_selection_to_app()
        self.app.show_operation_select_screen()


class OperationSelectScreen(ttk.Frame):
    """Choose Move / Rotate / Scale for the current selection."""

    def __init__(self, parent: tk.Widget, app: LivEditApp) -> None:
        super().__init__(parent)
        self.app = app

        count = len(app.selected_storage_indices)
        ttk.Label(
            self,
            text=f"{count} decal(s) selected. Choose an operation:",
        ).pack(anchor="w", pady=(0, PAD))

        for label, op in (("Move", "move"), ("Rotate", "rotate"), ("Scale", "scale")):
            ttk.Button(
                self, text=label, width=20,
                command=lambda op=op: app.show_operation_params_screen(op),
            ).pack(anchor="w", pady=4)

        ttk.Button(self, text="Back to decal list", command=app.show_decal_list_screen).pack(
            anchor="w", pady=(PAD, 0)
        )


class _ParamsScreenBase(ttk.Frame):
    """Shared layout for the three parameter screens: a title, a radio
    group of direction choices, a numeric entry, and Apply/Cancel."""

    title_text = ""
    direction_label = ""
    directions: tuple[tuple[str, str], ...] = ()  # (value, display label)
    amount_label = ""

    def __init__(self, parent: tk.Widget, app: LivEditApp) -> None:
        super().__init__(parent)
        self.app = app

        count = len(app.selected_storage_indices)
        ttk.Label(
            self, text=f"{self.title_text} - {count} decal(s) selected",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", pady=(0, PAD))

        ttk.Label(self, text=self.direction_label).pack(anchor="w")
        self.direction_var = tk.StringVar(value=self.directions[0][0])
        for value, label in self.directions:
            ttk.Radiobutton(
                self, text=label, value=value, variable=self.direction_var
            ).pack(anchor="w")

        ttk.Label(self, text=self.amount_label).pack(anchor="w", pady=(PAD, 0))
        self.amount_var = tk.StringVar(value="10")
        ttk.Entry(self, textvariable=self.amount_var,
                  width=12).pack(anchor="w")

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(PAD, 0), side="bottom")
        ttk.Button(button_row, text="Cancel",
                   command=app.show_operation_select_screen).pack(side="left")
        ttk.Button(button_row, text="Apply",
                   command=self._on_apply).pack(side="right")

    def _parse_amount(self) -> float | None:
        try:
            value = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror(APP_TITLE, "Enter a number.")
            return None
        if value < 0:
            messagebox.showerror(
                APP_TITLE, "Enter a positive number; use the direction option for sign.")
            return None
        return value

    def _on_apply(self) -> None:
        raise NotImplementedError


class MoveParamsScreen(_ParamsScreenBase):
    title_text = "Move"
    direction_label = "Direction:"
    directions = (
        ("up", "Up"),
        ("right", "Right"),
        ("down", "Down"),
        ("left", "Left"),
    )
    amount_label = "Move by (game units):"

    def _on_apply(self) -> None:
        amount = self._parse_amount()
        if amount is None:
            return
        direction = self.direction_var.get()
        self.app.apply_operation_and_return(
            lambda: operations.move(
                self.app.selected_layers(), direction, amount)
        )


class RotateParamsScreen(_ParamsScreenBase):
    title_text = "Rotate"
    direction_label = "Direction:"
    directions = (
        ("clockwise", "Clockwise"),
        ("counterclockwise", "Counter-clockwise"),
    )
    amount_label = "Degrees:"

    def _on_apply(self) -> None:
        amount = self._parse_amount()
        if amount is None:
            return
        direction = self.direction_var.get()
        self.app.apply_operation_and_return(
            lambda: operations.rotate(
                self.app.selected_layers(), direction, amount)
        )


class ScaleParamsScreen(_ParamsScreenBase):
    title_text = "Scale"
    direction_label = "Direction:"
    directions = (
        ("larger", "Larger"),
        ("smaller", "Smaller"),
    )
    amount_label = "Percent:"

    def _on_apply(self) -> None:
        amount = self._parse_amount()
        if amount is None:
            return
        direction = self.direction_var.get()
        self.app.apply_operation_and_return(
            lambda: operations.scale(
                self.app.selected_layers(), direction, amount)
        )


class ExportScreen(ttk.Frame):
    """Copy to clipboard, or save to a .json file."""

    def __init__(self, parent: tk.Widget, app: LivEditApp) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(
            self, text="Export your edited livery:",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(anchor="w", pady=(0, PAD))

        ttk.Button(self, text="Copy to Clipboard", width=24, command=self._on_copy).pack(
            anchor="w", pady=4
        )
        ttk.Button(self, text="Save to File...", width=24, command=self._on_save).pack(
            anchor="w", pady=4
        )

        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, wraplength=560, foreground=theme.BLUE).pack(
            anchor="w", pady=(PAD, 0)
        )

        ttk.Button(self, text="Back", command=self._on_back).pack(
            anchor="w", pady=(PAD, 0), side="bottom")

    def _on_back(self) -> None:
        if self.app.selected_storage_indices:
            self.app.show_operation_select_screen()
        else:
            self.app.show_decal_list_screen()

    def _on_copy(self) -> None:
        assert self.app.document is not None
        text = self.app.document.to_json()
        try:
            status = copy_text(text, tk_widget=self.app)
        except ClipboardError as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            return
        self.status_var.set(status)

    def _on_save(self) -> None:
        assert self.app.document is not None
        path = filedialog.asksaveasfilename(
            title="Save livery JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.app.document.to_json())
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Could not save file: {exc}")
            return
        self.status_var.set(f"Saved to {path}")


def main() -> None:
    app = LivEditApp()
    app.mainloop()
