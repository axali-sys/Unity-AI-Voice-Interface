# PyInstaller spec for the controlled local research runner.
# Build from security-research/ with: pyinstaller XParallelResearch.spec

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('runner')

a = Analysis(
    ['runner/runner.py'],
    pathex=['.'],
    binaries=[],
    datas=[('config/scope.json', 'config')],
    hiddenimports=hiddenimports,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='XParallelResearch',
    debug=False,
    strip=False,
    upx=False,
    console=True,
)
