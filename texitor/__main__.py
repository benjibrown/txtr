# main entry point
import sys
from pathlib import Path


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else None
    startup_notice = None
    show_splash = filename is None
    if filename:
        target = Path(filename).expanduser()
        if target.exists() and target.is_dir():
            startup_notice = f"cannot open directory: {target}"
            filename = None
            show_splash = False
        else:
            filename = str(target)
    from texitor.ui.app import TxtrApp
    TxtrApp(filename=filename, startup_notice=startup_notice, show_splash=show_splash).run()


if __name__ == "__main__":
    main()
