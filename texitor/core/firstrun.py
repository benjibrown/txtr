# first run setup - copies bundled default configs to ~/.config/txtr/ if not present
# safe to call every launch - only writes files that are missing

import shutil
from pathlib import Path

_latexDir = Path(__file__).parent.parent / "latex"
_coreDir  = Path(__file__).parent

# files to seed - (source_dir, filename)
_CONFIG_FILES = [
    (_latexDir, "snippets.toml"),
    (_latexDir, "commands.toml"),
    (_coreDir,  "config_default.toml"),  # seeded as config.toml
]

def ensureUserConfig():
    userDir = Path.home() / ".config" / "txtr"
    userDir.mkdir(parents=True, exist_ok=True)

    for srcDir, filename in _CONFIG_FILES:
        # config_default.toml seeds as config.toml
        destName = "config.toml" if filename == "config_default.toml" else filename
        dest = userDir / destName
        if not dest.exists():
            src = srcDir / filename
            if src.exists():
                shutil.copy2(src, dest)
