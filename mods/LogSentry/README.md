# Log Sentry

Diagnostic capture mod. It does not change gameplay: it **traces every relevant
engine callback through every sink the vanilla game offers**, so behaviour can
be catalogued from the outside instead of guessed.

## The three sinks

| Sink | What it shows | Where |
| --- | --- | --- |
| **Files** | one file per event, the **file name is the log line** (`LH_<seq>_<event>.txt`) | search the game folder for `LH_*.txt` |
| **HUD messages** | `LH <seq> <event>` — the one visual channel proven to render | in game |
| **FTLog** | `LogSentry: <seq> <event>` | engine log channel |

The file **content** is the engine's own metrics report (the only vanilla
write-to-file API is `ResourceMetricsReportGenerator.WriteReportToFile`); the
**catalog is the directory listing** — which events fired, in what order
(`seq`), how many times.

## Events traced

| Event | Meaning |
| --- | --- |
| `CONT_INIT` / `CONT_ATTACH` | crosshair HUD controller initialized / player attached |
| `WEAPON_SWAP` | weapon changed (or holstered) |
| `VISION_<n>` / `INTERACT` | player state machine vision state / terminal interaction |
| `XHAIR_STATE` | **crosshair state change (weapon ready, aim start/stop)** |
| `PROJ_HIT` / `REAL_HIT` | damage pipeline ran (projection pass / real hit) |
| `CLEAR_PREVIEW` | the game cleared its aim-preview target |
| `TICKER_START`, `TICK_<n>` | the `DelayCallback` ticker started / tick number `n` |
| `AIM_<codes>` | **raw aim-query result**: `T`=tracked target, `C`=closest-to-crosshair, `A`/`B`=look-at (strict/permissive), `NONE`=nothing found |

## Reading the catalog

```powershell
Get-ChildItem "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077" -Recurse -Filter "LH_*.txt" |
  Sort-Object Name | Select-Object Name, LastWriteTime
```

- Files present but no `TICK_n` → the `DelayCallback` chain never fired.
- `TICK_n` present but `AIM_NONE` while aiming → the aim queries find nothing.
- `AIM_T`/`AIM_C` present but no head label → the head test / widget layer.
- No files at all → `WriteReportToFile` is not usable; rely on the HUD messages.

## Install

```powershell
pwsh -File tools/deploy.ps1 -ModId LogSentry
```
