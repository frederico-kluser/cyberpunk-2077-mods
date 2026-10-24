<#
.SYNOPSIS
  Runs the Desert Eagle asset pipeline in Blender (headless) — all output stays
  in the worktree. Nothing is ever deployed to the game from here.

.DESCRIPTION
  Thin wrapper over src/blender/run_pipeline.py:
    1. checks the inputs (source model + Nue template GLB) exist;
    2. runs the Blender stages: import -> align -> rig -> lods -> export -> report;
    3. prints where the .glb, .blend and JSON report landed (assets/work).

.EXAMPLE
  pwsh -File scripts/run-asset-pipeline.ps1
  pwsh -File scripts/run-asset-pipeline.ps1 -Model assets/raw/desert_eagle_poly.glb
  pwsh -File scripts/run-asset-pipeline.ps1 -Stages rig,export
#>
[CmdletBinding()]
param(
  [string]$BlenderExe = 'C:\Users\kluse\Tools\Blender\5.2\blender.exe',
  [string]$Config = 'src\blender\configs\desert_eagle.json',
  [string]$Model,
  [string[]]$Stages = @('all')
)

$ErrorActionPreference = 'Stop'
$modRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $modRoot $Config

if (-not (Test-Path -LiteralPath $configPath)) {
  throw "Erro: config '$configPath' em falta — Solução: use src/blender/configs/desert_eagle.json."
}
if (-not (Test-Path -LiteralPath $BlenderExe)) {
  throw "Erro: Blender não encontrado em '$BlenderExe' — Solução: corra scripts/setup-toolchain.ps1."
}

# Optionally override the source model without editing the config.
if ($Model) {
  $cfg = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
  $cfg.source_model = $Model
  $tmpConfig = Join-Path ([System.IO.Path]::GetTempPath()) 'desert_eagle_run.json'
  $cfg | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $tmpConfig -Encoding UTF8
  $configPath = $tmpConfig
  Write-Host "Modelo fonte: $Model"
}

$stageArgs = @()
foreach ($stage in $Stages) { $stageArgs += @('--stage', $stage) }

Write-Host "== Pipeline Desert Eagle (tudo fica na worktree) =="
& $BlenderExe --background --python (Join-Path $modRoot 'src\blender\run_pipeline.py') -- `
    --config $configPath @stageArgs

if ($LASTEXITCODE -ne 0) {
  throw 'Erro: o pipeline falhou — Solução: veja as linhas STAGE ... FAIL acima.'
}

Write-Host ''
Write-Host '== Artefactos (na worktree, nada vai para o jogo) =='
$work = Join-Path $modRoot 'assets\work'
Get-ChildItem -LiteralPath $work -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Host ("  {0}  ({1:N0} bytes)" -f $_.Name, $_.Length)
}
