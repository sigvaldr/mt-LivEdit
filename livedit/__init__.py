def main() -> None:
    """Launches the LivEdit GUI. Imported lazily so that the non-GUI
    modules (decal_model, operations) can be imported/tested in
    environments without tkinter installed."""
    from .app import main as _main
    _main()


__all__ = ["main"]
