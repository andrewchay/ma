# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building MA Agent Windows executable."""
import sys
from pathlib import Path

block_cipher = None
base_path = Path(SPECPATH)

# Data files to bundle
# (source_path, dest_folder_in_bundle)
datas = [
    (str(base_path / '.env'), '.'),
    (str(base_path / 'web'), 'web'),
    (str(base_path / 'agent_core'), 'agent_core'),
    (str(base_path / 'tests'), 'tests'),
    (str(base_path / '.agent'), '.agent'),
]

# Bundle root-level docs/configs
for f in base_path.iterdir():
    if f.is_file() and f.suffix in {'.md', '.json', '.txt', '.sh', '.yaml', '.yml', '.example', '.py'}:
        datas.append((str(f), '.'))

a = Analysis(
    ['web_api.py'],
    pathex=[str(base_path)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'pydantic',
        'pydantic.deprecated.decorator',
        'pydantic.v1',
        'starlette',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'openai',
        'anthropic',
        'python-dotenv',
        'httpx',
        'httpx_sse',
        'tavily',
        'metaso_sdk',
        'anyio',
        'sniffio',
        'h11',
        'httpcore',
        'jiter',
        'tqdm',
        'distro',
        'typing_extensions',
        'annotated_types',
        'pydantic_core',
        'playwright.sync_api',
        'camoufox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'numpy.random._examples',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ma-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ma-agent',
)
