"""A TudasJargany indító belépési pontja.

A teljes játékalkalmazás a tudasjargany.app modulban található.
"""
from tudasjargany.app import *  # noqa: F401,F403


if __name__ == "__main__":
    TudasJarganyGame().mainloop()