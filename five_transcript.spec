# PyInstaller specification for the Windows distribution folder.
from pathlib import Path

root = Path(SPECPATH)
datas = [
    (str(root / "models" / "faster-whisper-small"), "models/faster-whisper-small"),
    (str(root / "assets" / "ffmpeg" / "bin" / "ffmpeg.exe"), "assets/ffmpeg/bin"),
]
logo = root / "assets" / "logo.png"
if logo.is_file():
    datas.append((str(logo), "assets"))
icon = root / "assets" / "icon.ico"

a = Analysis([str(root / "app.py")], pathex=[str(root)], binaries=[], datas=datas, hiddenimports=["ctranslate2", "faster_whisper", "requests"], hookspath=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Five Transcript", console=False, icon=str(icon) if icon.is_file() else None)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name="Five Transcript")
