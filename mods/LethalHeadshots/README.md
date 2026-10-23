# Lethal Headshots

**Every headshot kills.** One clean hit to the head drops the target — no damage
multipliers, no armour math, no boss damage cap.

- Version: **1.0.1**
- Game: **Cyberpunk 2077 2.5** (PC)
- Requires: [redscript](https://github.com/jac3km4/redscript/releases) **0.5.32+**
  (RED4ext is **not** required for this mod)
- License: MIT

## Install

1. Install **redscript** into the Cyberpunk 2077 folder (extract its release zip
   into the game root).
2. Download `LethalHeadshots-1.0.1.zip` from the
   [releases page](https://github.com/frederico-kluser/cyberpunk-2077-mods/releases).
3. Extract it into the Cyberpunk 2077 folder (merge folders). You should end up
   with:

   ```text
   Cyberpunk 2077\r6\scripts\LethalHeadshots\LethalHeadshots.reds
   Cyberpunk 2077\r6\scripts\LethalHeadshots\Config.reds
   ```

4. Start the game. Redscript compiles the files at launch.

From a clone of this repository you can also run:

```powershell
pwsh -File tools/deploy.ps1
```

### Uninstall

Delete `Cyberpunk 2077\r6\scripts\LethalHeadshots\`.

## Configuration

Edit `r6\scripts\LethalHeadshots\Config.reds`, change `true` to `false`, save and
restart the game (the scripts are compiled on startup).

| Option | Default | Effect |
| --- | --- | --- |
| `SpareCivilians` | `true` | Civilians survive a headshot. Set to `false` to kill anyone. |
| `SpareAllies` | `true` | Characters with a friendly attitude towards V survive. |
| `SpareProtectedTargets` | `true` | God-mode / scripted-invulnerable / quest-protected NPCs survive. **Keep this on** unless you want to risk breaking quests. |

```redscript
module LethalHeadshots.Config

public func SpareCivilians() -> Bool {
  return true;
}
```

## What counts as a headshot

A hit is lethal when **all** of these are true:

- the player is the instigator;
- it is a direct hit, not an area-of-effect explosion;
- it is a real hit, not the aim-assist "projection" pass (so merely aiming at a
  head never kills);
- the hit shape is the head (`EHitReactionZone.Head`);
- the target is a living, non-player puppet that is not spared by the config.

Consequences:

- **Firearms, melee, mantis blades, throwing weapons:** yes, if the hit lands on
  the head hit shape.
- **Grenades, explosions, vehicle collisions:** no — they are area-of-effect and
  do not target a body part.
- **Quickhacks and damage over time:** no — they do not go through the localized
  damage path.
- **Drones, mechs, turrets, vehicles:** only if the game exposes a head hit shape
  for them; otherwise they take normal damage. Weakspots are a separate system.

## How it works (short version)

The mod wraps `DamageSystem.ProcessLocalizedDamage` — the same function where
the vanilla game decides that a hit was a headshot. When the hit qualifies, it
adds `hitFlag.Kill` to the attack. The engine's own `ProcessInstantKill` runs
immediately afterwards and drops the target's Health stat pool to its minimum,
which is the game's native instant-kill path (used by finishers and scripted
kills).

This is deliberately **not** a damage multiplier:

- a multiplier is clamped by boss/MaxTac per-hit damage caps and reduced by
  armour, resistances and mitigation;
- writing a huge damage value into the hit would still pass through those
  systems, and would show absurd damage numbers;
- `hitFlag.Kill` is the engine's "this target dies now" signal.

The full pipeline walk-through, including the exact call order and the safety
guards, is in [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md).

## Known limitations

- **No damage floater / no damage XP for the killing hit.** The instant-kill path
  sets Health directly instead of dealing damage, so the game does not show a
  number or award damage-based XP for that hit. Kill credit, loot and quest
  events still fire because the instigator is preserved.
- **Other mods that `@replaceMethod` the same function** (instead of wrapping it)
  can bypass this mod. Load order between Redscript mods is by module name; if
  another damage mod misbehaves, test with only this mod enabled.
- **Protected targets stay alive** while `SpareProtectedTargets` is on. That is
  intentional: one-shotting a quest-critical NPC can corrupt a playthrough.
- **Patch 2.5 only.** Older redscript versions cannot compile the 2.5 script
  bundle, and older game versions may not expose the same damage pipeline.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Nothing happens | `r6\logs\redscript_rCURRENT.log` must end with a successful compile and list `LethalHeadshots`. |
| Compile error in the log | You are probably on redscript < 0.5.32 or on a different game patch. |
| Works on enemies, not on a specific boss | The boss is probably protected (god mode / quest flag). That is `SpareProtectedTargets`. |
| Civilians die | `SpareCivilians` was set to `false`. |

## Development

```powershell
pwsh -File tools/validate.ps1 -DownloadTools   # type-check against your 2.5 bundle
pwsh -File tools/deploy.ps1 -Launch            # deploy and start the game
```

See [docs/TESTING.md](../../docs/TESTING.md) for the full validation and manual
test matrix.

