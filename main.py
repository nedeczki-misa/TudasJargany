"""A TudasJargany parancssori belépési pontja."""

from tudasjargany.app import TudasJarganyGame


def main() -> None:
    """Létrehozza és elindítja a játék alkalmazását."""
    TudasJarganyGame().mainloop()


if __name__ == "__main__":
    main()
