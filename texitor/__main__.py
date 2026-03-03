"""Entry point — `txtr [file]`."""

from __future__ import annotations
import sys


def main() -> None:
    filename: str | None = sys.argv[1] if len(sys.argv) > 1 else None
    from texitor.ui.app import TxtrApp
    TxtrApp(filename=filename).run()


if __name__ == "__main__":
    main()
