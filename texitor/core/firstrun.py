# first run setup - copies bundled default configs to ~/.config/txtr/ if not present
# safe to call every launch - only writes files that are missing

import shutil
from pathlib import Path

# bundled defaults live alongside the source
_bundledDir = Path(__file__).parent.parent / "latex"

# all config files to seed on first run
_CONFIG_FILES = [
    "snippets.toml",
    "commands.toml",
]

def ensureUserConfig():
    userDir = Path.home() / ".config" / "txtr"
    userDir.mkdir(parents=True, exist_ok=True)

    for filename in _CONFIG_FILES:
        dest = userDir / filename
        if not dest.exists():
            src = _bundledDir / filename
            if src.exists():
                shutil.copy2(src, dest)
