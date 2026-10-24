<#
.SYNOPSIS
  Validates the repository and (when the game is available) type-checks the
  Redscript sources against the game's own script bundle.

.EXAMPLE
  pwsh -File tools/validate.ps1
  pwsh -File tools/validate.ps1 -Static
  pwsh -File tools/validate.ps1 -GameDir "D:\Games\Cyberpunk 2077" -DownloadTools
#>
[CmdletBinding()]
param(
  [string]$GameDir,
  [switch]$Static,
  [switch]$DownloadTools
)

. "$PSScriptRoot\common.ps1"

$repoRoot = Get-RepoRoot
$failures = New-Object System.Collections.Generic.List[string]
$checks = 0

function Assert-True {
  param([bool]$Condition, [string]$Message)
  $script:checks++
  if ($Condition) {
    Write-Host "  [OK]   $Message"
  } else {
    Write-Host "  [FAIL] $Message" -ForegroundColor Red
    $script:failures.Add($Message)
  }
}

Write-Host '== Repositorio =='
Assert-True (Test-Path (Join-Path $repoRoot 'README.md')) 'README.md presente'
Assert-True (Test-Path (Join-Path $repoRoot 'LICENSE')) 'LICENSE presente'
Assert-True (Test-Path (Join-Path $repoRoot 'CHANGELOG.md')) 'CHANGELOG.md presente'
Assert-True (Test-Path (Join-Path $repoRoot 'CONTRIBUTING.md')) 'CONTRIBUTING.md presente'

Write-Host '== Mods =='
$modsRoot = Get-ModsRoot
$mods = @(Get-ChildItem -LiteralPath $modsRoot -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'mod.json') })
Assert-True ($mods.Count -gt 0) 'pelo menos um mod com mod.json'

foreach ($mod in $mods) {
  Write-Host "-- $($mod.Name) --"
  $manifest = Read-ModManifest -ModDir $mod.FullName

  Assert-True (-not [string]::IsNullOrWhiteSpace($manifest.id)) "$($mod.Name): id definido"
  Assert-True ($manifest.id -eq $mod.Name) "$($mod.Name): id == nome da pasta"
  Assert-True ([string]$manifest.version -match '^\d+\.\d+\.\d+$') "$($mod.Name): version SemVer ('$($manifest.version)')"
  Assert-True (-not [string]::IsNullOrWhiteSpace($manifest.description)) "$($mod.Name): description definida"
  Assert-True ($null -ne $manifest.files -and @($manifest.files).Count -gt 0) "$($mod.Name): lista de ficheiros definida"

  foreach ($rel in $manifest.files) {
    $full = Join-Path $mod.FullName $rel
    Assert-True (Test-Path -LiteralPath $full) "$($mod.Name): ficheiro '$rel' existe"
  }

  $reds = @(Get-ChildItem -LiteralPath (Join-Path $mod.FullName 'src\reds') -Filter '*.reds' -File -ErrorAction SilentlyContinue)
  Assert-True ($reds.Count -gt 0) "$($mod.Name): fontes .reds presentes"

  foreach ($file in $reds) {
    $text = Get-Content -LiteralPath $file.FullName -Raw
    Assert-True ($text -match '(?m)^module\s+\S+') "$($mod.Name)/$($file.Name): declara um module"
  }
}

if ($Static) {
  Write-Host '== Redscript (modo estatico: so sintaxe, sem bundle do jogo) =='
} else {
  Write-Host '== Redscript (type-check contra o bundle do jogo) =='
}

$cli = Get-RedscriptCli -Download:$DownloadTools
if ($null -eq $cli) {
  Write-Host '  [SKIP] redscript-cli.exe nao esta em .cache/redscript (use -DownloadTools para o obter)'
  if (-not $Static) { $failures.Add('redscript-cli.exe em falta para type-check') }
} else {
  $bundle = $null
  if (-not $Static) {
    try {
      $game = Find-CyberpunkGameDir -Path $GameDir
      # Prefer the pristine cache redscript backs up before its first compile
      # (final.redscripts.bk = the vanilla game API). Linting against the
      # modded cache reports this mod's own previous compile as conflicting
      # types/fields/methods, which is a false positive.
      $bundle = Join-Path $game 'r6\cache\final.redscripts.bk'
      if (-not (Test-Path -LiteralPath $bundle)) {
        $bundle = Join-Path $game 'r6\cache\final.redscripts'
      }
      Assert-True (Test-Path -LiteralPath $bundle) "bundle do jogo encontrado ($bundle)"
    } catch {
      $failures.Add($_.Exception.Message)
      Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
    }
  }

  foreach ($mod in $mods) {
    $src = Join-Path $mod.FullName 'src\reds'
    if (-not (Test-Path -LiteralPath $src)) { continue }

    $cliArgs = @('lint', '-s', $src)
    if ($null -ne $bundle) { $cliArgs += @('-b', $bundle) }

    $output = & $cli @cliArgs 2>&1 | Out-String
    $hasError = $output -match '(?m)^ERROR'
    Assert-True (-not $hasError) "$($mod.Name): lint Redscript sem erros"
    if ($hasError) {
      Write-Host $output
    } elseif ($output.Trim().Length -gt 0 -and $output -notmatch 'Lint successful') {
      Write-Host "  $($output.Trim())"
    }
  }
}

Write-Host ''
if ($failures.Count -eq 0) {
  Write-Host "Validacao concluida: $checks verificacoes, 0 falhas." -ForegroundColor Green
  exit 0
}

Write-Host "Validacao falhou: $($failures.Count) problema(s) em $checks verificacoes." -ForegroundColor Red
foreach ($failure in $failures) { Write-Host " - $failure" -ForegroundColor Red }
exit 1
