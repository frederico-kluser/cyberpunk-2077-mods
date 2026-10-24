<#
.SYNOPSIS
  Installs (or verifies) the whole Desert Eagle toolchain on this machine.

.DESCRIPTION
  Everything installs WITHOUT admin rights into C:\Users\kluse\Tools (plus the
  game folder for the runtime frameworks). Idempotent: existing pieces are
  detected and skipped. Run it, then check the printed summary.

  Covered:
    - Blender (portable ZIP) + add-ons (Cyberpunk IO Suite, BlenderMCP, Rokoko)
    - uv/uvx + blender-mcp MCP server (cached for offline use)
    - WolvenKit App + CLI (+ local .NET 10 runtime)
    - RED4ext + ArchiveXL + TweakXL into the game folder

.EXAMPLE
  pwsh -File scripts/setup-toolchain.ps1
  pwsh -File scripts/setup-toolchain.ps1 -SkipDownloads   # verify only
#>
[CmdletBinding()]
param(
  [string]$ToolsRoot = 'C:\Users\kluse\Tools',
  [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
  [switch]$SkipDownloads
)

$ErrorActionPreference = 'Stop'
$blenderVersion = '5.2.3'
$blenderZipUrl = "https://download.blender.org/release/Blender5.2/blender-$blenderVersion-windows-x64.zip"
$blenderSha256 = '723F08A4401502561EB763CDEACF8745B31E5F3F154D287D3830D97CF75DC2FB'
$wolvenkitTag = '9.1.0'
$red4extTag = 'v1.30.0'
$archivexlTag = '1.27.5'
$tweakxlTag = '1.11.5'

$summary = New-Object System.Collections.Generic.List[string]

function Step {
  param([string]$Name, [string]$Status, [string]$Detail = '')
  $line = "[{0}] {1}" -f $Status, $Name
  if ($Detail) { $line += " — $Detail" }
  Write-Host $line
  $script:summary.Add($line) | Out-Null
}

function Get-File {
  param([string]$Url, [string]$OutFile, [string]$ExpectedSha256)
  if (Test-Path -LiteralPath $OutFile) {
    if ($ExpectedSha256) {
      $hash = (Get-FileHash -LiteralPath $OutFile -Algorithm SHA256).Hash.ToUpperInvariant()
      if ($hash -eq $ExpectedSha256.ToUpperInvariant()) { return $OutFile }
      Write-Host "  hash diferente, a voltar a transferir: $OutFile"
      Remove-Item -LiteralPath $OutFile -Force
    } else {
      return $OutFile
    }
  }
  if ($SkipDownloads) { throw "Erro: '$OutFile' em falta e -SkipDownloads ativo — Solução: corre sem -SkipDownloads." }
  New-Item -ItemType Directory -Force -Path (Split-Path $OutFile) | Out-Null
  Write-Host "  a transferir $Url"
  curl.exe -L --retry 3 -o $OutFile $Url
  if ($ExpectedSha256) {
    $hash = (Get-FileHash -LiteralPath $OutFile -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($hash -ne $ExpectedSha256.ToUpperInvariant()) {
      throw "Erro: SHA256 inesperado em $OutFile — Solução: apague o ficheiro e repita."
    }
  }
  return $OutFile
}

# ---------------------------------------------------------------------------
# 1. Blender (portable) + add-ons
# ---------------------------------------------------------------------------
$blenderDir = Join-Path $ToolsRoot 'Blender'
$blenderExe = Join-Path $blenderDir "5.2\blender.exe"
$blenderZip = Join-Path $blenderDir "downloads\blender-$blenderVersion-windows-x64.zip"

if (Test-Path -LiteralPath $blenderExe) {
  Step 'Blender' 'OK' $blenderExe
} else {
  Get-File -Url $blenderZipUrl -OutFile $blenderZip -ExpectedSha256 $blenderSha256 | Out-Null
  $target = Join-Path $blenderDir '5.2'
  New-Item -ItemType Directory -Force -Path $target | Out-Null
  tar -xf $blenderZip -C $target --strip-components=1
  Step 'Blender' 'INSTALADO' $blenderExe
}

$addonsDir = Join-Path $blenderDir 'addons'
New-Item -ItemType Directory -Force -Path $addonsDir | Out-Null

# Add-on do WolvenKit (Cyberpunk IO Suite) — asset do GitHub release.
$cpAddonZip = Join-Path $addonsDir 'Cyberpunk-Blender-add-on.zip'
if (Test-Path -LiteralPath $cpAddonZip) {
  Step 'Cyberpunk Blender Add-on (IO Suite)' 'OK' $cpAddonZip
} elseif (-not $SkipDownloads) {
  gh release download --repo WolvenKit/Cyberpunk-Blender-add-on --pattern '*.zip' --dir $addonsDir
  Step 'Cyberpunk Blender Add-on (IO Suite)' 'DESCARREGADO' $addonsDir
} else {
  Step 'Cyberpunk Blender Add-on (IO Suite)' 'FALTA' 'use sem -SkipDownloads'
}

# BlenderMCP add-on (single .py from the MCP repo).
$mcpAddon = Join-Path $addonsDir 'blendermcp_addon.py'
if (Test-Path -LiteralPath $mcpAddon) {
  Step 'BlenderMCP add-on' 'OK' $mcpAddon
} elseif (-not $SkipDownloads) {
  curl.exe -L -o $mcpAddon 'https://raw.githubusercontent.com/ahujasid/mcp-for-blender/main/addon.py'
  Step 'BlenderMCP add-on' 'DESCARREGADO' $mcpAddon
} else {
  Step 'BlenderMCP add-on' 'FALTA' 'use sem -SkipDownloads'
}

# Install/enabled add-ons inside Blender (no GUI clicking).
if (Test-Path -LiteralPath $blenderExe) {
  $enable = @(
    "import bpy,sys",
    "for m in sys.argv[sys.argv.index('--')+1:]:",
    "    try:",
    "        bpy.ops.preferences.addon_enable(module=m); print('ENABLED', m)",
    "    except Exception as e:",
    "        print('ENABLE_FAIL', m, e)",
    "bpy.ops.wm.save_userpref()",
    "print('ADDONS_DONE')"
  ) -join "`n"
  & $blenderExe --background --python-expr $enable -- 'io_scene_wolvenkit' 'blender_mcp' 'rokoko'
  Step 'add-ons ativados no Blender' 'OK' 'ver linhas ENABLED/ENABLE_FAIL acima'
}

# ---------------------------------------------------------------------------
# 2. uv/uvx + servidor blender-mcp
# ---------------------------------------------------------------------------
$uvx = Join-Path $env:APPDATA 'Python\Python312\Scripts\uvx.exe'
if (Test-Path -LiteralPath $uvx) {
  Step 'uv/uvx' 'OK' (& $uvx --version)
} else {
  python3 -m pip install --user uv
  Step 'uv/uvx' 'INSTALADO' (& $uvx --version)
}
if (-not $SkipDownloads) {
  & $uvx blender-mcp --help *> $null
  Step 'servidor blender-mcp (cache offline)' 'OK' 'uvx mcp-for-blender'
}

# ---------------------------------------------------------------------------
# 3. WolvenKit (App + CLI) + .NET runtime local
# ---------------------------------------------------------------------------
$wkitDir = Join-Path $ToolsRoot "WolvenKit\$wolvenkitTag"
$wkitCli = Join-Path $wkitDir 'wolvenkit-cli.cmd'
if (Test-Path -LiteralPath $wkitCli) {
  Step 'WolvenKit CLI' 'OK' (& $wkitCli --version)
} else {
  $wkitDownloads = Join-Path $wkitDir 'downloads'
  New-Item -ItemType Directory -Force -Path $wkitDownloads | Out-Null
  gh release download $wolvenkitTag --repo WolvenKit/WolvenKit --pattern 'WolvenKit-*.zip' --dir $wkitDownloads
  gh release download $wolvenkitTag --repo WolvenKit/WolvenKit --pattern 'WolvenKit.Console-*.zip' --dir $wkitDownloads
  tar -xf (Join-Path $wkitDownloads "WolvenKit-$wolvenkitTag.zip") -C (Join-Path $wkitDir 'WolvenKit.App')
  tar -xf (Join-Path $wkitDownloads "WolvenKit.Console-$wolvenkitTag.zip") -C (Join-Path $wkitDir 'WolvenKit.Console')
  Step 'WolvenKit App+CLI' 'DESCARREGADO' $wkitDir
}

$dotnet = Join-Path $ToolsRoot 'dotnet\dotnet.exe'
if (Test-Path -LiteralPath $dotnet) {
  Step '.NET runtime (user-local)' 'OK' $dotnet
} else {
  Step '.NET runtime (user-local)' 'FALTA' 'corra dotnet-install.ps1 para 10.0.x em C:\Users\kluse\Tools\dotnet'
}

# ---------------------------------------------------------------------------
# 4. RED4ext + ArchiveXL + TweakXL na pasta do jogo
# ---------------------------------------------------------------------------
if (-not (Test-Path -LiteralPath (Join-Path $GameDir 'bin\x64\Cyberpunk2077.exe'))) {
  throw "Erro: '$GameDir' não é o jogo — Solução: passe -GameDir."
}

function Install-GameZip {
  param([string]$Name, [string]$Repo, [string]$Tag, [string]$Pattern)
  $red = Join-Path $ToolsRoot "$Name\downloads"
  $marker = switch ($Name) {
    'RED4ext'  { Join-Path $GameDir 'red4ext\red4ext.dll' }
    'ArchiveXL'{ Join-Path $GameDir 'red4ext\plugins\ArchiveXL\ArchiveXL.dll' }
    'TweakXL'  { Join-Path $GameDir 'red4ext\plugins\TweakXL\TweakXL.dll' }
  }
  if (Test-Path -LiteralPath $marker) { Step $Name 'OK' $marker; return }
  if ($SkipDownloads) { Step $Name 'FALTA' 'use sem -SkipDownloads'; return }
  New-Item -ItemType Directory -Force -Path $red | Out-Null
  gh release download $Tag --repo $Repo --pattern $Pattern --dir $red
  $zip = Get-ChildItem -LiteralPath $red -Filter '*.zip' | Select-Object -First 1
  python3 -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" $zip.FullName $GameDir
  Step $Name 'INSTALADO' $marker
}

Install-GameZip -Name 'RED4ext' -Repo 'WopsS/RED4ext' -Tag $red4extTag -Pattern 'RED4ext-*.zip'
Install-GameZip -Name 'ArchiveXL' -Repo 'psiberx/cp2077-archive-xl' -Tag $archivexlTag -Pattern 'ArchiveXL-*.zip'
Install-GameZip -Name 'TweakXL' -Repo 'psiberx/cp2077-tweak-xl' -Tag $tweakxlTag -Pattern 'TweakXL-*.zip'

Write-Host ''
Write-Host '== Resumo da toolchain =='
$summary | ForEach-Object { Write-Host $_ }
