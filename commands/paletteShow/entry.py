import adsk.core, traceback, os, json

_app = adsk.core.Application.get()
_ui  = _app.userInterface

_CMD_ID = 'BGD_ShowPalette'
_CMD_NAME = 'Boardgame Insert'
_CMD_DESC = 'Öffnet die Boardgame-Insert Palette'

_PALETTE_ID = 'BGD_Palette'
_cmd_def = None

# Wir halten Delegates am Leben
_handlers = []

def _on_html_event_received(args: adsk.core.HTMLEventArgs):
    """
    Empfängt Nachrichten aus dem HTML (window.adsk.fusionJavaScriptHandler.sendData)
    Erwartet JSON-Strings mit mind. "type"
    """
    try:
        data = json.loads(args.data or '{}')
        msg_type = data.get('type')

        if msg_type == 'ping':
            # Antworte ins HTML
            payload = {'type': 'pong', 'ts': adsk.core.ValueInput.createByString('now')}
            _send_to_html(payload)

        elif msg_type == 'save_settings':
            # Beispiel: einfache Settings im Design als Attribut speichern
            attrs = data.get('payload', {})
            _set_design_attributes('bgd_settings', attrs)
            _send_to_html({'type': 'saved', 'payload': attrs})

        elif msg_type == 'load_settings':
            attrs = _get_design_attributes('bgd_settings')
            _send_to_html({'type': 'settings', 'payload': attrs})

        else:
            _ui.messageBox(f'Unbekannter HTML-Event: {msg_type}')

    except Exception:
        _ui.messageBox('Fehler in _on_html_event_received:\n{}'.format(traceback.format_exc()))

def _send_to_html(payload: dict):
    try:
        pal = _ui.palettes.itemById(_PALETTE_ID)
        if pal:
            pal.sendInfoToHTML('bgd-message', json.dumps(payload))
    except:
        _ui.messageBox('Fehler beim Senden an HTML:\n{}'.format(traceback.format_exc()))

def _on_command_created(args: adsk.core.CommandCreatedEventArgs):
    try:
        pal = _ui.palettes.itemById(_PALETTE_ID)
        if not pal:
            html_path = os.path.join(os.path.dirname(__file__), 'resources', 'palette.html')
            pal = _ui.palettes.add(
                _PALETTE_ID, 'Boardgame Insert', html_path,
                True, True, True, 420, 560
            )
            # HTML→Python
            pal.incomingFromHTML.add(_on_html_event_received)
            _handlers.append(_on_html_event_received)

        pal.isVisible = True

        # Beim Öffnen einmal Settings rüberschicken
        attrs = _get_design_attributes('bgd_settings')
        _send_to_html({'type': 'settings', 'payload': attrs})

    except:
        _ui.messageBox('Fehler beim Erstellen/Öffnen der Palette:\n{}'.format(traceback.format_exc()))

def start():
    global _cmd_def
    _cmd_def = _ui.commandDefinitions.itemById(_CMD_ID)
    if not _cmd_def:
        _cmd_def = _ui.commandDefinitions.addButtonDefinition(_CMD_ID, _CMD_NAME, _CMD_DESC)

    _cmd_def.commandCreated.add(_on_command_created)
    _handlers.append(_on_command_created)

    tab = _ui.allToolbarTabs.itemById('SolidScriptsAddinsTab')
    panel = tab.toolbarPanels.itemById('ScriptsAddinsPanel')
    if panel.controls.itemById(_CMD_ID) is None:
        panel.controls.addCommand(_cmd_def)

def stop():
    # Palette schließen/entfernen
    try:
        pal = _ui.palettes.itemById(_PALETTE_ID)
        if pal:
            pal.deleteMe()
    except:
        pass

    # Button entfernen
    try:
        tab = _ui.allToolbarTabs.itemById('SolidScriptsAddinsTab')
        panel = tab.toolbarPanels.itemById('ScriptsAddinsPanel')
        ctl = panel.controls.itemById(_CMD_ID)
        if ctl:
            ctl.deleteMe()
    except:
        pass

    if _cmd_def:
        _cmd_def.deleteMe()

# --- Kleine Helper für Attribute am Design (persistenter Speicher) ---

def _get_attr_set():
    try:
        des = adsk.fusion.Design.cast(_app.activeProduct)
        if not des:
            return None, None
        root = des.rootComponent
        return des, root.attributes
    except:
        return None, None

def _set_design_attributes(group: str, d: dict):
    des, attrs = _get_attr_set()
    if not attrs: return
    for k, v in (d or {}).items():
        attrs.add(group, str(k), json.dumps(v))

def _get_design_attributes(group: str) -> dict:
    des, attrs = _get_attr_set()
    if not attrs: return {}
    out = {}
    for i in range(attrs.count):
        a = attrs.item(i)
        if a.groupName == group:
            try:
                out[a.attributeName] = json.loads(a.value)
            except:
                out[a.attributeName] = a.value
    return out
