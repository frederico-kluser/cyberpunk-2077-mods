# Shared helpers for the build/deploy/validate scripts.
# Dot-source this file: . "$PSScriptRoot\common.ps1"

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}

function Get-ModsRoot {
  return (Join-Path (Get-RepoRoot) 'mods')
}

function Read-ModManifest {
  param([Parameter(Mandatory)][string]$ModDir)

  $manifestPath = Join-Path $ModDir 'mod.json'
  if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Erro: mod.json em falta em '$ModDir' — Solução: todo o mod precisa de um manifest mod.json."
  }

  return Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
}

function Get-ModDir {
  param([Parameter(Mandatory)][string]$Id)

  $dir = Join-Path (Get-ModsRoot) $Id
  if (-not (Test-Path -LiteralPath $dir)) {
    throw "Erro: mod '$Id' não existe — Solução: veja a pasta mods/."
  }

  return (Resolve-Path $dir).Path
}

function Test-CyberpunkGameDir {
  param([string]$Path)

  if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
  return (Test-Path -LiteralPath (Join-Path $Path 'bin\x64\Cyberpunk2077.exe'))
}

function Get-SteamLibraryPaths {
  $paths = New-Object System.Collections.Generic.List[string]

  $steamPath = $null
  try {
    $steamPath = (Get-ItemProperty -Path 'HKCU:\Software\Valve\Steam' -ErrorAction Stop).SteamPath
  } catch {
    $steamPath = $null
  }
  if ([string]::IsNullOrWhiteSpace($steamPath)) { return $paths }

  $paths.Add($steamPath)

  $vdf = Join-Path $steamPath 'steamapps\libraryfolders.vdf'
  if (Test-Path -LiteralPath $vdf) {
    $content = Get-Content -LiteralPath $vdf -Raw
    foreach ($match in [regex]::Matches($content, '"path"\s+"(?<path>[^"]+)"')) {
      $lib = $match.Groups['path'].Value -replace '\\\\', '\'
      if ($paths -notcontains $lib) { $paths.Add($lib) }
    }
  }

  return $paths
}

<#
.SYNOPSIS
  Finds the Cyberpunk 2077 installation directory.

.DESCRIPTION
  Resolution order: explicit -Path, $env:CYBERPUNK_GAME_DIR, Steam libraries
  (registry + libraryfolders.vdf), then common GOG/Epic locations.
#>
function Find-CyberpunkGameDir {
  param([string]$Path)

  if (-not [string]::IsNullOrWhiteSpace($Path)) {
    if (Test-CyberpunkGameDir $Path) { return (Resolve-Path $Path).Path }
    throw "Erro: '$Path' não parece uma instalação de Cyberpunk 2077 (falta bin\x64\Cyberpunk2077.exe) — Solução: indique a raiz do jogo em -GameDir."
  }

  if (-not [string]::IsNullOrWhiteSpace($env:CYBERPUNK_GAME_DIR)) {
    if (Test-CyberpunkGameDir $env:CYBERPUNK_GAME_DIR) { return (Resolve-Path $env:CYBERPUNK_GAME_DIR).Path }
  }

  foreach ($lib in Get-SteamLibraryPaths) {
    $candidate = Join-Path $lib 'steamapps\common\Cyberpunk 2077'
    if (Test-CyberpunkGameDir $candidate) { return (Resolve-Path $candidate).Path }
  }

  $fallbacks = @(
    'C:\GOG Games\Cyberpunk 2077',
    'C:\Program Files\Epic Games\Cyberpunk2077',
    'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
  )
  foreach ($candidate in $fallbacks) {
    if (Test-CyberpunkGameDir $candidate) { return (Resolve-Path $candidate).Path }
  }

  throw 'Erro: não encontrei o Cyberpunk 2077 — Solução: defina CYBERPUNK_GAME_DIR ou passe -GameDir "C:\...\Cyberpunk 2077".'
}

function Get-RedscriptCli {
  param(
    [switch]$Download,
    [string]$CacheDir = (Join-Path (Get-RepoRoot) '.cache\redscript')
  )

  $exe = Join-Path $CacheDir 'redscript-cli.exe'
  if (Test-Path -LiteralPath $exe) { return $exe }
  if (-not $Download) { return $null }

  New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null
  $url = 'https://github.com/jac3km4/redscript/releases/latest/download/redscript-cli.exe'
  Write-Host "A transferir redscript-cli.exe de $url"
  Invoke-WebRequest -Uri $url -OutFile $exe -UseBasicParsing
  if (-not (Test-Path -LiteralPath $exe)) {
    throw 'Erro: falha ao transferir o redscript-cli.exe — Solução: descarregue manualmente de https://github.com/jac3km4/redscript/releases.'
  }
  return $exe
}

function Get-FileSha256 {
  param([Parameter(Mandatory)][string]$Path)
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
