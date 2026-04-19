from texitor.core.keybinds import normalizeKeySequence
# arguably the most peak thing in existence :)

def tryDispatchKey(app, mode, key, char):
    candidate = normalizeKeySequence((app._pending_key + " " + key).strip())
    char_candidate = normalizeKeySequence((app._pending_key + " " + char).strip()) if char else ""

    binding = app.keybinds.get(mode, candidate) or (
        app.keybinds.get(mode, char_candidate) if char_candidate else None
    )
    if binding:
        app._pending_key = ""
        _runBinding(app, binding)
        return True

    if _isPrefix(app, mode, candidate) or (char_candidate and _isPrefix(app, mode, char_candidate)):
        app._pending_key = candidate
        return True

    app._pending_key = ""
    binding = app.keybinds.get(mode, key) or (app.keybinds.get(mode, char) if char else None)
    if binding:
        _runBinding(app, binding)
        return True
    return False


def _isPrefix(app, mode, prefix):
    if not prefix:
        return False
    return any(
        seq == prefix or seq.startswith(prefix + " ")
        for seq in app.keybinds.all_for_mode(mode)
    )


def _runBinding(app, binding):
    if binding.kind == "command":
        app.cmd_input = binding.value.lstrip(":").strip()
        app._action_execute_command()
        return
    handler = getattr(app, f"_action_{binding.value}", None)
    if handler:
        handler()
        return
    # yeah cooked 
    app.notify(f"unknown keybind action: {binding.value}", severity="warning")
