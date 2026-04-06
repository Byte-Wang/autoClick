# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# 获取cv2库的路径
import cv2
cv2_path = os.path.dirname(cv2.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 添加cv2相关文件
        (os.path.join(cv2_path, '*.pyd'), 'cv2'),
        (os.path.join(cv2_path, '*.dll'), 'cv2'),
        (os.path.join(cv2_path, 'config.py'), 'cv2'),
    ],
    hiddenimports=['cv2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['loader_dir_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='auto_tool_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='auto_tool_v2',
)
