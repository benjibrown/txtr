# the only reason this isnt in the splash code is cos i wanna avoid it getting too long 
from pathlib import Path

try:
    from importlib.metadata import PackageNotFoundError, version as distVersion
except ImportError:
    PackageNotFoundError = Exception
    distVersion = None

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def _pyprojectVersion():
    root = Path(__file__).resolve().parents[2]
    pyproject = root / "pyproject.toml"
    if not pyproject.exists() or tomllib is None:
        return ""
    try:
        data = tomllib.loads(pyproject.read_text())
    except Exception:
        return ""
    return str(data.get("project", {}).get("version", "")).strip()
# hopefully the versions match 

def appVersion():
    version = _pyprojectVersion()
    if version:
        return version
    if distVersion is not None:
        try:
            return distVersion("texitor")
        except PackageNotFoundError:
            return "dev"
    return "dev"


def displayVersion():
    return f"v{appVersion()}"

