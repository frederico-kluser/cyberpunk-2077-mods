<#
.SYNOPSIS
  Assembles and packs the Desert Eagle .archive from the compiled artifacts.

.DESCRIPTION
  Everything stays in the project (owner constraint: nothing is deployed to the
  game). The staging mirrors the depot paths referenced by our .app/.ent/factory:

    desert_eagle\items\w_handgun_desert_eagle.mesh
    desert_eagle\items\desert_eagle.app
    desert_eagle\items\desert_eagle.ent
    desert_eagle\factories\weapons.csv
    desert_eagle\localization\en-us.json / pt-br.json

  and packs it with `wolvenkit-cli pack`. The ArchiveXL loader
  (desert_eagle.archive.xl) is emitted NEXT TO the archive, as the game expects.

.EXAMPLE
  pwsh -File scripts/pack_archive.ps1
#>
[CmdletBinding()]
param(
  [string]$WolvenKitCli = 'C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd',
  [string]$WorkDir,
  [string]$OutDir
)

$ErrorActionPreference = 'Stop'
$modRoot = Split-Path -Parent $PSScriptRoot
if (-not $WorkDir) { $WorkDir = Join-Path $modRoot 'assets\work' }
if (-not $OutDir)  { $OutDir  = Join-Path $WorkDir 'release' }

$staging = Join-Path $WorkDir 'archive_staging'
$deApp   = Join-Path $WorkDir 'de_app\bin'
$meshBin = Join-Path $WorkDir 'mesh_test\bin'
$factory = Join-Path $WorkDir 'cr2w_test\bin'

Write-Host '== 1. Staging layout =='
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
foreach ($d in @('items', 'items\textures', 'factories', 'localization')) {
  New-Item -ItemType Directory -Force -Path (Join-Path $staging "desert_eagle\$d") | Out-Null
}

Copy-Item (Join-Path $meshBin 'desert_eagle.mesh') (Join-Path $staging 'desert_eagle\items\w_handgun_desert_eagle.mesh') -Force
Copy-Item (Join-Path $deApp 'desert_eagle.app')   (Join-Path $staging 'desert_eagle\items\desert_eagle.app') -Force
Copy-Item (Join-Path $deApp 'desert_eagle.ent')   (Join-Path $staging 'desert_eagle\items\desert_eagle.ent') -Force
Copy-Item (Join-Path $factory 'weapons.csv')      (Join-Path $staging 'desert_eagle\factories\weapons.csv') -Force

# textures built by src/blender/export_xbm.py (referenced by the mesh material)
$xbmBin = Join-Path $WorkDir 'xbms\bin'
foreach ($t in @('desert_eagle_bc.xbm', 'desert_eagle_n.xbm')) {
  $src = Join-Path $xbmBin $t
  if (Test-Path $src) {
    Copy-Item $src (Join-Path $staging "desert_eagle\items\textures\$t") -Force
  } else {
    Write-Host "  [AVISO] textura '$t' em falta ($src) — o material vai referenciar um caminho ausente."
  }
}
Write-Host '  items/factories/textures copied'

Write-Host '== 2. Localizations (JSON -> CR2W) =='
$locSrc = Join-Path $modRoot 'src\archivexl\localization'
foreach ($lang in @('en-us', 'pt-br')) {
  # the deserializer derives the output name from the input name, so the JSON
  # dump must be named exactly <target>.json.json
  $tmpDir = Join-Path $env:TEMP "de_loc_$lang"
  New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
  $tmp = Join-Path $tmpDir "$lang.json.json"
  Copy-Item (Join-Path $locSrc "$lang.json") $tmp -Force
  $outLog = & $WolvenKitCli convert deserialize $tmp -o (Join-Path $staging 'desert_eagle\localization') -v Detailed 2>&1
  $built = Join-Path $staging "desert_eagle\localization\$lang.json"
  if (-not (Test-Path $built)) {
    $outLog | Select-String 'Error|Exception' | Select-Object -First 3 | ForEach-Object { Write-Host $_.Line }
    throw "Erro: localização '$lang' não compilou — Solução: verifique o JSON de origem."
  }
  Write-Host "  $lang.json -> CR2W ok"
}

Write-Host '== 3. Pack =='
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
& $WolvenKitCli pack $staging -o $OutDir -v Normal 2>&1 | Select-Object -Last 3

$archive = Get-ChildItem $OutDir -Filter '*.archive' | Select-Object -First 1
if (-not $archive) { throw 'Erro: pack não produziu .archive — Solução: verifique a saída do wolvenkit-cli.' }

# the packer names the archive after the staging folder — use the final name
$finalArchive = Join-Path $OutDir 'desert_eagle.archive'
if ($archive.FullName -ne $finalArchive) {
  Move-Item $archive.FullName $finalArchive -Force
  $archive = Get-Item $finalArchive
}

# ArchiveXL loader goes NEXT TO the archive
Copy-Item (Join-Path $modRoot 'src\archivexl\desert_eagle.archive.xl') (Join-Path $OutDir 'desert_eagle.archive.xl') -Force
Copy-Item (Join-Path $modRoot 'src\tweakxl\desert_eagle.yaml') (Join-Path $OutDir 'desert_eagle.yaml') -Force

Write-Host '== 4. Verify =='
& $WolvenKitCli archive $archive.FullName -l -v Minimal 2>&1 | Select-Object -Last 12
Write-Host ''
Write-Host ("archive: {0}  ({1:N0} bytes)" -f $archive.FullName, $archive.Length)
Get-ChildItem $OutDir | ForEach-Object { Write-Host ("  {0}  {1:N0} B" -f $_.Name, $_.Length) }
Write-Host 'PACK_DONE'
