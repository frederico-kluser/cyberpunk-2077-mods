@echo off
rem CP2077 CET gate — Steam shim. See cet-gate.ps1 for the full behaviour.
rem Steam launch options:  "C:\Users\kluse\Tools\cp2077-cet-gate.bat" %command% -modded
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\kluse\Tools\cp2077-cet-gate.ps1" %*
