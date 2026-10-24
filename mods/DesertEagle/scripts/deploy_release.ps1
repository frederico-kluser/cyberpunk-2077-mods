<#
.SYNOPSIS
  Installs the packed Desert Eagle release into the game — ONLY when the owner
  explicitly authorizes it.

.DESCRIPTION
  OWNER CONSTRAINT (still in force): nothing is deployed to the game without
  explicit authorization. This script refuses to run unless
  -IAuthorizeTheGameInstall is passed AND the owner has said so in the session.

  Copies:
    release\desert_eagle.archive      -> <game>\archive\pc\mod\
    release\desert_eagle.archive.xl   -> <game>\archive\pc\mod\
    release\desert_eagle.yaml         -> <game>\r6\tweaks\

.EXAMPLE
  pwsh -File scripts/deploy_release.ps1 -IAuthorizeTheGameInstall
#>
[CmdletBinding()]
param(
  [switch]$IAuthorizeTheGameInstall,
  [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
  [string]$ReleaseDir
)

$ErrorActionPreference = 'Stop'
$modRoot = Split-Path -Parent $PSScriptRoot
if (-not $ReleaseDir) { $ReleaseDir = Join-Path $modRoot 'assets\work\release' }

if (-not $IAuthorizeTheGameInstall) {
  throw 'Erro: deploy bloqueado — a restrição do dono proíbe injetar no jogo sem autorização explícita. Solução: correr com -IAuthorizeTheGameInstall APÓS o dono autorizar.'
}

if (-not (Test-Path (Join-Path $GameDir 'bin\x64\Cyberpunk2077.exe'))) {
  throw "Erro: '$GameDir' não é uma instalação do Cyberpunk 2077 — Solução: indicar -GameDir."
}

$archive = Join-Path $ReleaseDir 'desert_eagle.archive'
$xl      = Join-Path $ReleaseDir 'desert_eagle.archive.xl'
$yaml    = Join-Path $ReleaseDir 'desert_eagle.yaml'
foreach ($f in @($archive, $xl, $yaml)) {
  if (-not (Test-Path $f)) { throw "Erro: '$f' em falta — Solução: correr scripts/pack_archive.ps1." }
}

$modDir = Join-Path $GameDir 'archive\pc\mod'
$tweaks = Join-Path $GameDir 'r6\tweaks'
New-Item -ItemType Directory -Force -Path $modDir, $tweaks | Out-Null

Copy-Item $archive (Join-Path $modDir 'desert_eagle.archive') -Force
Copy-Item $xl      (Join-Path $modDir 'desert_eagle.archive.xl') -Force
Copy-Item $yaml    (Join-Path $tweaks 'desert_eagle.yaml') -Force

Write-Host '== Deploy efetuado =='
Get-ChildItem $modDir -Filter 'desert_eagle*' | ForEach-Object { Write-Host ("  {0}  {1:N0} B" -f $_.FullName, $_.Length) }
Get-ChildItem $tweaks -Filter 'desert_eagle*' | ForEach-Object { Write-Host ("  {0}  {1:N0} B" -f $_.FullName, $_.Length) }
Write-Host ''
Write-Host 'Teste em jogo: Game.AddToInventory("Items.DesertEagle", 1)'
Write-Host 'Logs: red4ext\plugins\ArchiveXL\ArchiveXL.log · red4ext\plugins\TweakXL\TweakXL.log'
Write-Host 'DEPLOY_DONE'
