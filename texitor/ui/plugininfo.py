# method so peak it deserved its own file
def pluginInfoRows(meta, loaded, plugin_cmds, config_options=None):
    rows = [
        ("row", "name", meta.get("name") or "(unknown)"),
        ("row", "version", meta.get("version") or "(unknown)"),
        ("row", "author", meta.get("author") or "(unknown)"),
        ("row", "description", meta.get("description") or "(none)"),
        ("row", "type", meta.get("type", "single file")),
        ("row", "status", "loaded" if loaded else "not loaded"),
        ("row", "path", meta.get("path") or "not found on disk"),
    ]
	# cmds and cfg opts are optional in metadata
    if plugin_cmds:
        rows.append(("gap",))
        rows.append(("header", "Commands"))
        for cmd, desc in plugin_cmds:
            rows.append(("text", cmd if not desc else f"{cmd}  {desc}"))
    if config_options:
        rows.append(("gap",))
        rows.append(("header", "Config"))
        for item in config_options:
            default = item.get("default", "")
			# format val for display 
            if isinstance(default, list):
                default = "[" + ", ".join(str(part) for part in default) + "]"
            elif default is True:
                default = "true"
            elif default is False:
                default = "false"
            elif default in ("", None):
                default = "(none)"
            else:
                default = str(default)
            rows.append(("config", item["key"], default, item.get("description") or "(no description)"))
    return rows

