# CP2077 CET gate — Cyber Engine Tweaks loads ONLY with the -modded flag.
#
# Steam launch options (Propriedades -> Geral -> Opcoes de inicializacao):
#
#   "C:\Users\kluse\Tools\cp2077-cet-gate.bat" %command% -modded
#
#   - with -modded    -> CET ENABLED  (LogSentry + CET console)
#   - without -modded -> CET DISABLED (vanilla: the ASI is renamed .off)
#
# The wrapper forwards every argument to the game, so -modded also reaches the
# game itself (forces the REDmod "modded" pipeline - keep the empty folder
# r6\cache\modded in place).

$game = $args[0]
$gameArgs = @()
if ($args.Count -gt 1) {
  $gameArgs = $args[1..($args.Count - 1)]
}

$wantCet = $gameArgs -contains '-modded'

$plugins = Join-Path (Split-Path -Parent $game) 'plugins'
$asiOn  = Join-Path $plugins 'cyber_engine_tweaks.asi'
$asiOff = Join-Path $plugins 'cyber_engine_tweaks.asi.off'

if ($wantCet) {
  if (Test-Path -LiteralPath $asiOff) {
    Move-Item -LiteralPath $asiOff -Destination $asiOn -Force
  }
  Write-Host '[cet-gate] CET ATIVO (flag -modded) — LogSentry + console CET'
} else {
  if (Test-Path -LiteralPath $asiOn) {
    Move-Item -LiteralPath $asiOn -Destination $asiOff -Force
  }
  Write-Host '[cet-gate] CET DESATIVADO (sem -modded) — jogo vanilla'
}

Start-Process -FilePath $game -ArgumentList $gameArgs -WorkingDirectory (Split-Path -Parent $game)
