<#
.SYNOPSIS
  Copies a mod's Redscript sources into the local Cyberpunk 2077 installation.

.EXAMPLE
  pwsh -File tools/deploy.ps1
  pwsh -File tools/deploy.ps1 -ModId LethalHeadshots -Launch
  pwsh -File tools/deploy.ps1 -GameDir "D:\Games\Cyberpunk 2077"
#>
[CmdletBinding()]
param(
  [string]$ModId = 'LethalHeadshots',
  [string]$GameDir,
  [switch]$Launch
)

. "$PSScriptRoot\common.ps1"

$game = Find-CyberpunkGameDir -Path $GameDir
Write-Host "Jogo: $game"

$modDir = Get-ModDir -Id $ModId
$manifest = Read-ModManifest -ModDir $modDir

$sourceDir = Join-Path $modDir 'src\reds'
$targetDir = Join-Path $game "r6\scripts\$($manifest.id)"
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$copied = 0
foreach ($file in (Get-ChildItem -LiteralPath $sourceDir -Filter '*.reds' -File)) {
  Copy-Item -LiteralPath $file.FullName -Destination $targetDir -Force
  Write-Host "  -> $($file.Name)"
  $copied++
}

# Mods may also ship a CET/Lua side (diagnostics): deploy it to the CET mods
# folder when present.
$luaDir = Join-Path $modDir 'src\lua'
if (Test-Path -LiteralPath $luaDir) {
  $cetDir = Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'
  $luaTarget = Join-Path $cetDir $manifest.id
  New-Item -ItemType Directory -Force -Path $luaTarget | Out-Null
  foreach ($file in (Get-ChildItem -LiteralPath $luaDir -Filter '*.lua' -File)) {
    Copy-Item -LiteralPath $file.FullName -Destination $luaTarget -Force
    Write-Host "  -> lua:$($file.Name) => $luaTarget"
    $copied++
  }
}

Write-Host "$copied ficheiro(s) instalados em $targetDir"

if (-not (Test-Path -LiteralPath (Join-Path $game 'engine\tools\scc.exe'))) {
  Write-Warning 'redscript (engine\tools\scc.exe) não foi encontrado. Instale o redscript antes de arrancar o jogo.'
}
if (-not (Test-Path -LiteralPath (Join-Path $game 'r6\scripts'))) {
  New-Item -ItemType Directory -Force -Path (Join-Path $game 'r6\scripts') | Out-Null
}

if ($Launch) {
  $exe = Join-Path $game 'bin\x64\Cyberpunk2077.exe'
  Write-Host "A iniciar $exe"
  Start-Process -FilePath $exe
}
