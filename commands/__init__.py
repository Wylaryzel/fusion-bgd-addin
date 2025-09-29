# commands/__init__.py
from .paletteShow.entry import start as start_palette_show, stop as stop_palette_show
# weitere Commands kannst du hier später ergänzen

def start():
    start_palette_show()

def stop():
    stop_palette_show()
