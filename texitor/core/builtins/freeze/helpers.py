from __future__ import annotations

import shlex
from pathlib import Path


def parseFreezeArgs(raw):
    parts = shlex.split(raw) if raw else []
    if not parts:
        return {"mode": "auto", "lines": "", "output": ""}
    if parts[0] == "full":
        return {"mode": "full", "lines": "", "output": parts[1] if len(parts) > 1 else ""}
    if parts[0] == "lines":
        if len(parts) < 2:
            raise ValueError("usage: :freeze lines <start,end> [output]")
        return {
            "mode": "lines",
            "lines": parts[1],
            "output": parts[2] if len(parts) > 2 else "",
        }
    return {"mode": "auto", "lines": "", "output": parts[0]}


def lineRangeArg(line_range):
    if not line_range:
        return ""
    return f"{line_range[0]},{line_range[1]}"


def resolveFreezeConfig(config_name):
    raw = str(config_name or "").strip()
    if not raw:
        return ""
    candidate = Path(raw).expanduser()
    if raw.startswith("~") or "/" in raw or "\\" in raw or raw.endswith(".json"):
        return str(candidate.resolve()) if candidate.exists() else str(candidate)
    return raw


def outputPathFor(file_path, output_override="", line_range=None):
    if output_override:
        return Path(output_override).expanduser()
    p = Path(file_path).expanduser().resolve()
    if line_range:
        return p.parent / f"{p.stem}.{line_range[0]}-{line_range[1]}.freeze.png"
    return p.parent / f"{p.stem}.freeze.png"


def freezePlaceholders(file_path, output_path, line_arg="", config_name="", extra_args=""):
    p = Path(file_path).expanduser().resolve()
    resolved_config = resolveFreezeConfig(config_name)
    quoted_file = shlex.quote(str(p))
    quoted_output = shlex.quote(str(output_path))
    quoted_lines = shlex.quote(line_arg) if line_arg else ""
    quoted_config = shlex.quote(resolved_config) if resolved_config else ""
    lines_arg = f"--lines {quoted_lines}" if quoted_lines else ""
    output_arg = f"--output {quoted_output}" if quoted_output else ""
    config_arg = f"--config {quoted_config}" if quoted_config else ""
    return {
        "FILE": quoted_file,
        "DIR": shlex.quote(str(p.parent)),
        "STEM": shlex.quote(p.stem),
        "LINES": quoted_lines,
        "LINES_ARG": lines_arg,
        "OUTPUT": quoted_output,
        "OUTPUT_ARG": output_arg,
        "CONFIG": quoted_config,
        "CONFIG_ARG": config_arg,
        "EXTRA_ARGS": extra_args,
    }


def buildFreezeCommand(settings, file_path, line_arg="", output_override=""):
    output_path = outputPathFor(file_path, output_override=output_override, line_range=parseLineArg(line_arg))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    extra = settings.get("extra_args", [])
    if isinstance(extra, str):
        extra_list = shlex.split(extra)
    elif isinstance(extra, list):
        extra_list = [str(item) for item in extra if str(item).strip()]
    else:
        extra_list = []
    extra_joined = " ".join(shlex.quote(arg) for arg in extra_list)

    config_name = resolveFreezeConfig(settings.get("config", ""))
    custom = str(settings.get("custom_command", "") or "").strip()
    if custom:
        formatted = custom.format_map(
            freezePlaceholders(
                file_path,
                output_path,
                line_arg=line_arg,
                config_name=config_name,
                extra_args=extra_joined,
            )
        ).strip()
        if not formatted:
            raise ValueError("freeze.custom_command expanded to an empty command")
        return shlex.split(formatted), output_path

    executable = str(settings.get("executable", "freeze") or "freeze").strip()
    cmd = [executable, str(Path(file_path).expanduser().resolve())]
    if config_name:
        cmd += ["--config", config_name]
    if settings.get("show_line_numbers", True):
        cmd.append("--show-line-numbers")
    if line_arg:
        cmd += ["--lines", line_arg]
    cmd += ["--output", str(output_path)]
    cmd.extend(extra_list)
    return cmd, output_path


def parseLineArg(raw):
    if not raw:
        return None
    parts = [part.strip() for part in raw.split(",", 1)]
    if len(parts) != 2:
        raise ValueError("line range must be start,end")
    start = int(parts[0])
    end = int(parts[1])
    if start <= 0 or end <= 0 or end < start:
        raise ValueError("line range must be positive and ascending")
    return (start, end)
