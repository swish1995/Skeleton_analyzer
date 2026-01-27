# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Skeleton Analyzer"""

import os
import sys

block_cipher = None

# MediaPipe 모델 파일 경로
model_path = os.path.join('src', 'core', 'pose_landmarker.task')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (model_path, 'src/core'),  # MediaPipe 모델 포함
    ],
    hiddenimports=[
        'mediapipe',
        'mediapipe.tasks',
        'mediapipe.tasks.python',
        'mediapipe.tasks.python.vision',
        'cv2',
        'numpy',
        'PyQt6',
    ],
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
    name='SkeletonAnalyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일 경로 (resources/icon.ico)
)

# macOS 앱 번들 (선택적)
app = BUNDLE(
    exe,
    name='SkeletonAnalyzer.app',
    icon=None,  # resources/icon.icns
    bundle_identifier='com.skeletonanalyzer.app',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
    },
)
