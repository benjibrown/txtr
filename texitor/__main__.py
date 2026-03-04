"""Entry point — `txtr [file]`."""

import sys


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else None
    from texitor.ui.app import TxtrApp
    TxtrApp(filename=filename).run()


if __name__ == "__main__":
    main()
