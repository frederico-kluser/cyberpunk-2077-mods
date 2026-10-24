@echo off
rem CP2077 CET gate - Steam shim. See cet-gate.ps1 for the full behaviour.
rem Steam launch options:  "C:\Users\kluse\Tools\cet-gate.bat" %command% -modded
rem The ps1 sits NEXT TO this bat (%~dp0), so the install folder can be anything.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0cet-gate.ps1" %*
