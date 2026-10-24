<#
.SYNOPSIS
  Builds the ENTIRE Desert Eagle mod release with one command.

.DESCRIPTION
  Rebuilds every artifact from source (no manual steps, nothing deployed to
  the game):

    1. geometry   Blender: CS2 model -> de_geometry.json (retarget + fit + skin)
    2. material   patch the Nue template's material to our metal_base instance
    3. mesh       pack geometry into the .mesh buffer -> CR2W
    4. app/ent    transform the Nue app/ent -> CR2W
    5. textures   Blender: CS2 maps -> .xbm (RGBA + BC5) -> CR2W
    6. factory    entity factory -> CR2W
    7. pack       wolvenkit-cli pack -> desert_eagle.archive + .xl + yaml
    8. verify     scripts/verify_release.py (RELEASE_VERIFY_OK required)

.EXAMPLE
  pwsh -File scripts/build_release.ps1
#>
[CmdletBinding()]
param(
  [string]$BlenderExe = 'C:\Users\kluse\Tools\Blender\5.2\blender.exe',
  [string]$WolvenKitCli = 'C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd',
  [switch]$SkipVerify
)

$ErrorActionPreference = 'Stop'
$modRoot = Split-Path -Parent $PSScriptRoot
$work = Join-Path $modRoot 'assets\work'
$inv = Join-Path $modRoot 'assets\_inventory'
$scripts = Join-Path $modRoot 'scripts'

function Step($msg) { Write-Host "`n== $msg ==" -ForegroundColor Cyan }
function Fail($msg) { throw "Erro: $msg — Solução: ver a saída acima." }

function Invoke-Tool([string]$exe, [string[]]$argv, [string]$marker = '') {
  $out = & $exe @argv 2>&1 | ForEach-Object { Write-Host "  $_"; "$_" }
  if ($LASTEXITCODE -ne 0) { Fail "comando falhou: $exe $($argv -join ' ')" }
  # Blender exits 0 even when the python stage raised — require the marker
  if ($marker -and -not ($out -match $marker)) {
    Fail "etapa nao produziu '$marker' (script falhou em silencio?)"
  }
}

$py = Join-Path (Split-Path $BlenderExe) '5.2\python\bin\python.exe'
if (-not (Test-Path $py)) { $py = 'python3' }

# ---------------------------------------------------------------- 1. geometry
Step '1/8 geometria (Blender: CS2 -> geometry.json)'
$geo = Join-Path $work 'de_geometry.json'
Invoke-Tool $BlenderExe @(
  '--background', '--python', (Join-Path $modRoot 'src\blender\export_geometry.py'), '--',
  (Join-Path $inv 'mesh_json\w_handgun__tsunami_nue__base1_01.mesh.json'), $geo
) 'GEOM_OK'
if (-not (Test-Path $geo)) { Fail 'geometry.json não foi gerado.' }

# ---------------------------------------------------------------- 2. material
Step '2/8 material (metal_base + texturas CS2)'
$templateMat = Join-Path $work 'mesh_test\template_mat.mesh.json'
New-Item -ItemType Directory -Force -Path (Split-Path $templateMat) | Out-Null
Invoke-Tool $py @(
  (Join-Path $scripts 'build_materials.py'),
  (Join-Path $inv 'mesh_json\w_handgun__tsunami_nue__base1_01.mesh.json'),
  $templateMat
)

# ---------------------------------------------------------------- 3. mesh
Step '3/8 mesh (buffer de geometria -> CR2W)'
$meshJson = Join-Path $work 'mesh_test\desert_eagle.mesh.json'
Invoke-Tool $py @((Join-Path $scripts 'mesh_write.py'), $templateMat, $geo, $meshJson)
$meshBin = Join-Path $work 'mesh_test\bin'
New-Item -ItemType Directory -Force -Path $meshBin | Out-Null
Invoke-Tool $WolvenKitCli @('convert', 'deserialize', $meshJson, '-o', $meshBin, '-v', 'Minimal')

