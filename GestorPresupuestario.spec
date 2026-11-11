# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Root path for standalone application
app_dir = Path.cwd()

datas = [
    (str(app_dir / "data"), "data"),
]

hidden_imports = [
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "sqlalchemy",
    "sqlalchemy.sql.default_comparator",
    "passlib",
    "passlib.handlers.bcrypt",
    "bcrypt",
    "jose",
    "cryptography",
    "dateutil",
    "pydantic",
    "pydantic.deprecated",
    "pydantic.deprecated.decorator",
    "email_validator",
]
hidden_imports += collect_submodules("pydantic")
hidden_imports += collect_submodules("models")
hidden_imports += collect_submodules("services")
hidden_imports += collect_submodules("schemas")
hidden_imports += collect_submodules("core")
hidden_imports += collect_submodules("db")
hidden_imports += collect_submodules("ui")

a = Analysis(
    [str(app_dir / "main.py")],
    pathex=[str(app_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="GestorPresupuestario",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
