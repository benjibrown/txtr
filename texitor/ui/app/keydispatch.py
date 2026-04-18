from texitor.core.keybinds import normalizeKeySequence
# arguably the most peak thing in existence :)

def tryDispatchKey(app, mode, key, char):
    candidate = normalizeKeySequence((app._pending_key + " " + key).strip())
    char_candidate = normalizeKeySequence((app._pending_key + " " + char).strip()) if char else ""

    binding = app.keybinds.get(mode, candidate) or ()
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



