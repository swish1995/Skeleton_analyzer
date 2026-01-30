# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Skeleton Analyzer"""

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# MediaPipe 모델 파일 경로
model_path = os.path.join('src', 'core', 'pose_landmarker.task')

# MediaPipe 전체 수집
mediapipe_datas, mediapipe_binaries, mediapipe_hiddenimports = collect_all('mediapipe')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=mediapipe_binaries,
    datas=[
        (model_path, 'src/core'),  # MediaPipe 모델 포함
        ('resources/icon.ico', 'resources'),  # Windows 아이콘
        ('resources/icon.icns', 'resources'),  # macOS 아이콘
        ('src/resources/help', 'help'),  # 도움말 파일
        ('src/resources/icons', 'icons'),  # 아이콘 파일 (있는 경우)
    ] + mediapipe_datas,
    hiddenimports=[
        'mediapipe',
        'mediapipe.tasks',
        'mediapipe.tasks.python',
        'mediapipe.tasks.python.vision',
        'mediapipe.tasks.python.core',
        'mediapipe.tasks.c',
        'cv2',
        'numpy',
        'PyQt6',
    ] + mediapipe_hiddenimports,
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

# onedir 모드: EXE는 스크립트만 포함
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
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
    icon='resources/icon.ico',  # Windows 아이콘
)

# onedir 모드: COLLECT로 모든 파일 수집
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SkeletonAnalyzer',
)

# macOS 앱 번들
app = BUNDLE(
    coll,
    name='SkeletonAnalyzer.app',
    icon='resources/icon.icns',  # macOS 아이콘
    bundle_identifier='com.skeletonanalyzer.app',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'Skeleton Analyzer',
        'CFBundleDisplayName': 'Skeleton Analyzer',
    },
)
