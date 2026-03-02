# txtr entry point, placeholder for now
from __future__ import annotations
import sys


def main() -> None:
    filename: str | None = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"txtr: would open {filename!r}")  # placeholder until i can be bothered to implement the actual editor


if __name__ == "__main__":
    main()