# ---------------------------------------------------------------- 4. app/ent
Step '4/8 app/ent (transformador da Nue)'
$deApp = Join-Path $work 'de_app'
Invoke-Tool $py @(
  (Join-Path $scripts 'build_app_json.py'),
  (Join-Path $inv 'app_json\w_handgun__tsunami_nue.app.json'),
  (Join-Path $inv 'app_json\w_handgun__tsunami_nue__base1_01.ent.json'),
  $deApp
)
$deAppBin = Join-Path $deApp 'bin'
New-Item -ItemType Directory -Force -Path $deAppBin | Out-Null
foreach ($f in @('desert_eagle.app.json', 'desert_eagle.ent.json')) {
  Invoke-Tool $WolvenKitCli @('convert', 'deserialize', (Join-Path $deApp $f), '-o', $deAppBin, '-v', 'Minimal')
}

# ---------------------------------------------------------------- 5. textures
Step '5/8 texturas (Blender: CS2 maps -> xbm)'
$tex = Join-Path $work 'cs2_textures'
$xbmBin = Join-Path $work 'xbms\bin'
New-Item -ItemType Directory -Force -Path $xbmBin | Out-Null
Invoke-Tool $BlenderExe @(
  '--background', '--python', (Join-Path $modRoot 'src\blender\export_xbm.py'), '--',
  (Join-Path $work 'xbms'),
  "color:$tex\texture_00.png", (Join-Path $inv 'xbm_json\w_tsunami_decal_01_d01.xbm.json'), 'desert_eagle_bc', '1024',
  "normal:$tex\texture_01.png", (Join-Path $inv 'xbm_json\w_handgun__tsunami_nue__base1_01_n01.xbm.json'), 'desert_eagle_n', '1024'
) 'XBM_DONE'
foreach ($t in @('desert_eagle_bc.xbm.json', 'desert_eagle_n.xbm.json')) {
  Invoke-Tool $WolvenKitCli @('convert', 'deserialize', (Join-Path $work "xbms\$t"), '-o', $xbmBin, '-v', 'Minimal')
}

# ------------------------------------------------------------- 5b. animations
Step '5b/8 animacoes (CS2 .re -> .anims -> CR2W)'
$animsBin = Join-Path $work 'anims_final\bin'
New-Item -ItemType Directory -Force -Path $animsBin | Out-Null
Invoke-Tool $py @(
  (Join-Path $scripts 're_to_anims.py'), '--',
  (Join-Path $work 're'),
  (Join-Path $inv 'anims_json'),
  (Join-Path $work 'anims_final')
)
foreach ($t in @('w_handgun__tsunami_nue__base1.anims.json', 'w_handgun__tsunami_nue__mag_std.anims.json')) {
  Invoke-Tool $WolvenKitCli @('convert', 'deserialize', (Join-Path $work "anims_final\$t"), '-o', $animsBin, '-v', 'Minimal')
}

# ---------------------------------------------------------------- 6. factory
Step '6/8 factory (entity factory -> CR2W)'
$facTmp = Join-Path $env:TEMP 'de_factory'
New-Item -ItemType Directory -Force -Path $facTmp | Out-Null
Copy-Item (Join-Path $modRoot 'src\archivexl\factories\weapons.csv') (Join-Path $facTmp 'weapons.csv.json') -Force
$facBin = Join-Path $work 'cr2w_test\bin'
New-Item -ItemType Directory -Force -Path $facBin | Out-Null
Invoke-Tool $WolvenKitCli @('convert', 'deserialize', (Join-Path $facTmp 'weapons.csv.json'), '-o', $facBin, '-v', 'Minimal')

# ---------------------------------------------------------------- 7. pack
Step '7/8 pack (desert_eagle.archive + .xl + yaml)'
Invoke-Tool 'pwsh' @('-File', (Join-Path $scripts 'pack_archive.ps1'))

# ---------------------------------------------------------------- 8. verify
if (-not $SkipVerify) {
  Step '8/8 verify (verificação integral do pacote)'
  & $py (Join-Path $scripts 'verify_release.py') 2>&1 | ForEach-Object { Write-Host "  $_" }
  if ($LASTEXITCODE -ne 0) { Fail 'verify_release.py encontrou problemas.' }
}

Write-Host "`nBUILD_RELEASE_OK" -ForegroundColor Green
Get-ChildItem (Join-Path $work 'release') -File | ForEach-Object {
  Write-Host ("  {0}  {1:N0} B" -f $_.Name, $_.Length)
}
