import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES = [
    "01_imports.py", "02_widgets.py", "03_config.py", "04_spotify.py",
    "05_gui.py", "06_audio.py", "07_permissions.py", "08_music.py",
    "09_tiktok.py", "10_main.py"
]

globals_dict = globals()
for filename in FILES:
    path = os.path.join(BASE_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        code = compile(f.read(), path, "exec")
    exec(code, globals_dict)
