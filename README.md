# Cyberpunk 2077 Mods

<p align="center">
  <a href="https://github.com/frederico-kluser/cyberpunk-2077-mods/actions/workflows/ci.yml"><img src="https://github.com/frederico-kluser/cyberpunk-2077-mods/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://securityscorecards.dev/viewer/?uri=github.com/frederico-kluser/cyberpunk-2077-mods"><img src="https://api.securityscorecards.dev/projects/github.com/frederico-kluser/cyberpunk-2077-mods/badge" alt="OpenSSF Scorecard"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://github.com/frederico-kluser/cyberpunk-2077-mods/releases"><img src="https://img.shields.io/github/v/release/frederico-kluser/cyberpunk-2077-mods" alt="GitHub release"></a>
</p>

Open-source mods for **Cyberpunk 2077** on PC. Every mod lives in its own folder
under [`mods/`](mods/), is written in Redscript, ships as a plain zip that you
extract into the game folder, and is covered by the same build, validation and
release pipeline.

[Português (BR)](README.pt-BR.md)

## Mods

| Mod | Version | What it does |
| --- | --- | --- |
| [**Lethal Headshots**](mods/LethalHeadshots) | 1.1.0 | Every headshot kills instantly — any NPC, no exceptions. No damage multipliers, no boss damage caps: the hit calls the game's force kill directly. Also shows a red "QUE OTA" label while the crosshair is over a killable head. |
| [**Desert Eagle**](mods/DesertEagle) | 0.1.0 | Custom Desert Eagle .50 AE handgun over the Tsunami Nue skeleton and animations, produced by an automated Blender pipeline (alignment, rigging, LODs, export). |

## Requirements

- Cyberpunk 2077 for PC, **patch 2.5** (game version `3.0.88.x`).
- [redscript](https://github.com/jac3km4/redscript/releases) **0.5.32 or newer**
  (0.5.32 is the first release that supports the 2.5 script bundle).

> Redscript compiles `r6/scripts/**/*.reds` when the game starts, and the engine
> does it natively — **RED4ext is not required** for these mods. Nothing needs to
> be launched with `-modded`; that flag is only for REDmod packages.

## Install a mod

1. Install RED4ext and redscript into the Cyberpunk 2077 folder.
2. Download the mod zip from the [releases page](https://github.com/frederico-kluser/cyberpunk-2077-mods/releases).
3. Extract it into the Cyberpunk 2077 folder, merging folders. The scripts land
   in `r6\scripts\<ModId>\`.
4. Start the game.

To uninstall, delete `r6\scripts\<ModId>\`.

## The CET gate (special launch command)

Cyber Engine Tweaks — required by the **LogSentry** diagnostic mod — must load
**only** when you deliberately ask for it. A gate wrapper decides before the
game starts. Add this to **Steam → Cyberpunk 2077 → Properties → General →
Launch options**:

```
"C:\Users\kluse\Tools\cet-gate.bat" %command% -modded
```

> **This is a Steam field value, not a terminal command.** `%command%` is a
> placeholder that only Steam substitutes (with the real game command) — pasting
> it into PowerShell fails (`%` is an operator there). To launch the same way
> from a terminal, replace `%command%` with the game exe:
>
> ```powershell
> & "C:\Users\kluse\Tools\cet-gate.bat" "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe" -modded
> ```

| Launch | Result |
| --- | --- |
| **with** `-modded` | CET enabled — console + LogSentry logging |
| **without** `-modded` | CET disabled — plain vanilla game |

`%command%` makes Steam hand the real game command to the gate
([`tools/cet-gate.bat`](tools/cet-gate.bat), installed at
`C:\Users\kluse\Tools\`), which renames `cyber_engine_tweaks.asi` ↔
`cyber_engine_tweaks.asi.off` and then starts the game with every argument
forwarded. `-modded` also reaches the game itself and forces the REDmod
pipeline (keep the empty `r6\cache\modded` folder).

Without the flag the game runs exactly as if CET were not installed.

## Build from source

The build scripts only need PowerShell 7 (or Windows PowerShell 5.1) and,
optionally, a local game install to type-check the scripts against the real
2.5 script bundle.

```powershell
git clone https://github.com/frederico-kluser/cyberpunk-2077-mods.git
cd cyberpunk-2077-mods

# Static checks (no game required)
pwsh -File tools/validate.ps1 -Static

# Full type-check against your installation
pwsh -File tools/validate.ps1 -DownloadTools

# Build zips into dist/
pwsh -File tools/build.ps1

# Copy the mod into your game
pwsh -File tools/deploy.ps1
```

## Repository layout

```text
mods/
  LethalHeadshots/
    mod.json              metadata read by the build/release scripts
    src/reds/             Redscript sources (the actual mod)
  DesertEagle/
    mod.json              metadata read by the build/release scripts
    src/reds/             Redscript helper (spawn/test)
    src/blender/          automated 3D pipeline (bpy stages + tests)
    src/tweakxl/          item records (TweakXL)
    src/archivexl/        entity factory + localization (ArchiveXL)
    docs/                 pipeline + toolchain documentation
docs/
  ARCHITECTURE.md         how the damage pipeline works and why the mod hooks it
  TESTING.md              how to validate a change, in and out of the game
  RELEASING.md            versioning and release checklist
  ADDING_A_MOD.md         how to add the next mod to this monorepo
tools/
  validate.ps1            static checks + Redscript type-check
  build.ps1               packages every mod into dist/*.zip
  deploy.ps1              copies a mod into the local game
```

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) first. In short: branch from `main` as
`<type>/<slug>`, use [Conventional Commits](https://www.conventionalcommits.org/),
open a pull request and let CI run. `main` is protected; direct commits are
rejected.

## Security

Please do not report security issues in public. See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).


