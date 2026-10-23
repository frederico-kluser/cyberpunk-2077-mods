# Testing

The mod is a single hook, so testing has three layers: static validation, a
compile/load smoke test, and a short manual matrix in game.

## 1. Static validation (no game required)

```powershell
pwsh -File tools/validate.ps1 -Static
```

Checks every `mod.json`, that all declared files exist, that each `.reds` file
declares a module, and runs `redscript-cli lint` on the sources. Without a game
bundle this validates syntax only.

## 2. Type-check against the real 2.5 API

```powershell
pwsh -File tools/validate.ps1 -DownloadTools
```

`validate.ps1` downloads `redscript-cli.exe` into `.cache/redscript/`, locates
the game (registry → Steam libraries → `CYBERPUNK_GAME_DIR` → `-GameDir`) and
lints the sources **against `r6/cache/final.redscripts`**. This is the important
check: it proves that every class, method and enum used by the mod exists in the
installed game version with the expected signature.

A successful run ends with:

```text
INFO [redscript_cli] Lint successful
```

Note: `redscript-cli` exits with status 0 even when it prints diagnostics, so the
script treats any line starting with `ERROR` as a failure.

## 3. Compile/load smoke test

1. Install redscript 0.5.32+ into the game folder (RED4ext is not needed).
2. `pwsh -File tools/deploy.ps1`
3. Start the game and quit after reaching the main menu (or load a save).
4. Open `r6\logs\redscript_rCURRENT.log` and confirm:
   - the compile finished with `Output successfully saved to ...`;
   - there is no `ERROR` line mentioning `LethalHeadshots`.

If the log does not exist, redscript is not installed correctly. If it mentions
a compile error, the game version and the redscript version do not match.

## 4. Manual in-game matrix

Run these with a fresh save or a save where you can reload freely.

| # | Scenario | Expected |
| --- | --- | --- |
| 1 | Shoot a hostile ganger in the head with a pistol | Dies on the first hit |
| 2 | Shoot the same enemy in the chest | Normal damage, no instant kill |
| 3 | Aim at an enemy's head without shooting (aim assist / projection) | Nothing happens |
| 4 | Shoot a civilian in the head | Survives (with `SpareCivilians = true`) |
| 5 | Shoot an ally / companion in the head | Survives (with `SpareAllies = true`) |
| 6 | Headshot a boss (e.g. a cyberpsycho) | Dies, unless the boss is in a protected phase |
| 7 | Headshot a drone / mech / turret | Normal behaviour, no crash |
| 8 | Throw a grenade at an enemy's head level | Explosion behaves normally |
| 9 | Get shot in the head by an enemy | V takes normal damage, never an instant kill |
| 10 | Kill an enemy with a headshot, then loot it | Kill credit and loot work |
| 11 | Reload the save | The mod is still active |
| 12 | Install alongside another damage mod | No compile error; document any behavioural conflict |

Record the game version (`Cyberpunk 2077\bin\x64\Cyberpunk2077.exe` → Properties →
Details) and the redscript version in the pull request.

## 5. Regression checklist for a patch bump

When CDPR ships a new patch:

1. Update redscript to a release that supports the new script bundle.
2. Run `tools/validate.ps1 -DownloadTools`; fix any API break.
3. Run the manual matrix above.
4. Bump `mod.json` `gameVersion` and note the supported patch in the README.
