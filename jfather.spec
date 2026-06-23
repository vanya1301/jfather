# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the directory where this spec file is located
spec_dir = os.path.abspath(SPECPATH) if 'SPECPATH' in dir() else os.path.dirname(os.path.abspath(__file__))

# Collect PySide6 data files and submodules
pyside6_data = collect_data_files('PySide6', include_py_files=False)
pyside6_submodules = collect_submodules('PySide6')

# Collect application icon resources
icon_datas = []
resources_dir = os.path.join(spec_dir, 'jfather', 'resources')
if os.path.exists(resources_dir):
    for icon_file in os.listdir(resources_dir):
        if icon_file.endswith('.png'):
            icon_datas.append((os.path.join(resources_dir, icon_file), os.path.join('jfather', 'resources')))


def _build_icns():
    """Build a proper .icns from the icon.iconset dir (macOS only). Returns path or None."""
    if sys.platform != 'darwin':
        return None
    iconset = os.path.join(resources_dir, 'icon.iconset')
    icns_path = os.path.join(resources_dir, 'jfather.icns')
    if os.path.exists(icns_path):
        return icns_path
    if os.path.isdir(iconset):
        import subprocess
        try:
            subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', icns_path], check=True)
            return icns_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    # Fallback: raw PNG
    png = os.path.join(resources_dir, 'icon-512.png')
    return png if os.path.exists(png) else None


# Code signing identity / entitlements pulled from env (set by CI). Empty -> None.
_sign_identity = os.environ.get('PYINSTALLER_CODESIGN_IDENTITY') or None
_entitlements = os.environ.get('PYINSTALLER_ENTITLEMENTS') or None
if _entitlements and not os.path.exists(_entitlements):
    _entitlements = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include any data files your app needs
    ] + pyside6_data + icon_datas,
    hiddenimports=[
        'collection_query',
        'collection_query.lookups',
    ] + pyside6_submodules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='jfather',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed mode for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=_sign_identity,
    entitlements_file=_entitlements,
)

# macOS specific: create universal binary and app bundle
if sys.platform == 'darwin':
    icon_file = _build_icns()

    app = BUNDLE(
        exe,
        name='jfather.app',
        icon=icon_file,
        bundle_identifier='com.jfather.app',
        info_plist={
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'CFBundleShortVersionString': '0.1.0',
            'CFBundleVersion': '0.1.0',
        },
    )
