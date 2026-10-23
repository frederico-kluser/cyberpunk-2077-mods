<#
.SYNOPSIS
  Builds redistributable zips for every mod in mods/.

.DESCRIPTION
  The zip is laid out as the game expects it: extract it into the Cyberpunk
  2077 root and the scripts land in r6/scripts/<ModId>/.

.EXAMPLE
  pwsh -File tools/build.ps1
  pwsh -File tools/build.ps1 -OutputDir C:\Temp\dist -SkipValidation
#>
[CmdletBinding()]
param(
  [string]$OutputDir,
  [switch]$SkipValidation
)

. "$PSScriptRoot\common.ps1"

$repoRoot = Get-RepoRoot
if ([string]::IsNullOrWhiteSpace($OutputDir)) { $OutputDir = Join-Path $repoRoot 'dist' }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$OutputDir = (Resolve-Path $OutputDir).Path

if (-not $SkipValidation) {
  Write-Host '== Validação =='
  & (Join-Path $PSScriptRoot 'validate.ps1') -Static
  if ($LASTEXITCODE -ne 0) {
    throw 'Erro: a validação falhou — Solução: corrija os problemas acima antes de empacotar.'
  }
}

$stagingRoot = Join-Path $OutputDir '_staging'
if (Test-Path -LiteralPath $stagingRoot) { Remove-Item -LiteralPath $stagingRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

$artifacts = New-Object System.Collections.Generic.List[object]

foreach ($modDir in (Get-ChildItem -LiteralPath (Get-ModsRoot) -Directory)) {
  $manifestPath = Join-Path $modDir.FullName 'mod.json'
  if (-not (Test-Path -LiteralPath $manifestPath)) { continue }

  $manifest = Read-ModManifest -ModDir $modDir.FullName
  $name = "$($manifest.id)-$($manifest.version)"

  Write-Host "== Empacotar $($manifest.name) v$($manifest.version) =="

  $stage = Join-Path $stagingRoot $manifest.id
  $scriptsDir = Join-Path $stage "r6\scripts\$($manifest.id)"
  New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null

  $sources = Get-ChildItem -LiteralPath (Join-Path $modDir.FullName 'src\reds') -Filter '*.reds' -File
  if ($sources.Count -eq 0) {
    throw "Erro: $($manifest.id) não tem fontes .reds — Solução: veja mods/$($manifest.id)/src/reds."
  }
  foreach ($source in $sources) {
    Copy-Item -LiteralPath $source.FullName -Destination $scriptsDir -Force
  }

  $install = @"
$($manifest.name) v$($manifest.version)
$($manifest.description)

REQUISITOS
  - Cyberpunk 2077 para PC, versao $($manifest.gameVersion)
  - redscript $($manifest.requires.redscript) ou superior (https://github.com/jac3km4/redscript/releases)
  - RED4ext NAO e necessario para este mod.

INSTALACAO
  1. Instale o redscript na raiz do jogo (extraia o zip do release).
  2. Extraia este zip para a raiz do jogo ("Cyberpunk 2077"), aceitando a
     fusao de pastas. Os ficheiros ficam em r6\scripts\$($manifest.id)\.
  3. Inicie o jogo normalmente (nao e preciso -modded).

CONFIGURACAO
  Edite r6\scripts\$($manifest.id)\Config.reds e reinicie o jogo.

DESINSTALACAO
  Apague a pasta r6\scripts\$($manifest.id)\.

LICENCA
  $($manifest.license) - ver LICENSE.
"@
  Set-Content -LiteralPath (Join-Path $stage 'INSTALL.txt') -Value $install -Encoding UTF8
  Copy-Item -LiteralPath (Join-Path $repoRoot 'LICENSE') -Destination (Join-Path $stage 'LICENSE') -Force

  $zipPath = Join-Path $OutputDir "$name.zip"
  if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
  Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zipPath -CompressionLevel Optimal

  $hash = Get-FileSha256 -Path $zipPath
  $artifacts.Add([pscustomobject]@{
    Mod     = $manifest.id
    Version = $manifest.version
    Zip     = $zipPath
    Sha256  = $hash
    Bytes   = (Get-Item -LiteralPath $zipPath).Length
  }) | Out-Null
}

Remove-Item -LiteralPath $stagingRoot -Recurse -Force

Write-Host ''
foreach ($artifact in $artifacts) {
  Write-Host ("{0} v{1}" -f $artifact.Mod, $artifact.Version)
  Write-Host ("  {0} ({1:N0} bytes)" -f $artifact.Zip, $artifact.Bytes)
  Write-Host ("  sha256 {0}" -f $artifact.Sha256)
}

$checksumFile = Join-Path $OutputDir 'SHA256SUMS.txt'
$lines = $artifacts | ForEach-Object { "$($_.Sha256)  $(Split-Path -Leaf $_.Zip)" }
Set-Content -LiteralPath $checksumFile -Value ($lines -join "`n") -Encoding ASCII
Write-Host ''
Write-Host "Checksums: $checksumFile"

if ($artifacts.Count -eq 0) {
  throw 'Erro: nenhum mod empacotado — Solução: verifique mods/*/mod.json.'
}
