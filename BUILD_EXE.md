# Building PerformanceLens.exe for Windows

This guide explains how to build a standalone Windows executable (.exe) that users can run without installing Python or dependencies.

## Quick Setup

### 1. Install PyInstaller
```powershell
pip install pyinstaller
```

### 2. Build the exe
```powershell
# From the project root
pyinstaller build.spec
```

The exe will be created in:
```
dist/PerformanceLens.exe
```

### 3. Test the exe
```powershell
.\dist\PerformanceLens.exe
```

The app should launch with a native window and run on `http://127.0.0.1:5000`.

## How it works

- **Flask backend** runs inside the exe in a background thread
- **pywebview** with Qt opens a native Windows window
- **SQLite database** stores data in `performance.db` next to the exe by default (can be overridden with `PERFORMANCELENS_DB_PATH`)
- First run unpacks ~150–200MB to `%TEMP%` for speed; subsequent runs are faster

## Configuration for exe builds

Before building, set the Flask secret key:
```powershell
$env:PERFORMANCELENS_SECRET_KEY = "your-long-random-string-here"
pyinstaller build.spec
```

Or hardcode it in `desktop.py` line 27 (not recommended for shared builds):
```python
app.config['SECRET_KEY'] = 'hardcoded-key'
```

## Optional: Add an icon

Place an `icon.ico` file in the project root and rebuild:
```powershell
pyinstaller build.spec
```

## Optional: Create an installer (NSIS)

For professional distribution, wrap the exe in an NSIS installer:
1. Install NSIS: https://nsis.sourceforge.io/
2. Create `installer.nsi` with your branding
3. Run `makensis installer.nsi`

Example `installer.nsi` stub:
```nsis
!include "MUI2.nsh"
Name "PerformanceLens"
OutFile "PerformanceLens-Setup.exe"
InstallDir "$PROGRAMFILES\PerformanceLens"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\PerformanceLens.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\PerformanceLens.exe"
  RMDir "$INSTDIR"
SectionEnd
```

## Troubleshooting

- **"Failed to load main window"**: Missing Qt backend. Ensure `PyQt6` and `qtpy` are in `requirements.txt`.
- **Port 5000 already in use**: Edit `desktop.py` line 27 to use a different port.
- **Large .exe size**: Normal for PyInstaller + PyQt6; typical size is 150–250MB.
- **Antivirus warnings**: PyInstaller-built exes can trigger false positives. Whitelist or code-sign the exe.

## Database & backups

- **Default location**: `performance.db` next to the exe or in the repo root
- **Backup before updates**: Use Settings → Download backup
- **Custom location**: Set `PERFORMANCELENS_DB_PATH=C:\Users\YourName\AppData\Local\PerformanceLens\performance.db`

## Next steps

- Test the exe on a clean Windows machine before distributing
- Code-sign the exe for distribution (optional but recommended)
- Create a GitHub Release and upload the exe
