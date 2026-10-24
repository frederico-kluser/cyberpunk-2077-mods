<#
.SYNOPSIS
  Installs the packed Desert Eagle release into the game — ONLY when the owner
  explicitly authorizes it.

.DESCRIPTION
  OWNER CONSTRAINT (still in force): nothing is deployed to the game without
  explicit authorization. This script refuses to run unless
  -IAuthorizeTheGameInstall is passed AND the owner has said so in the session.

  -Preview lists exactly what would be installed where WITHOUT writing
  anything (no authorization needed — it touches nothing).

  Installs:
    release\desert_eagle.archive      -> <game>\archive\pc\mod\
    release\desert_eagle.archive.xl   -> <game>\archive\pc\mod\
    release\desert_eagle.yaml         -> <game>\r6\tweaks\
    src\reds\*.reds                   -> <game>\r6\scripts\DesertEagle\

.EXAMPLE
  pwsh -File scripts/deploy_release.ps1 -Preview
  pwsh -File scripts/deploy_release.ps1 -IAuthorizeTheGameInstall
#>
[CmdletBinding()]
param(
  [switch]$IAuthorizeTheGameInstall,
  [switch]$Preview,
  [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
  [string]$ReleaseDir
)

$ErrorActionPreference = 'Stop'
$modRoot = Split-Path -Parent $PSScriptRoot
if (-not $ReleaseDir) { $ReleaseDir = Join-Path $modRoot 'assets\work\release' }

if (-not $IAuthorizeTheGameInstall -and -not $Preview) {
  throw 'Erro: deploy bloqueado — a restrição do dono proíbe injetar no jogo sem autorização explícita. Solução: correr com -IAuthorizeTheGameInstall APÓS o dono autorizar (ou -Preview para ver o plano sem instalar).'
}

$archive = Join-Path $ReleaseDir 'desert_eagle.archive'
$xl      = Join-Path $ReleaseDir 'desert_eagle.archive.xl'
$yaml    = Join-Path $ReleaseDir 'desert_eagle.yaml'
$redsDir = Join-Path $modRoot 'src\reds'

$plan = @(
  @{ From = $archive; To = (Join-Path $GameDir 'archive\pc\mod\desert_eagle.archive') },
  @{ From = $xl;      To = (Join-Path $GameDir 'archive\pc\mod\desert_eagle.archive.xl') },
  @{ From = $yaml;    To = (Join-Path $GameDir 'r6\tweaks\desert_eagle.yaml') }
)
foreach ($r in Get-ChildItem $redsDir -Filter '*.reds' -File -ErrorAction SilentlyContinue) {
  $plan += @{ From = $r.FullName; To = (Join-Path $GameDir "r6\scripts\DesertEagle\$($r.Name)") }
}

foreach ($p in $plan) {
  if (-not (Test-Path $p.From)) { throw "Erro: '$($p.From)' em falta — Solução: correr scripts/build_release.ps1." }
}

if ($Preview) {
  Write-Host '== PREVIEW (nada é instalado) =='
  foreach ($p in $plan) {
    $size = (Get-Item $p.From).Length
    Write-Host ("  {0,-64} -> {1}  ({2:N0} B)" -f (Split-Path $p.From -Leaf), $p.To, $size)
  }
  Write-Host ''
  Write-Host 'Para instalar: pwsh -File scripts/deploy_release.ps1 -IAuthorizeTheGameInstall'
  Write-Host 'DEPLOY_PREVIEW_OK'
  return
}

if (-not (Test-Path (Join-Path $GameDir 'bin\x64\Cyberpunk2077.exe'))) {
  throw "Erro: '$GameDir' não é uma instalação do Cyberpunk 2077 — Solução: indicar -GameDir."
}

foreach ($p in $plan) {
  $destDir = Split-Path $p.To -Parent
  New-Item -ItemType Directory -Force -Path $destDir | Out-Null
  Copy-Item $p.From $p.To -Force
}

Write-Host '== Deploy efetuado =='
foreach ($p in $plan) {
  Write-Host ("  {0}  {1:N0} B" -f $p.To, (Get-Item $p.To).Length)
}
Write-Host ''
Write-Host 'Teste em jogo: Game.AddToInventory("Items.DesertEagle", 1)'
Write-Host 'Logs: red4ext\plugins\ArchiveXL\ArchiveXL.log · red4ext\plugins\TweakXL\TweakXL.log'
Write-Host 'DEPLOY_DONE'
