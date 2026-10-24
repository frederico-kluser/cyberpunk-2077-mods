# Log Sentry

Diagnostic capture mod. It does not change gameplay: it **captures and catalogs
every kind of log, structured and timestamped**. Two halves:

## 1. Redscript (`src/reds/LogSentry.reds`)

Every traced engine callback emits a **logfmt line with three clocks** through
`FTLog` (which lands in the CET game log):

```
[LogSentry] ts=1714233600.123 sim=12345.678 game=54321 lvl=INFO cat=damage ev=real_hit found=TC
```

| Field | Meaning |
| --- | --- |
| `ts` | `TimeSystem.GetGameTimeStamp()` — absolute stamp (semantics proven by the `clock_probe` line) |
| `sim` | `EngineTime.ToFloat(GetSimTime)` — monotonic engine seconds (ordering within a session) |
| `game` | `GameTime.GetSeconds` — world clock |
| `lvl` | `DEBUG / INFO / WARN / ERROR` (mapped to `FTLog`/`FTLogWarning`/`FTLogError`) |
| `cat` | `sessao / hud / psm / damage / aim / equip` |
| `ev` | stable event name, no dynamic values (attributes carry values) |

Sparse events also go to the **file-name catalog** through the only vanilla
write-to-file channel with a caller-controlled name
(`ResourceMetricsReportGenerator.WriteReportToFile`): one `LS-<seq>-<event>.txt`
per event — the directory listing is the event order.

Events traced: HUD controller init/attach, weapon swap, vision/interaction
state, crosshair state changes, damage pipeline (projection vs real hits),
preview clears, aim-query probes (`aim_probe found=T/C/A/B/NONE`), ticker
ticks, session boundaries (`QuestTrackerGameController`, in-game menu).

## 2. CET/Lua (`src/lua/init.lua`) — wall clock + real file

Owner-authorised CET usage for this diagnostic mod. It adds what pure redscript
cannot:

- **`<game>/r6/logs/logsentry.jsonl`** — the structured catalog with **real
  wall-clock timestamps** (`wall` field, ISO-8601);
- **game-log capture**: tails `bin/x64/plugins/cyber_engine_tweaks/gamelog.log`
  and bridges every `[LogSentry]` line from the redscript side into the JSONL —
  the engine's otherwise-invisible log stream becomes a real file;
- extra CET-only events (`player_attached`, `on_hit`, overlay open/close);
- a live **LogSentry** overlay panel with counters.

## Reading the catalog

```powershell
# the structured catalog (wall-clock timestamps):
Get-Content "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\r6\logs\logsentry.jsonl"

# the raw engine stream (three clocks, logfmt):
Select-String -Path "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\gamelog.log" -Pattern "\[LogSentry\]"

# the file-name catalog:
Get-ChildItem "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077" -Recurse -Filter "LS-*.txt" | Sort-Object Name
```

## Install

```powershell
pwsh -File tools/deploy.ps1 -ModId LogSentry   # redscript + CET/Lua
```

Requires redscript ≥ 0.5.32 and Cyber Engine Tweaks ≥ 1.38.0 (game 2.5).

## Design references

Research dossier: [`docs/research/dossie-logsentry.md`](../../docs/research/dossie-logsentry.md)
— output channels (FTLog does not persist without CET), time APIs, event
taxonomy (OpenTelemetry conventions) and the ecosystem's logging patterns.
